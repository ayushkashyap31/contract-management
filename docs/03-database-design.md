# Database Design

## Introduction

The database is designed using a normalized relational model to ensure scalability, maintainability, and data integrity.

Instead of storing all information in a single Contract document, the application separates business entities into independent DocTypes while leveraging Frappe's built-in features wherever appropriate.

---

# Design Principles

The database follows these principles:

- Single Responsibility Principle
- No duplicate data
- Proper Link relationships
- Child Tables only for dependent data
- Reuse Frappe features whenever possible
- Executed contracts are immutable
- Every business event is traceable

---

# Main Entities

The application consists of the following primary entities.

## 1. Contract

The central entity of the application.

Represents a legal agreement between the organization and a counterparty.

Responsibilities:

- Store contract metadata
- Maintain lifecycle status
- Reference current version
- Manage collaborators
- Trigger approvals
- Trigger signatures

---

## 2. Counterparty

Represents the external organization or individual with whom the contract is signed.

Responsibilities:

- Company details
- Contact information
- Portal access
- Multiple contracts

---

## 3. Contract Version

Stores every version of a contract.

Responsibilities:

- Version history
- Attached contract document
- Current version indicator
- Previous version reference

Executed versions are never modified.

---

## 4. Signature Request

Represents a signature request generated using Documenso.

Responsibilities:

- External Request ID
- Signature status
- Signing URL
- Synchronization status

---

# Child Tables

The following child tables belong to the Contract DocType.

## Collaborators

Stores users participating in contract review.

Fields:

- User
- Role
- Review Status

---

## Approvals

Stores approval records.

Fields:

- Approver
- Status
- Remarks
- Approved On

---

# Entity Relationships

Counterparty

↓

One Counterparty

↓

Many Contracts

Contract

↓

One Contract

↓

Many Versions

Contract

↓

One Contract

↓

Many Signature Requests

Contract

↓

One Contract

↓

Many Collaborators

Contract

↓

One Contract

↓

Many Approvals

---

# Entity Relationship Diagram

Counterparty

1

↓

N

Contract

│

├──────────► Contract Version

│

├──────────► Signature Request

│

├──────────► Collaborators

│

└──────────► Approvals

---

# Lifecycle Rules

Draft contracts are editable.

Executed contracts become read-only.

Creating an amendment generates a new Contract Version instead of modifying the executed version.

Deleting executed contracts is prohibited.

Signature requests can only be generated after internal approval.

---

# Naming Series

Contract

CTR-.YYYY.-.#####

Example:

CTR-2026-00001

---

Counterparty

CP-.#####

Example:

CP-00001

---

Contract Version

CTR-2026-00001-V1

CTR-2026-00001-V2

CTR-2026-00001-V3

---

Signature Request

SIG-.#####

Example:

SIG-00001

---

# Data Integrity Rules

Every Contract must belong to one Counterparty.

A Contract always has one Current Version.

Only one Version can be marked as Current.

Executed Versions cannot be edited.

Signature Requests always belong to one Contract.

Approvals belong only to one Contract.

Collaborators belong only to one Contract.

---

# Future Enhancements

- AI Contract Review
- OCR Support
- Clause Library
- Contract Templates
- Risk Analysis
- Renewal Automation
- Bulk Import