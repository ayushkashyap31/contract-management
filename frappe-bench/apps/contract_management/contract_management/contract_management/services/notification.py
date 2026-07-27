# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

"""
NotificationService — single entry point for all notification logic.

Business services MUST use this class instead of calling Frappe
notification APIs directly. Notification delivery will be implemented
incrementally in future phases.
"""

from enum import StrEnum

from frappe.model.document import Document


class _NotificationEvent(StrEnum):
    """Internal event type constants for notification dispatch."""

    APPROVAL_ASSIGNED = "approval_assigned"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"


class NotificationService:
    """Entry point for all notification-related business logic."""

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    @classmethod
    def notify_approval_assigned(cls, approval: Document) -> None:
        """Send notification when an approval is assigned to a user."""

        recipients = cls._get_recipients(approval)
        message = cls._build_message(
            approval,
            _NotificationEvent.APPROVAL_ASSIGNED,
        )
        cls._create_notification(recipients, message)

    @classmethod
    def notify_approval_approved(cls, approval: Document) -> None:
        """Send notification when an approval is approved."""

        recipients = cls._get_recipients(approval)
        message = cls._build_message(
            approval,
            _NotificationEvent.APPROVAL_APPROVED,
        )
        cls._create_notification(recipients, message)

    @classmethod
    def notify_approval_rejected(cls, approval: Document) -> None:
        """Send notification when an approval is rejected."""

        recipients = cls._get_recipients(approval)
        message = cls._build_message(
            approval,
            _NotificationEvent.APPROVAL_REJECTED,
        )
        cls._create_notification(recipients, message)

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _get_recipients(cls, approval: Document) -> list[str]:
        """Resolve notification recipients for an approval event."""

        raise NotImplementedError(
            "Notification recipient resolution will be implemented "
            "in a future phase."
        )

    @classmethod
    def _build_message(cls, approval: Document, event: _NotificationEvent) -> str:
        """Build the notification message for an approval event."""

        raise NotImplementedError(
            "Notification message building will be implemented "
            "in a future phase."
        )

    @classmethod
    def _create_notification(cls, recipients: list[str], message: str) -> None:
        """Persist and dispatch a notification."""

        raise NotImplementedError(
            "Notification delivery will be implemented "
            "in a future phase."
        )
