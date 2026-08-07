# API Reference

This document describes every `@frappe.whitelist` endpoint implemented by the
CLM system, plus the framework's standard `/login` endpoint used by the portal.
Endpoints are grouped into **Portal API**, **Webhook API**, and **DocType
controller actions**.

All endpoints are called with Frappe's standard call convention:

```
POST /api/method/<method-path>
```

with arguments sent as form fields (or JSON). Logged-in requests require an
active Frappe session cookie; automated calls can use an API key/secret pair.

---

## Transport

| Port / Path | Purpose |
|-------------|---------|
| `POST /api/method/<path>` | Execute a whitelisted method |
| `GET /api/method/<path>?<query>` | Execute a whitelisted method with query args |
| `/api/method/login` | Framework login used by the portal |

Errors follow the standard Frappe response shape: `{"exc": "...", "message": "..."}`
with a non-2xx HTTP status.

---

## Conventions

- **Authentication**: session cookie; the portal shell and mutate-actions run
  under the logged-in counterparty's session.
- **Portal authorization**: every portal method resolves the session user's
  `Counterparty` (`portal_user` + `portal_enabled = 1`); methods that touch a
  record also verify the user owns it. Failures raise
  `frappe.PermissionError`.
- **Response**: success wraps the value under `"message"`.

---

# 1. Portal API

Module: `contract_management.contract_management.portal_api`

## 1.1 `get_session_info`

```text
POST /api/method/contract_management.contract_management.portal_api.get_session_info
```

**Purpose** — Return the identity the portal shell needs: the session user and,
when applicable, the linked Counterparty.

**Parameters**

- `*` (no required args)

**Authentication** — session; Counterparty-verified (optional; returns the
counterparty object or `None`).

**Permissions** — any authenticated user. `Guest` resolves to `counterparty: null`.

**Response (`200`)**

```json
{
  "message": {
    "user": "cp-user@example.com",
    "counterparty": {
      "name": "CP-00001",
      "counterparty_name": "Acme Corp",
      "email": "cp-user@example.com"
    }
  }
}
```

**Errors** — none enforced (may redirect for unauthenticated requests at the
page layer, not this API).

---

## 1.2 `get_dashboard`

```text
POST /api/method/contract_management.contract_management.portal_api.get_dashboard
```

**Purpose** — Return the portal dashboard data for the logged-in counterparty:
a single ordered list of their current contract versions.

**Authentication** — active session; must resolve to an enabled portal user.

**Permissions** — a `Counterparty` with `portal_enabled = 1` linked to the
session user. Otherwise raises `PermissionError`.

**Response**

```json
{
  "message": {
    "counterparty": {
      "name": "CP-00001",
      "counterparty_name": "Acme Corp",
      "email": "cp-user@example.com"
    },
    "contracts": [
      {
        "name": "CTR-2026-00001",
        "contract_title": "Master Services Agreement",
        "status": "Approved",
        "version_status": "Signature Requested",
        "version_number": 3,
        "effective_date": "2026-01-01",
        "expiration_date": "2027-01-01",
        "modified": "2026-08-01 10:00:00.000000"
      }
    ]
  }
}
```

Every row is a submitted Contract (`docstatus = 1`) belonging to the
counterparty with its **current** Contract Version. Rows are ordered so
`Signature Requested`, `Under Review`, `Approved`, `Draft` appear first (then
executed/expired/cancelled), then by `modified` descending.

**Errors** — `frappe.PermissionError` when the user has no portal counterparty.

---

## 1.3 `get_contract_detail`

```text
POST /api/method/contract_management.contract_management.portal_api.get_contract_detail
```

**Purpose** — Return everything the Contract Detail page needs for one contract:
header, current version, the latest approval and signature data, recipient
statuses, an activity timeline, and the flags that gate the review/sign actions.

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contract_name` | string | yes | Contract name (e.g. `CTR-2026-00001`) |

**Authentication** — session; portal- enabled counterparty.

**Permissions** — the contract must belong to the requesting counterparty
(`contract.counterparty == counterparty.name`); otherwise `frappe.PermissionError`.

**Response**

```json
{
  "message": {
    "contract": {
      "name": "CTR-2026-00001",
      "contract_title": "Master Services Agreement",
      "status": "Approved",
      "effective_date": "2026-01-01",
      "expiration_date": "2027-01-01",
      "creation": "2026-07-01 09:00:00"
    },
    "counterparty": {
      "name": "CP-00001",
      "counterparty_name": "Acme Corp",
      "email": "cp-user@example.com",
      "counterparty_type": "Company",
      "contact_person": "Jane Doe"
    },
    "current_version": {
      "name": "CTV-2026-00003",
      "version_number": 3,
      "status": "Signature Requested",
      "document": "/private/files/ctr-v3.pdf",
      "creation": "2026-07-30 12:00:00"
    },
    "approval": {
      "name": "APR-2026-00007",
      "approver": "jane@acme.com",
      "approver_name": "Jane Doe",
      "status": "Pending",
      "remarks": null,
      "approval_date": null
    },
    "signature": {
      "name": "SIG-2026-00005",
      "status": "Pending",
      "requested_on": "2026-07-31 09:00:00",
      "completed_on": null,
      "requested_by": "admin@example.com",
      "signing_url": "https://sign.example/documenso/abc",
      "recipients": [
        { "signer": "cp-user@example.com", "email": "cp-user@example.com", "status": "Pending", "signed_on": null }
      ]
    },
    "timeline": [
      { "type": "created", "title": "Contract created", "subtitle": null, "at": "2026-07-01 09:00:00", "tone": "" }
    ],
    "last_activity": "2026-07-01 09:00:00",
    "can_review": true,
    "can_sign": true,
    "signing_url": "https://sign.example/documenso/abc",
    "review_state": "pending"
  }
}
```

### Notable fields

- `can_review` — `true` only when the current version is `Under Review` and the
  **session user** has a `Pending` approval for it.
- `review_state` — `"pending"` / `"approved"` / `"rejected"` (or `null`) based
  on the session user's approval.
- `can_sign` — `true` only when the current version is `Signature Requested`,
  the latest request is `Pending`/`Sent`/`Viewed`, and the counterpart user's
  own recipient row is still `Pending`; the associated `signing_url` is exposed
  only in that case (never another recipient's URL).

**Errors**

| Condition | Error |
|-----------|-------|
| No portal counterparty | `frappe.PermissionError` |
| Contract not found | `frappe.PermissionError` |
| Contract owned by another counterparty | `frappe.PermissionError` |

---

## 1.4 `download_document`

```text
POST /api/method/contract_management.contract_management.portal_api.download_document?contract_version=CTV-2026-00003
```

**Purpose** — Stream the attached PDF of a Contract Version to the owning
counterparty. Gate via ownership rather than exposing `/private/files/`.

**Parameters**

| Name | Type | Required |
|------|------|----------|
| `contract_version` | string | yes |

**Authentication** — portal-enabled session.

**Permissions** — the version's contract must belong to the session user's
counterparty.

**Response** — a file-response:

- `type: download` with `filename` (original file name)
- `display_content_as: inline` for PDFs, else `attachment`
- body bytes

**Errors**

| Case | Error |
|------|-------|
| No portal | `frappe.PermissionError` |
| Version missing/no document | `frappe.ValidationError` ("No document...") |
| Not owner | `frappe.PermissionError` |
| File record missing | `frappe.ValidationError` |

---

## 1.5 `review_contract`

```text
POST /api/method/contract_management.contract_management.portal_api.review_contract
```

**Purpose** — Record a counterparty approver's decision on a contract version.
A thin, transactional wrapper over `ApprovalService`.

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contract_name` | string | yes | Contract being reviewed |
| `action` | string | yes | `approve` or `reject` |
| `remarks` | string | no | Optional note stored on the Approval |

**Authentication** — portal session.

**Permissions**

- The contract must belong to the user's counterparty.
- The user must have a `Pending` approval for the current version; otherwise
  `frappe.PermissionError`.

**Behavior** — runs inside a single transaction (rolls back on failure). The
approval decision, remarks (`frappe.db.set_value`) and the version transition
are atomic. Runs elevated as Administrator then restores the session (the
Approval/version doctypes are System-Manager-only).

**Response** — the refreshed `get_contract_detail` response for the contract.

**Errors**

| Case | Error |
|------|-------|
| Non-portal | `frappe.PermissionError` |
| Invalid action | `frappe.ValidationError` ("Action must be 'approve' or 'reject'") |
| Not owner | `frappe.PermissionError` |
| Not a pending approver | `frappe.PermissionError` |
| Version/Approval invalid at service layer | `frappe.ValidationError` |

---

# 2. Webhook

Module: `contract_management.contract_management.api.documenso_webhook`

## 2.1 `handle_webhook`

```text
POST /api/method/contract_management.contract_management.api.documenso_webhook.handle_webhook
```

**Purpose** — Receive Documenso webhooks (signed-secret verified) and dispatch
them for processing.

**Decorator** — `@frappe.whitelist(allow_guest=True, methods=["POST"])` (Guest is
allowed because Documenso is not a Frappe user).

**Parameters** — the raw JSON request body is a Documenso webhook payload:

```json
{
  "event": "DOCUMENT_COMPLETED",
  "payload": {
    "externalId": "SIG-2026-00005",
    "status": "COMPLETED",
    "recipients": [
      { "id": "rec_1", "signingStatus": "SIGNED", "signedAt": "2026-07-31T10:00:00.000Z" }
    ]
  }
}
```

**Authentication**

- Guest request.
- `X-Documenso-Secret` header must equal the configured `webhook_secret`
  (compared with `hmac.compare_digest`).
- If the secret is not configured → `DocumensoConfigurationError` (re-raised).
- If the header is missing or mismatched → HTTP `401` with
  `{"status": "error", "message": "Unauthorized"}`.

**Supported event** — `DOCUMENT_COMPLETED` is processed by
`SignatureService.process_document_completed`:

1. validates `externalId` + `status == "COMPLETED"`.
2. locates the `Signature Request` by externalId.
3. ignores duplicates (already `Completed`) and terminal states
   (Cancelled/Expired).
4. marks matching recipients signed (via `documenso_recipient_id`).
5. transitions the Contract Version to `Executed` (`Complete Signing`) and the
   request to `Completed` — idempotently.

Other events (`document.deleted`, `document.rejected`, `document.sent`,
`recipient.completed`, `recipient.signed`) are logged as not-yet-handled.

**Response** (success)

```json
{ "message": { "status": "ok", "message": "Webhook received." } }
```

**Errors**

| Case | HTTP / behavior |
|------|-----------------|
| Empty body | `frappe.ValidationError` ("Empty request body") |
| Invalid JSON | `frappe.ValidationError` ("Invalid JSON") |
| Non-object payload | `frappe.ValidationError` |
| Config error | re-raised |
| Bad secret | `401`, `{"status":"error","message":"Unauthorized"}` |
| Processing exception | re-raised (500) |

---

# 3. DocType controller actions

These are `@frappe.whitelist` methods on DocType controllers, invoked from the
desk (or any client) as:

```text
POST /api/method/contract_management.contract_management.doctype.<doctype>.<controller>.method
```

## 3.1 Contract — `create_version`

Module: `...doctype.contract.contract`

**Purpose** — compute initial values for a new draft Contract Version for the
given (submitted) contract; used by the "Create Version" button.

**Authentication** — desk session.

**Permissions** — requires submit-level rights; only a submitted contract
(`docstatus == 1`) may create versions.

**Parameters** — none.

**Response**

```json
{
  "message": {
    "contract": "CTR-2026-00001",
    "version_number": 4,
    "status": "Draft",
    "is_current": 1
  }
}
```

**Errors**

- Not submitted → `frappe.ValidationError` ("Only submitted contracts can have
  new versions created.")

## 3.2 Contract Version — `submit_for_review`

Module: `...doctype.contract_version.contract_version`

**Purpose** — submit the version for review and generate Approval records.

**Authentication** — desk session.

**Permissions** — workflow-dependent; the transition must be valid
(`can_transition`), and `WorkflowService.apply_action` applies the configured
role rules.

**Parameters** — none.

**Response** — the updated `Contract Version` object.

**Errors** — `frappe.ValidationError` if the transition is invalid or no
approval-capable collaborator exists.

## 3.3 Contract Version — `create_signature_request`

**Purpose** — create a draft `Signature Request` for this (Approved) version.

**Parameters** — none.

**Response**

```json
{ "message": "SIG-2026-00005" }
```

(the name of the created request; the desk routes to it).

**Errors** — the Signature request path validates it in `SignatureService`
(only approved/current versions).

## 3.4 Approval — `approve` / `reject`

Module: `...doctype.approval.approval`

**Purpose** — approve or reject an Approval record (used by the desk Approve /
Reject buttons).

**Parameters** — none (the current document).

**Response** — `200`; then the user reloads the form.

**Errors** — `frappe.ValidationError` if the Approval is not `Pending`, or the
transition/aggregation fails at the service layer.

## 3.5 Signature Request — `send_for_signature`

Module: `...doctype.signature_request.signature_request`

**Purpose** — send a Draft request to the validation, Documenso and completion
flow.

**Parameters** — none (uses the current document's recipients).

**Response** — the updated `Signature Request` object.

**Errors** — `frappe.ValidationError` for invalid state / missing recipients /
PDF placeholder issues; provider exceptions surface as Documenso errors.

---

# 4. Framework — `login`

Frappe built-in: `POST /api/method/login`

Used by the portal (`/portal/login`).

**Parameters**

| Name | Value |
|------|-------|
| `cmd` | `"login"` |
| `usr` | email / user id |
| `pwd` | password |

**Parameters** — form-encoded.

**Success** — sets the session cookie and returns `message: "...Logged In"`.
The portal then navigates to `/portal`.

**Errors** — `401` / `403` / `429` handled by `login.js`, which shows friendly
messages for invalid credentials, disabled/unauthorized accounts and rate
limiting.