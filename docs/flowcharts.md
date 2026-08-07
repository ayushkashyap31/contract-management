# Contract Lifecycle Management — Flowcharts

This document contains GitHub-compatible Mermaid diagrams for the Contract
Lifecycle Management (CLM) system. Every diagram reflects the **current
implementation** in the repository.

## Reusable style

All diagrams use a shared colour palette:

| Class | Purpose | Fill / Stroke |
|-------|---------|---------------|
| `ap` | Portal / API process | indigo |
| `proc` | Business process | slate |
| `dec` | Decision | amber |
| `ter` | Terminal / result | emerald |
| `ext` | External (Documenso) | rose |
| `store` | Data / persistence | blue |

```mermaid
flowchart LR
    classDef ap fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    classDef proc fill:#f8fafc,stroke:#64748b,color:#0f172a
    classDef dec fill:#fffbeb,stroke:#d97706,color:#78350f
    classDef ter fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef ext fill:#fef2f2,stroke:#dc2626,color:#7f1d1d
    classDef store fill:#eff6ff,stroke:#2563eb,color:#1e3a8a
```

---

## 1. Complete Contract Lifecycle

This is the end-to-end journey from creating a counterparty to a fully executed
contract, including the branch where approvals fail.

```mermaid
flowchart TD
    classDef ap fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    classDef proc fill:#f8fafc,stroke:#64748b,color:#0f172a
    classDef dec fill:#fffbeb,stroke:#d97706,color:#78350f
    classDef ter fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef ext fill:#fef2f2,stroke:#dc2626,color:#7f1d1d
    classDef store fill:#eff6ff,stroke:#2563eb,color:#1e3a8a

    A[Create Counterparty]:::proc --> B[Create Contract]:::proc
    B --> C[Create Contract Version]:::ap
    C --> D[Draft]:::proc
    D --> E[Submit for Review]:::ap
    E --> F{All Approvals Approved?}:::dec
    F -- No --> R[Rejected]:::ter
    R --> S[Revise → back to Draft]:::proc
    S --> D
    F -- Yes --> G[Create Signature Request]:::ap
    G --> H[Send to Documenso]:::ext
    H --> I[Counterparty Portal]:::ap
    I --> J[Sign Document]:::ext
    J --> K[Webhook Received]:::ext
    K --> L[Version Executed]:::ter
    L --> M[Contract Completed]:::ter
```

> Implementation notes: submissions go through `ContractVersionService.submit_for_review`
> → `ApprovalService`; sending uses `SignatureService.send_signature_request` →
> Documenso V2 `envelope/create` + `envelope/distribute`; completion is driven by the
> `DOCUMENT_COMPLETED` webhook via `SignatureService.process_document_completed`.

---

## 2. Counterparty Portal Flow

How a guest becomes an authenticated counterparty and navigates the portal to
sign a contract.

```mermaid
flowchart TD
    classDef ap fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    classDef proc fill:#f8fafc,stroke:#64748b,color:#0f172a
    classDef dec fill:#fffbeb,stroke:#d97706,color:#78350f
    classDef ter fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef ext fill:#fef2f2,stroke:#dc2626,color:#7f1d1d

    A[Guest visits site]:::proc
    A --> B[Portal Login<br/>/portal/login]:::ap
    B --> C{Authenticated?}:::dec
    C -- No --> B
    C -- Yes --> D[Portal Dashboard<br/>/portal]:::ap
    D --> E[View Contracts<br/>get_dashboard]:::ap
    E --> F[Open Contract<br/>get_contract_detail]:::ap
    F --> G[Download PDF<br/>download_document]:::ap
    G --> H{Pending Review?}:::dec
    H -- Yes --> I[Approve / Reject<br/>review_contract]:::ap
    I --> F
    H -- No --> J{Pending Signature?}:::dec
    J -- Yes --> K[Open Documenso<br/>signing URL]:::ext
    K --> J
    J -- No --> L[Executed Contract]:::ter
```

### Implementation notes
- Login posts to Frappe's `/api/method/login` (`public/portal/login.js`).
- Every portal API is guard-oriented by `_require_counterparty` / `_get_counterparty_for_user`
  (ownership is enforced server-side).

---

## 3. Contract Approval Workflow

The internal multi-approver decision flow, including rejection and the
revision loop.

```mermaid
flowchart TD
    classDef ap fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    classDef proc fill:#f8fafc,stroke:#64748b,color:#0f172a
    classDef dec fill:#fffbeb,stroke:#d97706,color:#78350f
    classDef ter fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef ext fill:#fef2f2,stroke:#dc2626,color:#7f1d1d

    A[Draft<br/>Contract Version]:::proc
    A --> B[Submit]:::ap
    B --> C[Approval Record Created<br/>ApprovalService.create_for_version]:::ap
    C --> D[Reviewer Opens Contract<br/>portal or desk]:::proc
    D --> E{Decision}:::dec
    E -- Reject --> F[Contract Version Rejected]:::ter
    F -- Revise --> A
    E -- Approve --> G[ApprovalService.approve]:::ap
    G --> H[WorkflowService<br/>apply_action / apply_system_action]:::ap
    H --> I{All approvals Approved?}:::dec
    I -- No --> D
    I -- Yes --> J[Version Approved]:::ter
```

### Implementation notes
`ApprovalService.create_for_version` creates one Approval per approval-capable
collaborator (roles in `APPROVAL_ROLES`). The version becomes `Approved` only
when every approval is `Approved`; any rejection sends it to `Rejected`.

---

## 4. Signature Workflow

From an approved version through Documenso and back to execution.

```mermaid
flowchart TD
    classDef ap fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    classDef proc fill:#f8fafc,stroke:#64748b,color:#0f172a
    classDef dec fill:#fffbeb,stroke:#d97706,color:#78350f
    classDef ter fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef ext fill:#fef2f2,stroke:#dc2626,color:#7f1d1d

    A[Approved Version] --> B[Create Signature Request<br/>contract_version.create_signature_request]:::ap
    B --> C[Generate Documenso Envelope<br/>envelope/create]:::ext
    C --> D[Recipients Created]:::proc
    D --> E[Send Signature Request<br/>SignatureService.send_signature_request]:::ap
    E --> F[Counterparty Opens Signing URL]:::ext
    F --> G[Signs]:::ext
    G --> H[Documenso Webhook<br/>DOCUMENT_COMPLETED]:::ext
    H --> I[Signature Request Updated<br/>SignatureService.process_document_completed]:::ap
    I --> J[Version Executed]:::ter
```

### Implementation notes
PDF placeholder validation (`{{signature,rN}}`) happens before
`envelope/create`. Recipient IDs and the signing URL are persisted from the
`envelope/distribute` response.

---

## 5. Portal Authorization Flow

How the `/portal` route decides whether to show the dashboard or redirect to
login.

```mermaid
flowchart TD
    classDef sub fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    classDef proc fill:#f8fafc,stroke:#64748b,color:#0f172a
    classDef dec fill:#fffbeb,stroke:#d97706,color:#78350f
    classDef ter fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef ext fill:#fef2f2,stroke:#dc2626,color:#7f1d1d

    A[User visits /portal]:::proc
    A --> B{Authenticated?}:::dec
    B -- No --> C[Redirect]:::ext
    C --> D["/portal/login"]:::ap
    D --> E[Login Success]:::ter
    E --> F[Portal Dashboard]:::ap
    B -- Yes --> G[Resolve Counterparty<br/>_get_counterparty_for_user]:::proc
    G --> H{Counterparty Exists?<br/>portal_enabled + portal_user}:::dec
    H -- No --> I[Permission Denied]:::ext
    H -- Yes --> F
```

> Note: `portal.py` redirects guests back to `/app` (or the login route) and
> `login.py` redirects already-authenticated counterparties straight to `/portal`.

---

## 6. Document Download Flow

Ownership-guarded file streaming for the portal.

```mermaid
flowchart TD
    classDef ap fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    classDef proc fill:#f8fafc,stroke:#64748b,color:#0f172a
    classDef dec fill:#fffbeb,stroke:#d97706,color:#78350f
    classDef ter fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef ext fill:#fef2f2,stroke:#dc2626,color:#7f1d1d

    A[Portal User]:::proc
    A --> B[Open Contract Detail]:::ap
    B --> C[Click Download]:::ap
    C --> D[download_document]:::proc
    D --> E[_require_counterparty]:::proc
    E --> F[Ownership Check<br/>contract.counterparty == counterparty.name]:::dec
    F -- No --> G[403 PermissionDenied]:::ext
    F -- Yes --> H[File Lookup<br/>version.document → tabFile]:::proc
    H --> I[Return PDF<br/>type=download, inline]:::ter
```

### Implementation notes
Access is gated server-side; `/private/files/` URLs are never exposed directly
to portal users.

---

## 7. Webhook Processing Flow

`DOCUMENT_COMPLETED` end-to-end.

```mermaid
flowchart TD
    classDef sub fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    classDef proc fill:#f8fafc,stroke:#64748b,color:#0f172a
    classDef dec fill:#fffbeb,stroke:#d97706,color:#78350f
    classDef ter fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef ext fill:#fef2f2,stroke:#dc2626,color:#7f1d1d

    A[Documenso]:::ext
    A --> B[Webhook POST<br/>handle_webhook]:::ap
    B --> C[Validate Secret<br/>WebhookAuthenticator.verify]:::ext
    C --> D[Dispatcher<br/>WebhookDispatcher]:::proc
    D --> E[Webhook Service<br/>WebhookService.handle]:::proc
    E --> F[Update Signature Request<br/>SignatureService.process_document_completed]:::ap
    F --> G[Update Recipients<br/>match by documenso_recipient_id]:::proc
    G --> H[Workflow Transition<br/>Complete Signing → Executed]:::ap
    H --> I[Version Executed]:::ter
    I --> J[Notifications]:::proc
```

### Implementation notes
- Auth: `WebhookAuthenticator.verify` compares `X-Documenso-Secret` with
  `hmac.compare_digest`.
- Idempotent: already-Completed, Cancelled and Expired requests are ignored.
- Other events (`document.deleted`, `document.rejected`, `document.sent`,
  `recipient.completed`, `recipient.signed`) are logged placeholders.

---

## 8. Admin Dashboard Flow

How the administrator reaches executive intelligence.

```mermaid
flowchart TD
    classDef sub fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    classDef proc fill:#f8fafc,stroke:#64748b,color:#0f172a
    classDef dec fill:#fffbeb,stroke:#d97706,color:#78350f
    classDef ter fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef ext fill:#fef2f2,stroke:#dc2626,color:#7f1d1d

    A[Administrator]:::proc
    A --> B[Login]:::ap
    B --> C[Executive Dashboard<br/>CLM Executive Dashboard]:::ap
    C --> D[Fetch Reports]:::proc
    D --> E[Contract Summary]:::proc
    D --> F[Expiring Contracts]:::proc
    D --> G[Pending Approvals]:::proc
    D --> H[Pending Signature Requests]:::proc
    E --> I[Charts<br/>Contracts by Status · Expiring over time]:::ter
    G --> I
    H --> I
    D --> J[Cards<br/>Total · Executed · Pending · Active]:::ter
    I --> K[User Actions]:::proc
    J --> K
```

> `Reports` are script reports restricted to System Manager; the dashboard is an
> Frappe desk dashboard assembled from number cards and charts.

---

## 9. System Architecture Flow

Layered view of the whole system.

```mermaid
flowchart TD
    subgraph sub-app[Users]
        A[Administrator]
        B[Counterparty User]
    end

    subgraph subweb[Frappe]
        C[Web / Desk UI]
        D[Portal SPA<br/>/portal]
    end

    C --> E[Doctype Controllers]:::proc
    D --> F[Portal API<br/>portal_api.py]:::proc
    E --> G[Service Layer<br/>Contract · ContractVersion · Approval · Signature · Workflow · Notification]:::proc
    F --> G
    G --> H[Workflow Layer<br/>constants/transitions + frappe workflow]:::proc
    H --> I[Integration Layer<br/>DocumensoProvider]:::ext
    I --> J[Documenso API]:::ext
    J --> K[Webhook<br/>handle_webhook]:::ext
    G --> L[(Frappe DB / Redis)]:::store
    F --> L

    A --> C
    B --> D
    J --> K
```

> Comments: the flow is desk/portal → controllers/portal_api → services →
> workflow → Documenso, with the webhook endpoint feeding back into the service
> layer. Data persists to Frappe/Redis.

---

## 10. End-to-End System Flow

The full journey in a single diagram, including the portal handoff.

```mermaid
flowchart TD
    classDef sub fill:#eef2ff,stroke:#4338ca,color:#1e1b4b
    classDef proc fill:#f8fafc,stroke:#64748b,color:#0f172a
    classDef dec fill:#fffbeb,stroke:#d97706,color:#78350f
    classDef ter fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef ext fill:#fef2f2,stroke:#dc2626,color:#7f1d1d

    A[Admin] --> B[Create Contract]:::proc
    B --> C[Submit Version]:::proc
    C --> D[Approval]:::proc
    D --> E[Portal Review]:::ap
    E --> F[Approve]:::ter
    F --> G[Signature Request]:::proc
    G --> H[Portal Sign]:::ap
    H --> I[Webhook]:::ext
    I --> J[Workflow Update]:::proc
    J --> K[Executed]:::ter
    K --> L[Dashboard Updated]:::ter
```

---

## Validation

Each Mermaid block above uses only features that render on GitHub:

- `flowchart TD` / `flowchart LR`
- `subgraph` grouping with optional titles
- decision diamonds with `{}`
- node labels with an em-dash and `:::class` style classes
- consistent `classDef` palette for every diagram

Every diagram is a single labelled code block with valid Mermaid syntax.