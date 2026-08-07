# DocType Design

## Overview

This document defines every DocType used in the Contract Lifecycle Management
System, as implemented in the `contract_management` and `docusign_integration`
apps.

Each DocType follows Frappe best practices: expression naming series, indexed
link/search fields, and validation at the controller level.

---

# 1. Contract

## Purpose

The primary business object. Stores the metadata of a legal agreement and its
lifecycle status. The actual contract file lives on the Contract Version.

## Module

Contract Management

## Naming Series

`CTR-.YYYY.-.#####` → e.g. `CTR-2026-00001`

## Properties

- Submittable (`is_submittable = 1`)

## Fields

| Section | Field | Type | Mandatory | Notes |
|---------|-------|------|-----------|-------|
| Basic Information | contract_title | Data | Yes | indexed, searchable |
| Basic Information | counterparty | Link (Counterparty) | Yes | indexed |
| Basic Information | status | Select | Yes | `Draft / Under Review / Approved / Executed / Expired / Cancelled`, default `Draft` |
| Dates | effective_date | Date | No | validated ≤ expiration_date |
| Dates | expiration_date | Date | No | |
| Collaborator Details | collaborators | Table (Collaborator) | No | unique users enforced |
| | amended_from | Link (Contract) | No | read-only |

## Controller Validation (`contract.py`)

- `normalize_fields` — trims title
- `validate_required_fields` — non-empty title after trim
- `validate_dates` — effective_date ≤ expiration_date
- `validate_unique_collaborators` — no duplicate user rows

## Whitelisted Method

`create_version` → returns initial values for a new Contract Version
(contract, version_number, status `Draft`, is_current). Only allowed when the
contract is submitted (`docstatus = 1`).

---

# 2. Counterparty

## Purpose

Stores external companies or individuals and controls their portal access.

## Naming Series

`CP-.#####` → e.g. `CP-00001`

## Fields

| Section | Field | Type | Mandatory |
|---------|-------|------|-----------|
| Basic | counterparty_type | Select (Company / Individual) | Yes |
| Basic | counterparty_name | Data | Yes (title field) |
| Contact | contact_person | Data | Yes |
| Contact | email | Data (Email) | Yes |
| Contact | phone | Phone | No |
| Address | address | Data | No |
| Portal Access | portal_user | Link (User) | No |
| Portal Access | portal_enabled | Check | No (default off) |
| Status | status | Select (Active / Inactive) | Yes |
| Notes | notes | Text Editor | No |

---

# 3. Contract Version

## Purpose

Stores every version of a contract including the uploaded PDF. Executed
versions are immutable.

## Naming Series

`CTV-.YYYY.-.#####` → e.g. `CTV-2026-00001`

## Fields

| Section | Field | Type | Mandatory |
|---------|-------|------|-----------|
| Contract Details | contract | Link (Contract) | Yes |
| Version Details | version_number | Int | Yes |
| Version Details | document | Attach | Yes |
| Version Details | is_current | Check | No |
| Version Details | status | Select | Yes (workflow state field) |
| Note | notes | Small Text | No |

`status` options: `Draft / Under Review / Approved / Signature Requested /
Rejected / Executed / Superseded`

## Controller Logic (`contract_version.py`)

- `set_as_current_version` runs in `before_save` when `is_current` is set; uses
  `SELECT ... FOR UPDATE` to unset other current versions without a race.
- `validate_unique_version_number` — version numbers unique per contract.
- `validate_status_consistency` — a current version cannot be `Superseded`.
- `validate_current_version_exists` — prevents unsetting the only current version.

## Whitelisted Methods

- `submit_for_review` → submits and generates Approval records for
  approval-capable collaborators.
- `create_signature_request` → creates a draft Signature Request for the
  version and returns its name.

---

# 4. Approval

## Purpose

Tracks each approver's decision for a contract version. A standalone DocType
linked to Contract and Contract Version.

## Naming Series

`APR-.YYYY.-.#####` → e.g. `APR-2026-00001`

## Fields

| Field | Type | Mandatory |
|-------|------|-----------|
| contract | Link (Contract) | Yes |
| contract_version | Link (Contract Version) | Yes |
| approver | Link (User) | Yes |
| status | Select (Pending / Approved / Rejected) | Yes |
| approval_date | Datetime | No |
| remarks | Small Text | No |

## Controller Logic (`approval.py`)

- `set_approval_date` — cleared on Pending, auto-set on decision.
- `validate_duplicate_pending_approval` — one pending approval per approver per version.
- `validate_status_change` — direct status edits via the form are blocked;
  decisions must go through Approve / Reject actions.

## Whitelisted Methods

- `approve` → delegates to `ApprovalService.approve`
- `reject` → delegates to `ApprovalService.reject`

---

# 5. Signature Request

## Purpose

Tracks a Documenso signing request for a contract version, its envelope,
signing URL, recipients and status.

## Naming Series

`SIG-.YYYY.-.#####` → e.g. `SIG-2026-00001`

## Fields

| Section | Field | Type | Mandatory |
|---------|-------|------|-----------|
| Contract and Request Details | contract_version | Link (Contract Version) | Yes |
| Contract and Request Details | status | Select | Yes |
| Contract and Request Details | requested_by | Link (User) | Yes |
| Contract and Request Details | requested_on | Datetime | Yes |
| Completion Details | completed_on | Datetime | No |
| Completion Details | envelope_id | Data | No |
| Completion Details | signing_url | Data | No |
| Recipients | signature_recipients | Table (Signature Recipient) | No |

`status` options: `Draft / Pending / Sent / Viewed / Completed / Declined /
Cancelled / Expired`

## Controller Logic (`signature_request.py`)

- `set_requested_on` / `set_completed_on` — automatic timestamps.
- `validate_duplicate_active_request` — only one active request per version
  (Draft/Pending/Sent/Viewed).
- `validate_unique_signer_emails` — no duplicate recipient emails.
- `validate_unique_signing_order` / `validate_signing_order_sequence` —
  orders must be unique, sequential from 1.
- `update_recipient_signed_on` — syncs child `signed_on` timestamps.

## Whitelisted Method

`send_for_signature` → sends the draft request through the Documenso flow.

---

# 6. Child Tables

## Collaborator (Contract)

| Field | Type | Options |
|-------|------|---------|
| user | Link (User) | |
| role | Select | Reviewer / Approver / Legal / Finance / Business Owner |
| review_status | Select | Pending / In Review / Approved / Rejected |

## Signature Recipient (Signature Request)

| Field | Type | Options |
|-------|------|---------|
| signer | Link (User) | |
| email | Data (Email) | |
| signing_order | Int | sequential from 1 |
| status | Select | Pending / Sent / Viewed / Signed / Declined |
| signed_on | Datetime | |
| documenso_recipient_id | Data | read-only |

---

# 7. Documenso Settings (docusign_integration app)

## Purpose

Single-document configuration for the Documenso integration.

## Fields

| Section | Field | Type | Default |
|---------|-------|------|---------|
| General | enabled | Check | 1 |
| Connection | base_url | Data | reqd |
| Connection | api_token | Password | reqd |
| Webhook | webhook_secret | Password | |
| Networking | request_timeout | Int | 30 |
| Networking | retry_count | Int | 3 |
| Networking | retry_backoff | Float | 1.0 |

Permission: System Manager only.

---

# Relationships

```text
Counterparty (1) ──< Contract (N)
Contract (1) ──< Contract Version (N)
Contract Version (1) ──< Signature Request (N)
Signature Request (1) ──< Signature Recipient (N)
Contract (1) ──< Collaborator (N)   [child]
Contract (N) ──< Approval (N)       [Approval links to Contract and Version]
```

---

# Notes

- Executed contract versions cannot be edited.
- Amendments always create a new Contract Version.
- Only one Contract Version can be current per contract.
- Counterparties access contracts only through the Portal.
- Approval and Signature Request records are write-protected; state changes
  happen exclusively through service methods.