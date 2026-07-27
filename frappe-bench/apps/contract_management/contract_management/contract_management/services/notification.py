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

        recipients = cls._get_recipients(
            approval,
            _NotificationEvent.APPROVAL_ASSIGNED,
        )
        message = cls._build_message(
            approval,
            _NotificationEvent.APPROVAL_ASSIGNED,
        )
        cls._create_notification(recipients, message, approval)

    @classmethod
    def notify_approval_approved(cls, approval: Document) -> None:
        """Send notification when an approval is approved."""

        recipients = cls._get_recipients(
            approval,
            _NotificationEvent.APPROVAL_APPROVED,
        )
        message = cls._build_message(
            approval,
            _NotificationEvent.APPROVAL_APPROVED,
        )
        cls._create_notification(recipients, message, approval)

    @classmethod
    def notify_approval_rejected(cls, approval: Document) -> None:
        """Send notification when an approval is rejected."""

        recipients = cls._get_recipients(
            approval,
            _NotificationEvent.APPROVAL_REJECTED,
        )
        message = cls._build_message(
            approval,
            _NotificationEvent.APPROVAL_REJECTED,
        )
        cls._create_notification(recipients, message, approval)

    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _get_recipients(
        cls,
        approval: Document,
        event: _NotificationEvent,
    ) -> list[str]:
        """Resolve notification recipients for an approval event."""

        if event == _NotificationEvent.APPROVAL_ASSIGNED:
            if not approval.approver:
                return []

            return [approval.approver]

        contract = frappe.get_doc("Contract", approval.contract)

        return list({c.user for c in contract.collaborators if c.user})

    @classmethod
    def _build_message(cls, approval: Document, event: _NotificationEvent) -> str:
        """Build the notification message for an approval event."""

        if event == _NotificationEvent.APPROVAL_ASSIGNED:
            return _("<b>Approval Required:</b> {0}").format(approval.contract)

        if event == _NotificationEvent.APPROVAL_APPROVED:
            return _("<b>Approval Approved:</b> {0}").format(approval.contract)

        if event == _NotificationEvent.APPROVAL_REJECTED:
            return _("<b>Approval Rejected:</b> {0}").format(approval.contract)

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
