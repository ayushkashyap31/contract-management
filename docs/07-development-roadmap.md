# Development Roadmap

> Status: **IMPLEMENTATION COMPLETE.** All development phases are complete.
> The sections below reflect the delivered state of the repository.

## Phase 1 - Project Setup  ✅
- [x] Initialize Bench (frappe-bench/, `contract.local` site, developer mode)
- [x] Create the `contract_management` and `docusign_integration` apps
- [x] Install applications (apps.txt: contract_management, docusign_integration, frappe)
- [x] Documentation setup (`docs/`)

## Phase 2 - Database Design  ✅
- [x] Requirement Analysis (`01-requirement-analysis.md`)
- [x] System Architecture (`02-system-architecture.md`)
- [x] Database Design (`03-database-design.md`)
- [x] DocType Design (`04-doctype-design.md`)

## Phase 3 - Core Development  ✅
- [x] Create DocTypes (Contract, Counterparty, Contract Version, Approval, Signature Request, Collaborator, Signature Recipient, Documenso Settings)
- [x] Configure Roles (System Manager, Contract Manager, Approver, Counterparty and collaborator roles)
- [x] Configure Permissions (doctype-level + workflow role rules)
- [x] Implement Contract Version workflow (fixtures)
- [x] Create Service Layer (`services/`)
- [x] Create Reports (Contract Summary, Expiring Contracts, Pending Approvals, Pending Signature Requests)
- [x] Create Executive Dashboard + charts + number cards

## Phase 4 - Integration  ✅
- [x] Documenso integration (`docusign_integration` app)
- [x] Envelope creation (`envelope/create`) and distribution (`envelope/distribute`) via V2 API
- [x] Signature tracking and webhook handling
- [x] Webhook authentication (`X-Documenso-Secret`, constant-time compare)
- [x] Webhook dispatcher and `DOCUMENT_COMPLETED` handling

## Phase 5 - Portal  ✅
- [x] Counterparty Portal (`/portal` + `/portal/login`)
- [x] Portal login, dashboard, contract detail, review/approval, signing
- [x] Document download with ownership enforcement
- [x] Role-based home page routing (`role_home_page`)

## Phase 6 - Testing  ✅
- [x] Unit / integration tests scaffolds for each DocType
- [x] Portal API integration tests (`test_portal_api.py`: signing URL visibility and ownership)
- [x] CI workflow configured (`.github/workflows`)

## Phase 7 - Deployment & Documentation  ✅
- [x] Documentation (README, ARCHITECTURE, API, diagrams, REVIEW)
- [x] Screenshots captured (`docs/screenshots/`)
- [x] Linting / formatting tooling (ruff, eslint, prettier, pyupgrade, pre-commit)

---

## Not-Started / Deferred

The following were intentionally left as hooks for future work and are marked
in the code with `TODO` / placeholder handlers in `webhook_dispatcher.py`
(Phase 5 events):

- `document.deleted`, `document.rejected`, `document.sent`,
  `recipient.completed`, `recipient.signed` webhook handling.
- Notifications for the webhook completion path.
- Automated contract status synchronisation.