# Workflow Rules

## Contract Status Flow

Draft
↓

Under Review
↓

Changes Requested
↓

Approved
↓

Sent for Signature
↓

Partially Signed
↓

Executed
↓

Active
↓

Expired

Alternative Path:

Draft
↓

Cancelled

---

# Business Rules

## Draft

- Editable
- Can add collaborators
- Can update details

---

## Under Review

- Collaborators can review
- Changes can be requested
- Cannot send for signature

---

## Approved

- Ready for electronic signature
- Cannot edit contract content

---

## Sent for Signature

- Waiting for signatures
- Status synchronized with Documenso

---

## Executed

- Contract becomes read-only
- No direct edits allowed

---

## Amendment

- Creates a new Contract Version
- Previous executed version remains unchanged

---

# Validation Rules

- Expiry Date must be after Effective Date.
- Every Contract must have one Counterparty.
- Only one Current Version is allowed.
- Signature Request requires an Approved contract.
- Executed contracts cannot be deleted.

---

# Permission Rules

Contract Manager

- Create
- Edit Draft
- Send for Approval
- Send for Signature

Collaborator

- Review
- Comment

Approver

- Approve
- Reject

Counterparty

- View
- Sign

Administrator

- Full Access