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
    SIGNATURE_REQUEST_SENT = "signature_request_sent"
    SIGNATURE_COMPLETED = "signature_completed"
    SIGNATURE_CANCELLED = "signature_cancelled"
    CONTRACT_EXECUTED = "contract_executed"


class NotificationService:
    """Entry point for all notification-related business logic."""

    # -------------------------------------------------------------------------
    # Public API — Approval Events
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
    # Public API — Signature Events
    # -------------------------------------------------------------------------

    @classmethod
    def notify_signature_request_sent(cls, signature_request: Document) -> None:
        """Send notification when a signature request is sent."""

        contract = cls._resolve_contract(signature_request)

        recipients = cls._get_recipients(
            signature_request,
            _NotificationEvent.SIGNATURE_REQUEST_SENT,
            contract,
        )
        message = cls._build_message(
            contract,
            _NotificationEvent.SIGNATURE_REQUEST_SENT,
        )
        cls._create_notification(recipients, message, signature_request)

    @classmethod
    def notify_signature_completed(cls, signature_request: Document) -> None:
        """Send notification when a signature request is completed."""

        contract = cls._resolve_contract(signature_request)

        recipients = cls._get_recipients(
            signature_request,
            _NotificationEvent.SIGNATURE_COMPLETED,
            contract,
        )
        message = cls._build_message(
            contract,
            _NotificationEvent.SIGNATURE_COMPLETED,
        )
        cls._create_notification(recipients, message, signature_request)

    @classmethod
    def notify_signature_cancelled(cls, signature_request: Document) -> None:
        """Send notification when a signature request is cancelled."""

        contract = cls._resolve_contract(signature_request)

        recipients = cls._get_recipients(
            signature_request,
            _NotificationEvent.SIGNATURE_CANCELLED,
            contract,
        )
        message = cls._build_message(
            contract,
            _NotificationEvent.SIGNATURE_CANCELLED,
        )
        cls._create_notification(recipients, message, signature_request)

    # -------------------------------------------------------------------------
    # Public API — Contract Events
    # -------------------------------------------------------------------------

    @classmethod
    def notify_contract_executed(cls, contract_version: Document) -> None:
        """Send notification when a contract version is fully executed."""

        recipients = cls._get_recipients(
            contract_version,
            _NotificationEvent.CONTRACT_EXECUTED,
        )
        message = cls._build_message(
            contract_version,
            _NotificationEvent.CONTRACT_EXECUTED,
        )
        cls._create_notification(recipients, message, contract_version)

    # -------------------------------------------------------------------------
    # Private Helpers — Recipient Resolution
    # -------------------------------------------------------------------------

    @classmethod
    def _get_recipients(
        cls,
        doc: Document,
        event: _NotificationEvent,
        contract: Document | None = None,
    ) -> list[str]:
        """Resolve notification recipients for a notification event."""

        if event == _NotificationEvent.APPROVAL_ASSIGNED:
            if not doc.approver:
                return []

            return [doc.approver]

        if event == _NotificationEvent.SIGNATURE_REQUEST_SENT:
            return list(
                {r.signer for r in doc.signature_recipients if r.signer}
            )

        if contract is None:
            contract = cls._resolve_contract(doc)

        if not contract:
            return []

        return list({c.user for c in contract.collaborators if c.user})

    @classmethod
    def _resolve_contract(cls, doc: Document):
        """Resolve the Contract document from an Approval, Signature Request, or Contract Version."""

        if doc.doctype == "Approval":
            return frappe.get_doc("Contract", doc.contract)

        if doc.doctype == "Contract Version":
            return frappe.get_doc("Contract", doc.contract)

        if doc.doctype == "Signature Request":
            version = frappe.get_doc(
                "Contract Version",
                doc.contract_version,
            )
            return frappe.get_doc("Contract", version.contract)

        return None

    # -------------------------------------------------------------------------
    # Private Helpers — Message Building
    # -------------------------------------------------------------------------

    @classmethod
    def _build_message(
        cls,
        doc: Document,
        event: _NotificationEvent,
        contract: Document | None = None,
    ) -> str:
        """Build the notification message for a notification event."""

        if event == _NotificationEvent.APPROVAL_ASSIGNED:
            return _("<b>Approval Required:</b> {0}").format(doc.contract)

        if event == _NotificationEvent.APPROVAL_APPROVED:
            return _("<b>Approval Approved:</b> {0}").format(doc.contract)

        if event == _NotificationEvent.APPROVAL_REJECTED:
            return _("<b>Approval Rejected:</b> {0}").format(doc.contract)

        if contract is None:
            contract = cls._resolve_contract(doc)

        contract_name = contract.name if contract else doc.get("contract", "")

        if event == _NotificationEvent.SIGNATURE_REQUEST_SENT:
            return _("<b>Signature Request Sent:</b> {0}").format(contract_name)

        if event == _NotificationEvent.SIGNATURE_COMPLETED:
            return _("<b>Signature Completed:</b> {0}").format(contract_name)

        if event == _NotificationEvent.SIGNATURE_CANCELLED:
            return _("<b>Signature Cancelled:</b> {0}").format(contract_name)

        if event == _NotificationEvent.CONTRACT_EXECUTED:
            return _("<b>Contract Executed:</b> {0}").format(contract_name)

        raise NotImplementedError(
            "Notification message for event {0} is not implemented.".format(event)
        )

    # -------------------------------------------------------------------------
    # Private Helpers — Notification Delivery
    # -------------------------------------------------------------------------

    @classmethod
    def _create_notification(
        cls,
        recipients: list[str],
        message: str,
        doc: Document,
    ) -> None:
        """Persist and dispatch a notification."""

        if not recipients:
            return

        notification_doc = {
            "type": "Alert",
            "document_type": doc.doctype,
            "document_name": doc.name,
            "subject": message,
            "from_user": frappe.session.user,
        }

        enqueue_create_notification(recipients, notification_doc)
