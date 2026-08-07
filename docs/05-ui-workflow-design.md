# UI & Workflow Design

## Overview

The CLM system provides two user-facing surfaces:

1. **Frappe desk** — for internal teams (System Manager, Contract Manager,
   Approvers) to manage contracts, versions, approvals, signature requests,
   reports and the executive dashboard.
2. **Counterparty Portal** — a Vue single-page application served at `/portal`
   with a dedicated login page at `/portal/login`.

---

# Desk UI — Contract Form

The Contract form (`Contract`) is divided into logical sections:

## Basic Information

- Contract Title
- Counterparty (Link)
- Status

## Dates

- Effective Date
- Expiration Date

## Collaborator Details

Child table with columns: User, Role, Review Status.

## Quick Actions (Contract)

On a submitted contract (`docstatus = 1`), the primary action **"Create
Version"** opens a new pre-filled Contract Version (`contract.js`).

---

# Desk UI — Contract Version Form

- `status` is read-only (driven by the workflow).
- **Draft** → custom button **"Submit for Review"**.
- **Approved** → custom button **"Create Signature Request"**.

---

# Desk UI — Approval Form

- `status` is read-only.
- **Pending** → custom buttons **"Approve"** and **"Reject"** (with confirmations).

---

# Desk UI — Signature Request Form

- **Draft** (no envelope yet) → **"Send for Signature"** button with a
  confirmation and freeze message while Documenso processes the request.

---

# Executive Dashboard

Frappe desk dashboard (`CLM Executive Dashboard`) surfaced from number cards and
dashboard charts:

**Number cards**

- Total Contracts
- Executed Contracts
- Pending Approvals
- Active Signature Requests
- Executed Contracts Expiring in 30 Days

**Charts**

- Approvals by Status (bar, group by)
- Contracts by Status (pie)
- Contracts Expiring Over Time (line, monthly)
- Signature Requests by Status (bar)

---

# Reports

| Report | Ref DocType | Columns (highlights) |
|--------|-------------|----------------------|
| Contract Summary | Contract | current version, status, dates, owner |
| Expiring Contracts | Contract | expiration date, days remaining |
| Pending Approvals | Approval | approver, approval role, days pending |
| Pending Signature Requests | Signature Request | version, status, days pending |

All reports are script reports with declarative filters and are restricted to
the **System Manager** role.

---

# Portal UI

## Login (`/portal/login`)

Custom branded login page (`www/portal/login.py`) posting to Frappe's
`/api/method/login`. Includes show/hide password, friendly error mapping, and
CSRF handling. Authenticated counterparties are redirected to `/portal`.

## Portal Shell (`/portal`)

A Vue 3 SPA (`public/portal/portal.js`) mounted at `#portal-app`. Views:

- **Dashboard** — greeting, stat cards (Pending Review, Pending Signature,
  Executed), segmented contract list (All / Needs Action / Executed).
- **Contract Detail** — header + status badge, summary strip (status, current
  version, last activity), overview card, document card (download), approval
  card (approve/reject with remarks), signature card (recipient chips, "Sign
  Contract" button), and an activity timeline.

The portal shell auto-refreshes on focus/visibility (e.g. after returning from
the Documenso signing tab).

---

# User Workflow

```text
Contract Manager
  ↓
Create Contract (submit)
  ↓
Create Version (attach PDF)     [Draft]
  ↓
Submit for Review               [Under Review]
  ↓  ApprovalService generates Approval records
Approve / Reject                [Approved / Rejected]
  ↓
Create Signature Request        [approved]
  ↓
Send for Signature → Documenso  [Signature Requested]
  ↓ webhook (DOCUMENT_COMPLETED)
Executed                        [Executed]
  ↓
Amendment (if required) → new Contract Version
```

---

# Portal Workflow

```text
Counterparty
  ↓
Portal Login                       (/portal/login)
  ↓
Dashboard
  ↓
Contract Detail
  ↓
Review: Approve / Reject (if assigned)
  ↓
Sign: open Documenso signing URL
  ↓
Webhook marks request completed → Executed
```

---

# UI Principles

- Minimal clicks guided by context-sensitive actions
- Clear, consistent navigation across desk and portal
- Status colour coding (tone tokens via `tokens.css`)
- Role-based visibility (portal guarded by counterparty ownership)
- Responsive design (Vue SPA, design-token styling)
- Easy access to version / approval / signature history
- Reuse Frappe's built-in desk experience where possible