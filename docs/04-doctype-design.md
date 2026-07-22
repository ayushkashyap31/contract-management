# DocType Design

## Overview

This document defines every DocType used in the Contract Lifecycle Management System.

Each DocType is designed according to its business responsibility while following Frappe best practices.

---

# 1. Contract

## Purpose

The Contract DocType is the primary business object.

It stores metadata related to a legal contract and manages its lifecycle.

The actual contract document is stored in Contract Version.

---

## Naming Series

CTR-.YYYY.-.#####

Example

CTR-2026-00001

---

## Module

Contract Management

---

## Fields

### Basic Information

| Field | Type | Mandatory |
|---------|------|-----------|
| Contract ID | Auto (Naming Series) | Yes |
| Title | Data | Yes |
| Description | Small Text | No |
| Contract Type | Select | Yes |
| Status | Select | Yes |
| Priority | Select | No |

---

### Counterparty

| Field | Type |
|---------|------|
| Counterparty | Link |
| Contact Person | Data |
| Contact Email | Data |

---

### Dates

| Field | Type |
|---------|------|
| Created Date | Date |
| Effective Date | Date |
| Expiry Date | Date |

---

### Ownership

| Field | Type |
|---------|------|
| Contract Manager | Link(User) |
| Department | Link |

---

### Version

| Field | Type |
|---------|------|
| Current Version | Link(Contract Version) |

---

### Child Tables

Collaborators

---

### Actions

- Create Version
- Create Amendment
- Send For Approval
- Send For Signature
- Cancel Contract

---

# 2. Counterparty

## Purpose

Stores external companies or people.

---

## Naming Series

CP-.#####

---

## Fields

| Field | Type |
|---------|------|
| Company Name | Data |
| Contact Person | Data |
| Email | Data |
| Phone | Data |
| Address | Small Text |

---

# 3. Contract Version

## Purpose

Stores every version of a contract.

Executed versions are immutable.

---

## Naming Series

Auto Generated

---

## Fields

| Field | Type |
|---------|------|
| Contract | Link |
| Version Number | Int |
| Document | Attach |
| Summary | Small Text |
| Is Current | Check |
| Status | Select |

---

# 4. Approval

## Purpose

Tracks internal approval history.

---

## Fields

| Field | Type |
|---------|------|
| Contract | Link |
| Approver | Link(User) |
| Status | Select |
| Remarks | Small Text |
| Approved On | Datetime |

---

# 5. Signature Request

## Purpose

Tracks Documenso signature requests.

---

## Fields

| Field | Type |
|---------|------|
| Contract | Link |
| Request ID | Data |
| Signing URL | Data |
| Status | Select |
| Sent On | Datetime |
| Completed On | Datetime |

---

# Child Table

## Collaborators

| Field | Type |
|---------|------|
| User | Link(User) |
| Role | Select |
| Review Status | Select |

---

# Relationships

Counterparty

↓

Contract

↓

Contract Version

↓

Signature Request

Contract

↓

Approval

Contract

↓

Collaborators

---

# Notes

Executed contracts cannot be edited.

Amendments always create a new Contract Version.

Only one Contract Version can be Current.

Counterparties access contracts only through the Portal.
