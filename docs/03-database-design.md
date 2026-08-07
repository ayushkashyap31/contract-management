# Database Design

## Introduction

The database is designed with a normalized relational model to ensure
scalability, maintainability and referential integrity.

Instead of storing everything inside a single Contract document, the system
separates business concerns into independent DocTypes while leveraging Frappe's
built-in features (workflow state fields, file attachments, submit-only
documents).

---

# Design Principles

- Single Responsibility Principle per entity
- No duplication of data across entities
- Proper `Link` relationships between independent entities
- `Table` (child) DocTypes only for dependent rows
- Reuse of Frappe features (naming series, attachments, workflow status field)
- Executed versions are immutable
- Every business event is traceable (timestamps, audit trail)

---

# Main Entities

## 1. Contract (`CTR-.YYYY.-.#####`)

The central entity. Represents a legal agreement between the organization and a
counterparty.

Responsibilities:

- Store contract metadata (title, counterparty, dates, status)
- Maintain lifecycle status (`Draft`, `Under Review`, `Approved`, `Executed`, `Expired`, `Cancelled`)
- Manage collaborators (child table)
- Anchor multiple Contract Versions, Approvals and Signature Requests

`Contract` is **submittable** (`docstatus`). The current contract-level status
select is a first-class field used across reports, dashboard and portal.

## 2. Counterparty — `CP-.#####`

Represents the external organization or individual the contract is signed with.

Responsibilities:

- Company/individual details (type, name, contact person, email, phone, address)
- Portal access control (`portal_enabled`, `portal_user`)
- Active/Inactive status and notes
- Links to many Contracts

## 3. Contract Version — `CTV-.YYYY.-.#####`

Stores every version of a contract, including the uploaded PDF document.

| Field | Notes |
|-------|-------|
| contract | Link → Contract |
| version_number | Int, unique per contract |
| is_current | Check; exactly one per contract |
| document | Attach (the actual contract PDF) |
| status | Workflow state field |
| notes | Small Text |

Responsibilities:

- Version history with an immutable executed record
- The attached document drives Documenso PDF processing
- **Current Version** flag enforced via a row-level `FOR UPDATE` lock

## 4. Approval — `APR-.YYYY.-.#####`

A standalone DocType (not a child table) tracking each approver's decision for
a contract version.

| Field | Notes |
|-------|-------|
| contract | Link → Contract |
| contract_version | Link → Contract Version |
| approver | Link → User |
| status | Pending / Approved / Rejected |
| approval_date | Datetime |
| remarks | Small Text |

One Approval is created per approval-capable collaborator when a version is
submitted for review.

## 5. Signature Request — `SIG-.YYYY.-.#####`

Represents a Documenso signing request for a contract version.

| Field | Notes |
|-------|-------|
| contract_version | Link → Contract Version |
| status | Draft/Pending/Sent/Viewed/Completed/Declined/Cancelled/Expired |
| requested_by | Link → User |
| requested_on / completed_on | Datetime |
| envelope_id | Documenso envelope ID |
| signing_url | Documenso signing URL |
| signature_recipients | Child table |

## 6. Documenso Settings (single document, in `docusign_integration`)

Centralized integration configuration: `enabled`, `base_url`, `api_token`,
`request_timeout`, `retry_count`, `retry_backoff`, `webhook_secret`.

---

# Child Tables

## Collaborator (child of Contract)

| Field | Type | Notes |
|-------|------|-------|
| user | Link(User) | must be unique per contract |
| role | Select | Reviewer / Approver / Legal / Finance / Business Owner |
| review_status | Select | Pending / In Review / Approved / Rejected |

## Signature Recipient (child of Signature Request)

| Field | Type | Notes |
|-------|------|-------|
| signer | Link(User) | |
| email | Data | unique per request |
| signing_order | Int | sequential from 1, no gaps |
| status | Select | Pending / Sent / Viewed / Signed / Declined |
| signed_on | Datetime | set when signed |
| documenso_recipient_id | Data | read-only, populated from Documenso |

---

# Entity Relationships

```text
Counterparty (1) ──< Contract (N)
Contract (1) ──< Contract Version (N)
Contract (1) ──< Approvals (N)
Contract (1) ──< Collaborators (N)            [child, inline on Contract]
Contract Version (1) ──< Signature Request (N)
Signature Request (1) ──< Signature Recipients (N)   [child]
Approval ──> Contract Version (many approvals target the same version)
```

---

# Lifecycle Rules

- Draft contracts are editable; executed contracts are not amended in place.
- Executed contract versions become read-only and are never modified.
- Amendments create a new Contract Version (`Create Version`) leaving the
  executed version untouched.
- Signature requests can only be created for **approved** and **current**
  contract versions.
- Only one Contract Version may be marked current for a given contract.
- Approval records cannot be edited directly; decisions go through
  `ApprovalService` (approve/reject actions).

---

# Naming Series

| DocType | Series | Example |
|---------|--------|---------|
| Contract | `CTR-.YYYY.-.#####` | `CTR-2026-00001` |
| Counterparty | `CP-.#####` | `CP-00001` |
| Contract Version | `CTV-.YYYY.-.#####` | `CTV-2026-00001` |
| Approval | `APR-.YYYY.-.#####` | `APR-2026-00001` |
| Signature Request | `SIG-.YYYY.-.#####` | `SIG-2026-00001` |

---

# Data Integrity Rules

- Every Contract must belong to exactly one Counterparty.
- A Contract has exactly one current Contract Version.
- Only one version can be flagged `is_current=1` (enforced with row lock).
- Version numbers are unique within a contract.
- Executed/Superseded versions are terminal.
- Signature requests can be duplicated only for an already-completed flow; one
  active request per contract version at a time.
- Pointer integrity: `Approval.contract == Contract(key)` and a version-level
  uniqueness for pending approvals per approver.

---

# Future Enhancements

- AI Contract Review
- OCR Support
- Clause Library
- Contract Templates
- Risk Analysis
- Renewal Automation
- Bulk Import