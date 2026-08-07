# System Architecture

## High Level Modules

```text
Contract Management
│
├── Contracts
├── Version Management
├── Collaborators
├── Approval Workflow
├── Signature Management
├── Counterparty Management
├── Counterparty Portal
├── Reports & Dashboard
├── Notifications
└── Webhook Processing
```

---

## Main Applications

```text
frappe-bench/apps/

├── contract_management      # Core CLM app (module: contract_management)
│
└── docusign_integration     # Documenso integration layer (module: docusign_integration)
```

The core business domain lives in the `contract_management` app. All Documenso
transport, configuration and exceptions are isolated in the separate
`docusign_integration` app so the integration can evolve or be swapped without
touching CLM business logic.

---

## Layered Architecture

The codebase is organised into explicit layers:

```text
Desk (Frappe)                 Counterparty Portal (Vue SPA + /portal)
      │                             │
      │ frappe.ui.form / APIs        │ /api/method/contract_management...portal_api.*
      ▼                             ▼
┌──────────────────────────────────────────────────────┐
│                Doctype Controllers (thin)             │
│   Contract · Contract Version · Approval ·           │
│   Signature Request                                   │
└───────────────────┬──────────────────────────────────┘
                    │ Validation + whitelisted methods
                    ▼
┌──────────────────────────────────────────────────────┐
│                   Service Layer                      │
│  ContractService  ContractVersionService  ApprovalService │
│  SignatureService  WorkflowService  NotificationService │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│                Webhook / Portal API                  │
│  api/documenso_webhook.py   portal_api.py            │
│  WebhookService WebhookAuthenticator WebhookDispatcher │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│           docusign_integration (integration app)     │
│   DocumensoProvider  DocumensoHttpClient  settings   │
└───────────────────┬──────────────────────────────────┘
                    │ REST (requests)
                    ▼
                Documenso REST API
                 (envelope create / distribute / webhooks)
```

### Layering Invariants

- **Controllers are thin.** DocType `.py` controllers only normalize/validate
  fields and expose whitelisted methods that delegate to services.
- **Business logic lives in services.** Workflow transitions, approval
  decisions, signature orchestration and notifications are service methods.
- **Webhook routing is decoupled.** The API endpoint validates authentication,
  `WebhookService` orchestrates, `WebhookDispatcher` routes by event, and
  `SignatureService` performs the actual work.
- **Integration is isolated.** No CLM service talks to Documenso directly;
  all HTTP goes through `DocumensoProvider`.

---

## Runtime Components

| Component | Role |
|-----------|------|
| Frappe Framework v16 (v16.27.1) | Application framework, desk, ORM, workflows, scheduling |
| Python 3.14 | Server-side application code |
| MariaDB | System database |
| Redis | Cache, queues, socket.io (port 13000 / 11000 / 9001) |
| Vue 3 | Counterparty Portal single-page application |
| Documenso API | Electronic signing (v1 verification + v2 envelope API) |
| Gunicorn / Nginx | Production serving (bench-managed) |

---

## Design Principles

- Modular architecture split across two apps
- Separation of concerns: controller / service / integration
- Reuse of Frappe built-in features (workflow engine, file manager, notifications)
- Independent, transport-agnostic integration layer
- Single source of truth for constants and transition rules
- Constant-time webhook authentication
- Idempotent webhook processing
- Dashboard and reports built on Frappe desk primitives