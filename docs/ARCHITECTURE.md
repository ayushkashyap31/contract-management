# Architecture

This document explains how the Contract Lifecycle Management (CLM) system is
structured and why. It reflects the current implementation in the repository.

---

## 1. Overall Architecture

The system is built on the Frappe Framework and is split into **two apps**:

| App | Responsibility |
|-----|----------------|
| `contract_management` | Core CLM domain: doctypes, service layer, workflow, portal, webhooks, reports, dashboard |
| `docusign_integration` | Documenso transport, configuration and exception hierarchy |

The two-app split isolates the external signing provider from the core domain.
CLM code never calls the Documenso HTTP API directly; it always goes through
`DocumensoProvider` in the integration app.

### Runtime diagram

```text
Frappe Desk                       Counterparty Portal (Vue 3 SPA)
   │                                     │  /portal  ·  /portal/login
   │ frappe.ui.form / workflow           │  /api/method/...portal_api.*
   ▼                                     ▼
┌────────────────────────────────────────────────────────────────┐
│                 Doctype Controllers (thin)                      │
│   Contract · Contract Version · Approval · Signature Request    │
└───────────────────────────┬────────────────────────────────────┘
                            │ validation + whitelisted methods
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    Service Layer                                 │
│  ContractService · ContractVersionService · ApprovalService     │
│  SignatureService · WorkflowService · NotificationService       │
└─────────────┬──────────────────────────────┬────────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────┐   ┌───────────────────────────────────┐
│ Webhook / Portal API     │   │  docusign_integration app          │
│ api/documenso_webhook    │   │  DocumensoProvider                 │
│ portal_api               │   │  DocumensoHttpClient               │
│ WebhookService/Auth/Disp │   │  integration_config · exceptions   │
└─────────────┬────────────┘   └─────────────────┬─────────────────┘
              │                                  │ REST + webhooks
              ▼                                  ▼
   Frappe DB · Redis                    Documenso REST API
```

---

## 2. Service layer

The service layer holds the domain logic and is the single entry point for each
concern.

- **ContractService** (`services/contract.py`) — computes initial values for a
  new draft Contract Version and the next version number; enforces that only
  submitted contracts can create versions.
- **ContractVersionService** (`services/contract_version.py`) — `submit_for_review`
  validates the transition, applies the `Submit for Review` workflow action and
  generates Approval records through `ApprovalService`.
- **ApprovalService** (`services/approval.py`) — creates one Approval per
  approval-capable collaborator; approves/rejects; syncs the collaborator
  review status; transitions the version to `Approved` only when all approvals
  pass, or to `Rejected` on any rejection; triggers notifications.
- **SignatureService** (`services/signature.py`) — creates draft requests,
  sends requests to Documenso, processes the `DOCUMENT_COMPLETED` webhook,
  marks recipients signed, and completes or cancels requests. A single private
  method `_apply_completion_transitions` is shared by the manual and webhook
  completion paths so the authoritative logic lives in one place.
- **WorkflowService** (`services/workflow.py`) — thin wrapper over the Frappe
  workflow engine. `can_transition` validates against in-code transition maps;
  `apply_action` applies a configured action; `apply_system_action` elevates to
  Administrator for Guest/background flows.
- **NotificationService** (`services/notification.py`) — the single entry point
  for notifications, built on Frappe's `enqueue_create_notification`. Typed
  events, recipient resolution and message building are internalized.

### Layer invariant

Doctype controllers are thin. The `.py` controllers normalize and validate
fields and expose whitelisted methods that delegate to services; they do not
implement domain workflow. The `.js` controllers add contextual buttons that
call those methods.

---

## 3. Workflow layer

The official workflow is defined as a **Frappe workflow fixture on the
`Contract Version` DocType** (`fixtures/workflow.json`, "Contract Version
Workflow"), states are recorded in `fixtures/workflow_state.json`, and action
names in `fixtures/workflow_action_master.json`.

Alongside the fixture, `constants/transitions.py` defines the same graph as an
in-code map (`VERSION_TRANSITIONS`). The service layer consults this map first
(`WorkflowService.can_transition`) and then applies the action through the
workflow engine.

The workflow states are:

- Draft → (Submit for Review) → Under Review
- Under Review → (Approve) → Approved
- Under Review → (Reject) → Rejected
- Rejected → (Revise) → Draft
- Approved → (Request Signature) → Signature Requested
- Approved → (Supersede) → Superseded
- Signature Requested → (Complete Signing) → Executed
- Signature Requested → (Cancel Signature) → Approved

Approvals are companion records: one `Approval` row per approval-capable
collaborator. The version moves to `Approved` only after every Approval is
approved. Any rejection moves it to `Rejected`.

## 4. Portal layer

The portal is a Vue 3 single-page application served by Frappe:

- `templates/pages/portal.py` / `portal.html` — the portal shell at `/portal`.
- `www/portal/login.{py,html}` — the branded login page at `/portal/login`.
- `public/portal/portal.js` — the SPA logic and Vue components.
- `public/portal/{tokens,login,portal}.css` — shared design tokens and layout.

`portal_api.py` exposes whitelisted methods that keep the portal authorized:

- `get_session_info` — identity for the shell.
- `get_dashboard` — one aggregated contract list for the counterparty.
- `get_contract_detail` — everything the detail page renders.
- `download_document` — streams the version's file to the owner.
- `review_contract` — an approver's decision (approve/reject with remarks).

Portal users have no desk doctype permissions, so the portal API resolves data
and re-verifies ownership server-side. Mutating calls run elevated as
Administrator inside a transaction and snapshot/restore the session so the next
request is not poisoned.

## 5. Documenso integration layer

The `docusign_integration` app:

- `http_client.py` — a `requests.Session`-based, transport-agnostic client
  (`GET / POST / PATCH / DELETE`) that reads settings, sets the Bearer token
  and maps HTTP/parse failures onto the exception hierarchy.
- `provider.py` — `DocumensoProvider`: `create_document` (V2
  `envelope/create` with the PDF multipart payload), `distribute_document`
  (V2 `envelope/distribute`), `verify_connection` (V1 `documents`).
- `integration_config.py` — cached settings lookup; raises if the integration
  is disabled.
- `documenso_settings` doctype — single settings document (base URL, API token,
  webhook secret, timeout, retry).
- `exceptions.py` — typed error hierarchy.

No CLM service builds URLs or sends HTTP; it calls `DocumensoProvider`.

## 6. Webhook layer

- `api/documenso_webhook.py` — `@frappe.whitelist(allow_guest=True)` POST
  endpoint: parses the JSON body, verifies the `X-Documenso-Secret` header,
  and hands the payload to the service.
- `services/webhook_auth.py` — `WebhookAuthenticator` extracts the secret
  (case-insensitively) and compares it in constant time via `hmac.compare_digest`.
- `services/webhook.py` — `WebhookService`, the orchestrator (no routing).
- `services/webhook_dispatcher.py` — maps event names to handlers. Only
  `DOCUMENT_COMPLETED` is fully wired to `SignatureService`; the other events
  are placeholder handlers with `TODO` markers.
- `constants/webhook_events.py` — event name constants.

## 7. Notification layer

`NotificationService` is the only way business code sends notifications. It
maps typed events to recipients and a message, then dispatches through
`enqueue_create_notification`. Business services call it through `_notify_safely`
wrappers so a failure is logged rather than allowed to break the flow.
Currently delivered: approval assigned / approved / rejected, signature
request sent / cancelled / completed, contract executed.

## 8. Design decisions

1. **Two apps** — the provider is isolated from the core domain.
2. **Versioned contracts** — a contract is a stable header; the file and the
   workflow live on immutable Contract Versions.
3. **Thin controllers, rich services** — testable, reusable business logic.
4. **Canonical in-code transition map** — deterministic validation in addition
   to the desk workflow fixture.
5. **Aggregate approval** — a version is approved only after every assigned
   approver approves.
6. **Shared completion transition** — one authoritative method for manual and
   webhook completion.
7. **Idempotent webhook** — duplicates and terminal states are ignored.
8. **Ownership-guarded portal** — every portal call verifies the requesting
   counterparty owns the target records.
9. **Session-snapshot hygiene** — elevated actions restore the session to avoid
   cache poisoning.
10. **Constant-time webhook auth** — resist timing attacks.
11. **Safe notifications** — failures never break the main workflow.

## 9. Enterprise practices

- Single responsibility and explicit layering (controller / service /
  integration).
- Immutable executed records and terminal workflow states.
- Centralized constants instead of scattered status strings.
- A typed exception hierarchy for the integration.
- Server-side validation (uniqueness, sequencing, dates, ownership).
- Defense in depth: doctype permissions hold, workflow role gates, per-API
  ownership checks.
- Audit-friendly timestamps (approval date, requested/completed timestamps,
  signed timestamps).
- Logging via `frappe.logger` and safe failure isolation.
- Linting/formatting tooling and CI workflows.

## 10. Why this structure

- **Testability** — services and portal API are directly unit/integration
  testable (integration tests cover signing URL leakage and ownership).
- **Swappable integration** — replacing Documenso touches only one app.
- **Clear authorization boundaries** — desk and portal paths are explicit.
- **Operability** — centralized webhook authentication and dispatch,
  centralized notifications.
- **Maintainability** — fixed terminology, explicit layering, single source of
  truth for transitions.