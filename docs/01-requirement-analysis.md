# Contract Lifecycle Management System (CLM)

## Project Overview

The Contract Lifecycle Management (CLM) System is a web application built on the
Frappe Framework and Python that manages the complete lifecycle of legal
contracts within an organization.

The system lets organizations create, review, approve, version, sign, execute
and manage contracts on a single platform while maintaining a full audit trail
and integrating with **Documenso** for electronic signatures and a dedicated
**Counterparty Portal** for external stakeholders.

---

# Problem Statement

Organizations typically manage contracts using email threads and shared folders,
which results in:

- Poor version control and unclear "which document is the source of truth"
- Lack of structured collaboration across legal, finance and business teams
- No centralized tracking of signing state
- Cumbersome approval workflows
- No visibility into who has signed what and when
- Missed expiry reminders and renewals
- No self-service for external counterparties

This project solves these problems with a centralized CLM system and role-aware
interfaces for internal staff and external counterparties.

---

# Objectives

The application allows users to:

- Create and manage legal contracts
- Maintain immutable contract versions and amendments
- Collaborate with legal, finance and business-owner teams
- Approve contract versions through an internal approval workflow
- Send approved contracts for electronic signatures via Documenso
- Track signing status and synchronise via Documenso webhooks
- Manage counterparties and their portal access
- Provide a self-service portal for external users
- Generate reports and an executive dashboard
- Emit in-app notifications for approval and signature events

---

# Personas

## Contract Manager

Responsible for:

- Creating contracts
- Attaching collaborators
- Managing versions
- Submitting versions for review
- Sending approved versions for signature
- Managing amendments (new versions)

## Collaborator

Participates in review through the contract's collaborators table. Roles include
`Reviewer`, `Approver`, `Legal`, `Finance` and `Business Owner`. Collaborators
with approval-capable roles receive Approval records.

## Approver

Responsible for:

- Reviewing an assigned contract version
- Approving or rejecting with optional remarks
- Driving the version to `Approved` (when all approvals pass) or `Rejected` (on any rejection)

## Counterparty

External user with no Desk access. Access is scoped to the Counterparty Portal.

Can:

- Log in to the portal
- View their contracts and the current version's document
- Review, approve or reject when assigned
- Sign a contract through Documenso

## Administrator / System Manager

Responsible for:

- User management and role assignments
- Permissions and configuration
- Documenso Settings
- Webhook secret configuration
- Overseeing the whole CLM module in the Frappe desk

---

# Scope

The system provides:

- Contract Management
- Version Management
- Collaboration
- Approval Workflow
- Signature Workflow (Documenso)
- Counterparty Management
- Counterparty Portal
- Webhook Processing (Documenso)
- Notifications
- Reports
- Executive Dashboard

---

# Roles and Permissions

| Role | Scope |
|------|-------|
| System Manager | Full desk access; all DocTypes; webhook and integration config. Tests Service Manager as the only doctype permission. |
| Contract Manager | Workflow transitions (`Submit for Review`, `Revise`, `Request Signature`, `Supersede`) and Draft editing on Contract Version. |
| Approver / Legal / Finance / Business Owner | Approval-capable collaborator roles; `Approve` / `Reject` workflow transitions. |
| Counterparty | Routes `role_home_page` to `/portal`; no desk access. |

---

# Project Goal

Develop a scalable, modular and maintainable Contract Lifecycle Management
System using the Frappe Framework following an explicit service-layer
architecture and enterprise software engineering practices.