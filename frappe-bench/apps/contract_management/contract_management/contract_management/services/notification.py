# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

"""
NotificationService — single entry point for all notification logic.

Business services MUST use this class instead of calling Frappe
notification APIs directly. Notification delivery will be implemented
incrementally in future phases.
"""

from enum import StrEnum

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import (
    enqueue_create_notification,
)
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
        cls._create_notification(recipients, message, approval)

    @classmethod
    def notify_approval_approved(cls, approval: Document) -> None:
        """Send notification when an approval is approved."""

        raise NotImplementedError(
            "Approval approved notification will be implemented "
            "in a future phase."
        )

    @classmethod
    def notify_approval_rejected(cls, approval: Document) -> None:
        """Send notification when an approval is rejected."""

        raise NotImplementedError(
            "Approval rejected notification will be implemented "
            "in a future phase."
        )

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _get_recipients(cls, approval: Document) -> list[str]:
        """Resolve notification recipients for an approval event."""

        if not approval.approver:
            return []

        return [approval.approver]

    @classmethod
    def _build_message(cls, approval: Document, event: _NotificationEvent) -> str:
        """Build the notification message for an approval event."""

        if event == _NotificationEvent.APPROVAL_ASSIGNED:
            return _("<b>Approval Required:</b> {0}").format(approval.contract)

        raise NotImplementedError(
            "Notification message for event {0} is not implemented.".format(event)
        )

    @classmethod
    def _create_notification(
        cls,
        recipients: list[str],
        message: str,
        approval: Document,
    ) -> None:
        """Persist and dispatch a notification."""

        if not recipients:
            return

        notification_doc = {
            "type": "Alert",
            "document_type": "Approval",
            "document_name": approval.name,
            "subject": message,
            "from_user": frappe.session.user,
        }

        enqueue_create_notification(recipients, notification_doc)
