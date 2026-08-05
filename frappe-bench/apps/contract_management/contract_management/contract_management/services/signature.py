# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

from typing import Any

import io

import frappe
from frappe import _
from pypdf import PdfReader
from frappe.model.document import Document
from frappe.utils import now_datetime
from frappe.utils import get_datetime

from frappe.utils import (
    get_datetime,
    convert_utc_to_system_timezone,
    get_datetime_str,
)

from contract_management.contract_management.constants.workflow import (
    SignatureRequestStatus,
    SignatureRecipientStatus,
    VersionStatus,
)
from contract_management.contract_management.constants.transitions import (
    VERSION_TRANSITIONS,
)
from contract_management.contract_management.services.notification import (
    NotificationService,
)
from contract_management.contract_management.services.workflow import (
    WorkflowService,
)
from docusign_integration.provider import DocumensoProvider

logger = frappe.logger(__name__)

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
        cls._validate_recipients(
            [
                {"signer": r.signer, "signing_order": r.signing_order}
                for r in signature_request.signature_recipients
            ]
        )

        contract_version = frappe.get_doc(
            "Contract Version",
            signature_request.contract_version,
        )

        cls._validate_contract_version(contract_version)

        pdf_content = cls._get_pdf_content(contract_version)
        cls._validate_pdf_placeholders(pdf_content, signature_request)

        payload = cls._build_documenso_payload(
            signature_request,
            contract_version,
        )
        provider = DocumensoProvider()
        create_response = provider.create_document(payload, pdf_content)

        cls._apply_envelope_metadata(signature_request, create_response)
        cls._persist_documenso_metadata(signature_request)

        distribute_response = provider.distribute_document(
            signature_request.envelope_id,
        )

        cls._apply_recipient_metadata(signature_request, distribute_response)
        cls._persist_documenso_metadata(signature_request)

        cls._transition_contract_version(contract_version)
        cls._mark_signature_request_pending(signature_request)

        cls._notify_safely(
            NotificationService.notify_signature_request_sent,
            signature_request,
            "SIGNATURE_REQUEST_SENT",
        )

        return signature_request

    # ------------------------------------------------------------------
    # Webhook Event Handlers
    # ------------------------------------------------------------------

    @classmethod
    def process_document_completed(
        cls,
        document_payload: dict[str, Any],
    ) -> None:
        """Process a ``document.completed`` webhook from Documenso.

        Locates the corresponding Signature Request via ``externalId``,
        validates payload status, checks idempotency, updates signed
        recipients, then delegates to the shared completion transition
        method for the authoritative workflow logic.

        Args:
            document_payload: The inner ``payload`` object from the
                Documenso webhook. Must contain ``externalId``
                and ``status`` at minimum.
        """

        # ------------------------------------------------------------------
        # Step 1 — Validate required fields
        # ------------------------------------------------------------------

        external_id = document_payload.get("externalId")
        status = document_payload.get("status")

        if not external_id:
            logger.warning(
                "DOCUMENT_COMPLETED missing externalId — skipping.",
            )
            return

        if status != "COMPLETED":
            logger.warning(
                "DOCUMENT_COMPLETED unexpected status — "
                "expected: COMPLETED, received: %s, externalId: %s",
                status,
                external_id,
            )
            return

        logger.info(
            "DOCUMENT_COMPLETED processing started — externalId: %s",
            external_id,
        )

        # ------------------------------------------------------------------
        # Step 2 — Locate Signature Request
        # ------------------------------------------------------------------

        try:
            signature_request = frappe.get_doc(
                "Signature Request",
                external_id,
            )
        except frappe.DoesNotExistError:
            logger.warning(
                "DOCUMENT_COMPLETED Signature Request not found — "
                "externalId: %s",
                external_id,
            )
            return

        logger.info(
            "DOCUMENT_COMPLETED Signature Request found — "
            "name: %s, status: %s",
            signature_request.name,
            signature_request.status,
        )

        # ------------------------------------------------------------------
        # Step 3 — Idempotency
        # ------------------------------------------------------------------

        if signature_request.status == SignatureRequestStatus.COMPLETED:
            logger.info(
                "DOCUMENT_COMPLETED Signature Request already completed — "
                "name: %s, skipping",
                signature_request.name,
            )
            return

        if signature_request.status in (
            SignatureRequestStatus.CANCELLED,
            SignatureRequestStatus.EXPIRED,
        ):
            logger.warning(
                "DOCUMENT_COMPLETED Signature Request in terminal state "
                "%s — name: %s",
                signature_request.status,
                signature_request.name,
            )
            return

        # ------------------------------------------------------------------
        # Step 4 — Load Contract Version
        # ------------------------------------------------------------------

        contract_version = frappe.get_doc(
            "Contract Version",
            signature_request.contract_version,
        )

        # ------------------------------------------------------------------
        # Step 5 — Update Signature Recipients
        # ------------------------------------------------------------------

        for webhook_recipient in document_payload.get("recipients", []):
            if webhook_recipient.get("signingStatus") != "SIGNED":
                continue

            documenso_id = str(webhook_recipient["id"])
            signed_at = webhook_recipient.get("signedAt")

            matched = False

            for sr_recipient in signature_request.signature_recipients:
                if sr_recipient.documenso_recipient_id == documenso_id:
                    cls._mark_signature_recipient_signed(
                        sr_recipient,
                        signed_on=signed_at,
                    )
                    matched = True
                    logger.info(
                        "DOCUMENT_COMPLETED recipient matched — "
                        "documensoId: %s",
                        documenso_id,
                    )
                    break

            if not matched:
                logger.warning(
                    "DOCUMENT_COMPLETED recipient not found in "
                    "Signature Request — documensoId: %s, "
                    "externalId: %s",
                    documenso_id,
                    external_id,
                )

        # ------------------------------------------------------------------
        # Step 6 — Apply completion transitions
        # ------------------------------------------------------------------
    
        print("========== BEFORE TRANSITIONS ==========", flush=True)

        try:
            cls._apply_completion_transitions(
                signature_request=signature_request,
                contract_version=contract_version,
            )

            print("========== TRANSITIONS SUCCESS ==========", flush=True)

        except Exception as e:
            print("========== TRANSITIONS FAILED ==========", flush=True)
            print(repr(e), flush=True)
            raise

        logger.info(
            "DOCUMENT_COMPLETED Signature Request completed — "
            "name: %s",
            signature_request.name,
        )

        logger.info(
            "DOCUMENT_COMPLETED Contract Version executed — "
            "name: %s",
            contract_version.name,
        )

        # ------------------------------------------------------------------
        # Step 7 — Notifications (deferred)
        # ------------------------------------------------------------------

        # TODO: Add notification triggers in the Notifications phase.
        #   - notify_signature_completed(signature_request)
        #   - notify_contract_executed(contract_version)

    @classmethod
    def mark_recipient_signed(
        cls,
        signature_request_name: str,
        signer: str,
    ) -> Document:
        """
        Mark a recipient as signed.

        Args:
            signature_request_name: Name of the Signature Request.
            signer: User ID of the signing recipient.

        Returns:
            Updated Signature Request document.
        """

        signature_request = frappe.get_doc(
            "Signature Request",
            signature_request_name,
        )

        cls._validate_signature_request_for_signing(signature_request)

        recipient = cls._get_signature_recipient(
            signature_request,
            signer,
        )

        cls._validate_signature_recipient(recipient)
        cls._mark_signature_recipient_signed(recipient)

        signature_request.save()

        if cls._all_recipients_signed(signature_request):
            cls.complete_signature_request(signature_request)

        return signature_request

    @classmethod
    def _apply_completion_transitions(
        cls,
        signature_request: Document,
        contract_version: Document,
    ) -> None:
        """Apply workflow transitions to complete a signature lifecycle.

        Validates the Contract Version can transition to ``Executed``
        using the canonical workflow rules, then applies the status
        changes to both documents and persists them.

        Shared by the manual completion path (``complete_signature_request``)
        and the webhook path (``process_document_completed``) to guarantee
        a single authoritative implementation of the completion logic.

        Args:
            signature_request: The Signature Request to mark completed.
            contract_version: The Contract Version to execute.

        Raises:
            frappe.ValidationError: If the transition is not permitted
                by the workflow rules.
        """

        if not WorkflowService.can_transition(
            current_status=contract_version.status,
            new_status=VersionStatus.EXECUTED,
            transition_map=VERSION_TRANSITIONS,
        ):
            frappe.throw(
                _("Contract Version cannot be executed in its current state."),
                frappe.ValidationError,
            )

        WorkflowService.apply_system_action(
            contract_version,
            "Complete Signing",
        )

        signature_request.status = SignatureRequestStatus.COMPLETED
        signature_request.save(ignore_permissions=True)

    @classmethod
    def complete_signature_request(
        cls,
        signature_request: Document,
    ) -> Document:
        """Complete a signature request and send notifications."""

        contract_version = frappe.get_doc(
            "Contract Version",
            signature_request.contract_version,
        )

        cls._apply_completion_transitions(
            signature_request,
            contract_version,
        )

        cls._notify_safely(
            NotificationService.notify_signature_completed,
            signature_request,
            "SIGNATURE_COMPLETED",
        )

        cls._notify_safely(
            NotificationService.notify_contract_executed,
            contract_version,
            "CONTRACT_EXECUTED",
        )

        return signature_request

    @classmethod
    def cancel_signature_request(
        cls,
        signature_request_name: str,
    ) -> Document:
        """
        Cancel a draft or pending signature request.

        Args:
            signature_request_name: Name of the Signature Request.

        Returns:
            Updated Signature Request document.
        """

        signature_request = frappe.get_doc(
            "Signature Request",
            signature_request_name,
        )

        cls._validate_signature_request_for_cancellation(signature_request)

        contract_version = frappe.get_doc(
            "Contract Version",
            signature_request.contract_version,
        )

        if signature_request.status == SignatureRequestStatus.PENDING:
            cls._restore_contract_version(contract_version)

        cls._mark_signature_request_cancelled(signature_request)

        signature_request.save()

        cls._notify_safely(
            NotificationService.notify_signature_cancelled,
            signature_request,
            "SIGNATURE_CANCELLED",
        )

        return signature_request

    # -------------------------------------------------------------------------
    # Safe Notification Helper
    # -------------------------------------------------------------------------

    @staticmethod
    def _notify_safely(notify_func, signature_request, event_name):
        """Execute a notification safely without interrupting the workflow."""

        try:
            notify_func(signature_request)
        except Exception:
            frappe.log_error(
                title=_("Signature Notification Failed"),
                message=_(
                    "Signature Request: {0}\n"
                    "Event: {1}\n{2}"
                ).format(
                    signature_request.name,
                    event_name,
                    frappe.get_traceback(),
                ),
            )

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

    @staticmethod
    def _validate_pdf_placeholders(
        pdf_content: bytes,
        signature_request: Document,
    ) -> None:
        """Validate the uploaded PDF contains Documenso signature placeholders.

        Documenso scans ``{{signature,rN}}`` placeholders in the PDF during
        ``envelope/create``. Each recipient in the Signature Request must have a
        corresponding ``{{signature,rN}}`` placeholder, ordered exactly as
        ``_build_documenso_payload`` appends them.

        Only the ``signature`` placeholder type is checked here; date/name/email
        placeholders are intentionally not required.

        Args:
            pdf_content: Raw PDF bytes read from the Contract Version attachment.
            signature_request: The Signature Request being sent.

        Raises:
            frappe.ValidationError: If any recipient's signature placeholder
                is missing from the PDF.
        """

        try:
            reader = PdfReader(io.BytesIO(pdf_content))
            extracted = "".join(
                page.extract_text() or "" for page in reader.pages
            )
        except TypeError:
            # PyPDF raises TypeError when a page has no resources (e.g. a blank page)
            extracted = ""

        normalized = "".join(extracted.lower().split())
            
        

        missing: list[str] = []

        for index, recipient in enumerate(
            signature_request.signature_recipients,
            start=1,
        ):
            placeholder = f"{{{{signature,r{index}}}}}"
            if placeholder not in normalized:
                missing.append(placeholder)

        if missing:
            message = _(
                "The uploaded PDF is not prepared for Documenso signatures.\n\n"
                "Missing placeholder(s):\n{missing}\n\n"
                "Please upload a PDF containing the required Documenso "
                "signature placeholders."
            ).format(missing="\n".join(missing))

            frappe.throw(message, frappe.ValidationError)

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
    def _build_documenso_payload(
        signature_request: Document,
        contract_version: Document,
    ) -> dict[str, Any]:
        """Build the Documenso create document payload from CLM data."""

        contract = frappe.get_cached_doc(
            "Contract",
            contract_version.contract,
        )
        title = contract.contract_title or contract_version.name

        recipients = []

        for sr_recipient in signature_request.signature_recipients:
            user = frappe.get_cached_doc("User", sr_recipient.signer)

            recipients.append(
                {
                    "name": user.full_name,
                    "email": sr_recipient.email,
                    "role": "SIGNER",
                    "signingOrder": sr_recipient.signing_order,
                }
            )

        return {
            "type": "DOCUMENT",
            "title": title,
            "externalId": signature_request.name,
            "recipients": recipients,
        }

    @staticmethod
    def _get_pdf_content(
        contract_version: Document,
    ) -> bytes:
        """Read PDF bytes from the Contract Version attachment."""

        if not contract_version.document:
            frappe.throw(
                _("Cannot send for signature because the selected "
                  "Contract Version has no attached document.")
            )

        from frappe.utils.file_manager import get_file

        _filename, content = get_file(contract_version.document)
        return content

    @staticmethod
    def _apply_envelope_metadata(
        signature_request: Document,
        create_response: dict[str, Any],
    ) -> None:
        """Apply Documenso envelope ID from create response to the in-memory Signature Request."""

        signature_request.envelope_id = str(create_response["id"])

    @staticmethod
    def _apply_recipient_metadata(
        signature_request: Document,
        distribute_response: dict[str, Any],
    ) -> None:
        """Apply Documenso recipient metadata from distribute response to the in-memory Signature Request."""

        documenso_recipients = distribute_response.get("recipients", [])
        email_map = {r["email"]: r for r in documenso_recipients if "email" in r}

        for sr_recipient in signature_request.signature_recipients:
            documenso_recipient = email_map.get(sr_recipient.email)

            if documenso_recipient:
                recipient_id = documenso_recipient.get("recipientId") or documenso_recipient.get("id")
                if recipient_id is not None:
                    sr_recipient.documenso_recipient_id = str(recipient_id)

                if "signingUrl" in documenso_recipient:
                    signature_request.signing_url = str(documenso_recipient["signingUrl"])


    @staticmethod
    def _persist_documenso_metadata(
        signature_request: Document,
    ) -> None:
        """Persist Documenso envelope and recipient IDs to the database."""

        signature_request.save()

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

        WorkflowService.apply_action(
            contract_version,
            "Request Signature",
        )

    @staticmethod
    def _mark_signature_request_pending(
        signature_request: Document,
    ) -> None:
        """Mark the Signature Request as pending."""

        signature_request.status = (
            SignatureRequestStatus.PENDING
        )

        signature_request.save()

    # -------------------------------------------------------------------------
    # Mark Recipient Signed Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _validate_signature_request_for_signing(
        signature_request: Document,
    ) -> None:
        """Validate that a Signature Request can receive signatures."""

        if (
            signature_request.status
            != SignatureRequestStatus.PENDING
        ):
            frappe.throw(
                _("Only pending Signature Requests can be signed."),
                frappe.ValidationError,
            )

    @staticmethod
    def _get_signature_recipient(
        signature_request: Document,
        signer: str,
    ) -> Document:
        """Return the matching signature recipient child row."""

        for recipient in signature_request.signature_recipients:
            if recipient.signer == signer:
                return recipient

        frappe.throw(
            _("Signer {0} is not a recipient of this Signature Request.").format(
                signer,
            ),
            frappe.ValidationError,
        )

    @staticmethod
    def _validate_signature_recipient(
        recipient: Document,
    ) -> None:
        """Validate that a signature recipient can be marked signed."""

        if recipient.status != SignatureRecipientStatus.PENDING:
            frappe.throw(
                _(
                    "Only pending signature recipients can be marked as signed."
                ),
                frappe.ValidationError,
            )

    @staticmethod
    def _mark_signature_recipient_signed(
        recipient: Document,
        signed_on: str | None = None,
    ) -> None:
        """Mark a signature recipient as signed (no save).

        Args:
            recipient: The Signature Recipient child row.
            signed_on: ISO 8601 timestamp from Documenso webhook.
                Falls back to server time when not provided.
        """

        recipient.status = SignatureRecipientStatus.SIGNED
        

        if signed_on:
            utc_dt = get_datetime(signed_on)

            print("SIGNED_ON TYPE:", type(utc_dt), flush=True)
            print("SIGNED_ON VALUE:", repr(utc_dt), flush=True)
            
            local_dt = convert_utc_to_system_timezone(utc_dt)
            recipient.signed_on = get_datetime_str(local_dt)
        else:
            recipient.signed_on = now_datetime()

    @staticmethod
    def _all_recipients_signed(
        signature_request: Document,
    ) -> bool:
        """Return True if every recipient has signed."""

        return all(
            recipient.status == SignatureRecipientStatus.SIGNED
            for recipient in signature_request.signature_recipients
        )

    # -------------------------------------------------------------------------
    # Cancel Signature Request Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _validate_signature_request_for_cancellation(
        signature_request: Document,
    ) -> None:
        """Validate that a Signature Request can be cancelled."""

        if signature_request.status not in (
            SignatureRequestStatus.DRAFT,
            SignatureRequestStatus.PENDING,
        ):
            frappe.throw(
                _(
                    "Only draft or pending Signature Requests "
                    "can be cancelled."
                ),
                frappe.ValidationError,
            )

    @staticmethod
    def _restore_contract_version(
        contract_version: Document,
    ) -> None:
        """Restore the Contract Version to Approved status."""

        if not WorkflowService.can_transition(
            current_status=contract_version.status,
            new_status=VersionStatus.APPROVED,
            transition_map=VERSION_TRANSITIONS,
        ):
            frappe.throw(
                _("Contract Version cannot be restored to Approved."),
                frappe.ValidationError,
            )

        WorkflowService.apply_system_action(
            contract_version,
            "Cancel Signature",
        )

    @staticmethod
    def _mark_signature_request_cancelled(
        signature_request: Document,
    ) -> None:
        """Mark a Signature Request as cancelled (no save)."""

        signature_request.status = (
            SignatureRequestStatus.CANCELLED
        )