# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from contract_management.contract_management.constants.workflow import (
    SignatureRequestStatus,
    SignatureRecipientStatus,
    VersionStatus,
)

RecipientData = dict[str, Any]


class SignatureService:
    """Business logic for signature workflow."""

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    @staticmethod
    def create_signature_request(
        contract_version_name: str,
        recipients: list[RecipientData],
    ) -> Document:
        """
        Create a draft signature request for an approved contract version.

        Args:
            contract_version_name: Name of the Contract Version.
            recipients: List of recipient dictionaries.

        Returns:
            The newly created Signature Request document.
        """

        contract_version = frappe.get_doc(
            "Contract Version",
            contract_version_name,
        )

        SignatureService._validate_contract_version(contract_version)
        SignatureService._validate_recipients(recipients)

        signature_request = SignatureService._build_signature_request(
            contract_version
        )

        SignatureService._append_recipients(
            signature_request,
            recipients,
        )

        signature_request.insert()

        return signature_request

    @staticmethod
    def send_signature_request(signature_request: Document) -> None:
        """Send a signature request."""
        raise NotImplementedError

    @staticmethod
    def mark_recipient_signed(signature_request: Document) -> None:
        """Mark a recipient as signed."""
        raise NotImplementedError

    @staticmethod
    def complete_signature_request(signature_request: Document) -> None:
        """Complete a signature request."""
        raise NotImplementedError

    @staticmethod
    def cancel_signature_request(signature_request: Document) -> None:
        """Cancel a signature request."""
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Validation Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _validate_contract_version(
        contract_version: Document,
    ) -> None:
        """Validate whether a contract version can be sent for signature."""

        if not contract_version.is_current:
            frappe.throw(
                _("Only the current contract version can be sent for signature.")
            )

        if contract_version.status != VersionStatus.APPROVED:
            frappe.throw(
                _("Only approved contract versions can be sent for signature.")
            )

    @staticmethod
    def _validate_recipients(
        recipients: list[RecipientData],
    ) -> None:
        """Validate signature recipients."""

        if not recipients:
            frappe.throw(
                _("At least one signature recipient is required.")
            )

        for recipient in recipients:
            if not recipient.get("signer"):
                frappe.throw(
                    _("Each recipient must have a signer.")
                )

            if recipient.get("signing_order") is None:
                frappe.throw(
                    _("Each recipient must have a signing order.")
                )

    # -------------------------------------------------------------------------
    # Builders
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_signature_request(
        contract_version: Document,
    ) -> Document:
        """Create a draft Signature Request document."""

        signature_request = frappe.new_doc("Signature Request")

        signature_request.contract_version = contract_version.name
        signature_request.requested_by = frappe.session.user
        signature_request.status = SignatureRequestStatus.DRAFT

        return signature_request

    @staticmethod
    def _append_recipients(
        signature_request: Document,
        recipients: list[RecipientData],
    ) -> None:
        """Append recipients to the Signature Request."""

        for recipient in recipients:
            user = frappe.get_cached_doc(
                "User",
                recipient["signer"],
            )

            signature_request.append(
                "signature_recipients",
                {
                    "signer": recipient["signer"],
                    "email": user.email,
                    "signing_order": recipient["signing_order"],
                    "status": SignatureRecipientStatus.PENDING,
                },
            )