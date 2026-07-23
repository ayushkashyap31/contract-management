"""
Workflow-related constants used across the Contract Lifecycle
Management application.

Keeping workflow states centralized avoids hardcoded strings
throughout the codebase and provides a single source of truth.
"""

# Roles that participate in the approval workflow.
APPROVAL_ROLES = frozenset(
    {
        "Approver",
        "Legal",
        "Finance",
        "Business Owner",
    }
)


class ContractStatus:
    """Contract lifecycle statuses."""

    DRAFT = "Draft"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    SIGNATURE_REQUESTED = "Signature Requested"
    EXECUTED = "Executed"
    EXPIRED = "Expired"
    CANCELLED = "Cancelled"


class ApprovalStatus:
    """Approval decision statuses."""

    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class VersionStatus:
    """Contract Version lifecycle statuses."""

    DRAFT = "Draft"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    SIGNATURE_REQUESTED = "Signature Requested"
    EXECUTED = "Executed"
    SUPERSEDED = "Superseded"


class SignatureRequestStatus:
    """Signature request lifecycle statuses."""

    DRAFT = "Draft"
    PENDING = "Pending"
    SENT = "Sent"
    VIEWED = "Viewed"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    DECLINED = "Declined"
    CANCELLED = "Cancelled"
    EXPIRED = "Expired"


class SignatureRecipientStatus:
    """Signature recipient lifecycle statuses."""

    PENDING = "Pending"
    SENT = "Sent"
    VIEWED = "Viewed"
    SIGNED = "Signed"
    DECLINED = "Declined"