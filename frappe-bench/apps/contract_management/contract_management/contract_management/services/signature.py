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
from contract_management.contract_management.constants.transitions import (
    VERSION_TRANSITIONS,
)
from contract_management.contract_management.services.workflow import (
    WorkflowService,
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

    @classmethod
    def send_signature_request(
        cls,
        signature_request_name: str,
    ) -> Document:
        """
        Send a draft signature request.

        Args:
            signature_request_name: Name of the Signature Request.

        Returns:
            Updated Signature Request document.
        """

        signature_request = frappe.get_doc(
            "Signature Request",
            signature_request_name,
        )

        cls._validate_signature_request(signature_request)

        contract_version = frappe.get_doc(
            "Contract Version",
            signature_request.contract_version,
        )

        cls._validate_contract_version(contract_version)
        cls._transition_contract_version(contract_version)
        cls._mark_signature_request_pending(signature_request)

        return signature_request

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

    # -------------------------------------------------------------------------
    # Send Signature Request Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _validate_signature_request(
        signature_request: Document,
    ) -> None:
        """Validate that a Signature Request can be sent."""

        if (
            signature_request.status
            != SignatureRequestStatus.DRAFT
        ):
            frappe.throw(
                _("Only draft Signature Requests can be sent."),
                frappe.ValidationError,
            )

        if not signature_request.signature_recipients:
            frappe.throw(
                _("At least one signature recipient is required."),
                frappe.ValidationError,
            )



    @staticmethod
    def _transition_contract_version(
        contract_version: Document,
    ) -> None:
        """Transition the Contract Version into the signing phase."""

        if not WorkflowService.can_transition(
            current_status=contract_version.status,
            new_status=VersionStatus.SIGNATURE_REQUESTED,
            transition_map=VERSION_TRANSITIONS,
        ):
            frappe.throw(
                _("Contract Version cannot enter the signing phase."),
                frappe.ValidationError,
            )

        contract_version.status = VersionStatus.SIGNATURE_REQUESTED
        contract_version.save()


    @staticmethod
    def _mark_signature_request_pending(
        signature_request: Document,
    ) -> None:
        """Mark the Signature Request as pending."""

        signature_request.status = (
            SignatureRequestStatus.PENDING
        )

        signature_request.save()