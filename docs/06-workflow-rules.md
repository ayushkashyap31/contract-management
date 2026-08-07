# Workflow Rules

## Contract Version State Machine

The system uses Frappe's built-in workflow engine configured on the
**Contract Version** DocType (`fixtures/workflow.json`, fixture name
"Contract Version Workflow").

```text
        ┌──────────────────────────────────────────────┐
        │                                              │
        ▼                                              │
     Draft ──Submit for Review──► Under Review ─Reject─▶ Rejected
        ▲                              │                    │
        │                              │ Approve            │ Revise
        │                              ▼                    │
        │                          Approved ◄───────────────┘
        │                              │
        │                  ┌───────────┴───────────┐
        │                  │                       │
        │    Request Signature                  Supersede
        │                  │                       │
        │                  ▼                       ▼
        │          Signature Requested        Superseded (terminal)
        │                  │   │
        │       Complete    │   │  Cancel Signature
        │       Signing     │   │
        │                  ▼   ▼
        │               Executed (terminal)
        └──────────────────┘
```

### Canonical transitions (`constants/transitions.py`)

| From | To | Workflow Action | Allowed Role |
|------|----|-----------------|--------------|
| Draft | Under Review | Submit for Review | Contract Manager |
| Under Review | Approved | Approve | Approver |
| Under Review | Rejected | Reject | Approver |
| Rejected | Draft | Revise | Contract Manager |
| Approved | Signature Requested | Request Signature | Contract Manager |
| Approved | Superseded | Supersede | Contract Manager |
| Signature Requested | Executed | Complete Signing | System Manager |
| Signature Requested | Approved | Cancel Signature | System Manager |

`Executed` and `Superseded` are terminal states (no outgoing transitions).

> The same transition map (`VERSION_TRANSITIONS`) is mirrored in code and used
> with `WorkflowService.can_transition` before applying actions, giving a
> single source of truth independent of the fixture.

---

## Version States

- **Draft** — editable by Contract Manager; can be submitted for review.
- **Under Review** — awaiting collaborator approvals.
- **Approved** — internal approval complete; eligible for signature.
- **Rejected** — at least one approver rejected; can be revised back to Draft.
- **Signature Requested** — approved and sent to Documenso.
- **Executed** — fully signed; terminal and immutable.
- **Superseded** — replaced by a newer version; terminal.

---

## Approval Flow

1. `ContractVersion.submit_for_review` transitions the version to `Under Review`
   via the workflow, then `ApprovalService.create_for_version` creates one
   **Approval** record per approval-capable collaborator
   (`role` in {Approver, Legal, Finance, Business Owner}).
2. An approver approves/rejects through the desk button or the portal:
   - `approve` → mark Approval **Approved**, set `approval_date`, sync the
     collaborator's `review_status`.
   - `reject` → mark Approval **Rejected**, set date; the whole version becomes
     **Rejected**.
3. Only when **all** approvals for a version are `Approved` does the version
   transition to **Approved**.
4. Approvals cannot be re-triggered manually; status changes are blocked outside
   service actions (`validate_status_change`).

---

## Signature Workflow

1. A Signature Request is created (Draft) for an **approved**, **current**
   version.
2. `send_for_signature`:
   - validates version is `Approved` / `is_current`
   - reads the attached PDF and validates Documenso `{{signature,rN}}`
     placeholders
   - builds the payload, creates the envelope (`envelope/create`),
   - persists the envelope, distributes it (`envelope/distribute`),
   - records recipient IDs + signing URL,
   - transitions the version to `Signature Requested` (`Request Signature`),
   - marks the request `Pending`, and notifies recipients.
3. Completion is driven by the Documenso `DOCUMENT_COMPLETED` webhook (or a
   manual completion path), which:
   - matches signed recipients by `documenso_recipient_id`,
   - transitions the version to `Executed` (`Complete Signing`),
   - marks the request `Completed`.
4. Cancelling a pending request restores the version to `Approved`
   (`Cancel Signature`).

---

## Validation Rules

- Expiration Date must be on or after Effective Date (Contract).
- Every Contract must have a Counterparty.
- Exactly one **current** Contract Version per contract.
- Version numbers are unique per contract.
- Duplicate collaborator users, duplicate signer emails, duplicate and
  non-sequential signing orders are rejected.
- A Signature Request requires the Contract Version to be **Approved** and **current**.
- Only one active Signature Request per version.

---

## Permission Rules

### DocType-level permissions

All CLM DocTypes (`Contract`, `Contract Version`, `Approval`, `Signature
Request`, `Signature fields`, `Counterparty`) and `Documenso Settings` grant
full desk access to the **System Manager** role only.

### Workflow role gates

- **Contract Manager** — Draft edits, `Submit for Review`, `Revise`,
  `Request Signature`, `Supersede`.
- **Approver** — `Approve`, `Reject`.
- **System Manager** — `Complete Signing`, `Cancel Signature`.

### Portal access

- **Counterparty** role routes the user's home page to `/portal`.
- Portal access is additionally gated by `Counterparty.portal_enabled` and
  `Counterparty.portal_user`; ownership checks are enforced server-side on
  every portal API.

### Notes

- Whitelisted portal endpoints call `WorkflowService.apply_system_action`
  (or elevate to Administrator within a transaction) because the counterparty
  holds no desk permissions; this is documented in `portal_api.py`.
- Webhook processing runs as Guest and likewise uses `apply_system_action`.