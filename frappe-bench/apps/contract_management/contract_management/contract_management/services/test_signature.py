# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

"""Integration tests for the executed-document storage in SignatureService."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from docusign_integration.exceptions import DocumensoError

from contract_management.contract_management.constants.workflow import (
    SignatureRequestStatus,
    VersionStatus,
)
from contract_management.contract_management.services.signature import (
    SignatureService,
)

SIGNATURE_MODULE = (
    "contract_management.contract_management.services.signature.DocumensoProvider"
)

FAKE_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R"
    b"/Resources<</Font<</F1 5 0 R>>>>/Parent 2 0 R>>endobj\n"
    b"4 0 obj<</Length 0>>stream\nendstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n0000000000 65535 f \n"
    b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n220\n%%EOF"
)

FAKE_SIGNED_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R"
    b"/Resources<</Font<</F1 5 0 R>>>>/Parent 2 0 R>>endobj\n"
    b"4 0 obj<</Length 0>>stream\nendstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n0000000000 65535 f \n"
    b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n220\n%%EOF"
)


class IntegrationTestSignatureService(IntegrationTestCase):
    """Integration tests for SignatureService executed-document handling."""

    def _make_file(self, fname="contract-test.pdf"):
        from frappe.utils.file_manager import save_file

        return save_file(
            fname=fname,
            content=FAKE_PDF,
            dt="Contract Version",
            dn="",
            is_private=0,
        ).file_url

    def _make_docs(self):
        user = frappe.new_doc("User")
        user.email = "portal-sig@example.com"
        user.first_name = "Portal Signer"
        user.flags.ignore_permissions = True
        user.insert(ignore_if_duplicate=True)

        counterparty = frappe.new_doc("Counterparty")
        counterparty.counterparty_name = "Test Counterparty"
        counterparty.counterparty_type = "Company"
        counterparty.contact_person = "Test Contact"
        counterparty.email = "portal-sig@example.com"
        counterparty.portal_user = user.name
        counterparty.portal_enabled = 1
        counterparty.insert()

        contract = frappe.new_doc("Contract")
        contract.contract_title = "Test Contract"
        contract.counterparty = counterparty.name
        contract.status = "Approved"
        contract.insert()

        cv = frappe.new_doc("Contract Version")
        cv.contract = contract.name
        cv.document = self._make_file()
        cv.version_number = 1
        cv.status = "Draft"
        cv.insert()
        frappe.db.set_value(
            "Contract Version",
            cv.name,
            {"status": VersionStatus.SIGNATURE_REQUESTED, "is_current": 1},
        )
        frappe.db.commit()

        sr = frappe.new_doc("Signature Request")
        sr.contract_version = cv.name
        sr.requested_by = user.name
        sr.status = SignatureRequestStatus.PENDING
        sr.envelope_id = "envelope_1"
        sr.append(
            "signature_recipients",
            {
                "signer": user.name,
                "email": "portal-sig@example.com",
                "signing_order": 1,
                "status": "Pending",
                "documenso_recipient_id": "rec_1",
            },
        )
        sr.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "user": user,
            "counterparty": counterparty,
            "contract": contract,
            "version": cv,
            "signature": sr,
        }

    def _completed_payload(self, sr_name):
        return {
            "externalId": sr_name,
            "status": "COMPLETED",
            "recipients": [
                {
                    "id": "rec_1",
                    "signingStatus": "SIGNED",
                    "signedAt": "2026-08-01T10:00:00.000Z",
                }
            ],
        }

    def _mock_provider(self, get_envelope=None, download=None):
        patcher = patch(SIGNATURE_MODULE)
        provider_cls = patcher.start()
        provider = provider_cls.return_value
        provider.get_envelope.return_value = (
            get_envelope
            if get_envelope is not None
            else {"status": "COMPLETED", "envelopeItems": [{"id": "item_1"}]}
        )
        provider.download_envelope_item.return_value = (
            download if download is not None else FAKE_SIGNED_PDF
        )
        self.addCleanup(patcher.stop)
        return provider

    def _executed_files(self, cv_name):
        return frappe.db.get_all(
            "File",
            filters={
                "attached_to_doctype": "Contract Version",
                "attached_to_name": cv_name,
                "attached_to_field": "executed_document",
            },
            fields=["name", "is_private", "file_url"],
        )

    # ------------------------------------------------------------------
    # _store_executed_document
    # ------------------------------------------------------------------

    def test_store_executed_document_creates_private_file_and_sets_field(self):
        docs = self._make_docs()
        self._mock_provider()

        cv = frappe.get_doc("Contract Version", docs["version"].name)
        SignatureService._store_executed_document(docs["signature"], cv)

        files = self._executed_files(cv.name)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["is_private"], 1)
        self.assertEqual(cv.executed_document, files[0]["file_url"])
        self.assertIn("/private/files/", cv.executed_document)

    def test_store_executed_document_is_idempotent(self):
        docs = self._make_docs()
        provider = self._mock_provider()

        cv = frappe.get_doc("Contract Version", docs["version"].name)
        SignatureService._store_executed_document(docs["signature"], cv)
        SignatureService._store_executed_document(docs["signature"], cv)

        self.assertEqual(len(self._executed_files(cv.name)), 1)
        self.assertEqual(provider.download_envelope_item.call_count, 1)

    def test_store_executed_document_skips_when_already_set(self):
        docs = self._make_docs()
        provider = self._mock_provider()

        cv = frappe.get_doc("Contract Version", docs["version"].name)
        SignatureService._store_executed_document(docs["signature"], cv)
        provider.download_envelope_item.reset_mock()
        cv = frappe.get_doc("Contract Version", docs["version"].name)
        cv.executed_document = "/private/files/other.pdf"
        cv.save(ignore_permissions=True)

        SignatureService._store_executed_document(docs["signature"], cv)
        provider.download_envelope_item.assert_not_called()

    def test_store_executed_document_missing_envelope_id(self):
        docs = self._make_docs()
        provider = self._mock_provider()
        docs["signature"].envelope_id = None

        cv = frappe.get_doc("Contract Version", docs["version"].name)
        with self.assertRaises(DocumensoError):
            SignatureService._store_executed_document(docs["signature"], cv)
        provider.get_envelope.assert_not_called()

    def test_store_executed_document_envelope_not_completed(self):
        docs = self._make_docs()
        self._mock_provider(get_envelope={"status": "PENDING", "envelopeItems": []})

        cv = frappe.get_doc("Contract Version", docs["version"].name)
        with self.assertRaises(DocumensoError):
            SignatureService._store_executed_document(docs["signature"], cv)

    def test_store_executed_document_empty_envelope_items(self):
        docs = self._make_docs()
        self._mock_provider(
            get_envelope={"status": "COMPLETED", "envelopeItems": []}
        )

        cv = frappe.get_doc("Contract Version", docs["version"].name)
        with self.assertRaises(DocumensoError):
            SignatureService._store_executed_document(docs["signature"], cv)

    def test_store_executed_document_invalid_pdf(self):
        docs = self._make_docs()
        self._mock_provider(download=b"not a pdf")

        cv = frappe.get_doc("Contract Version", docs["version"].name)
        with self.assertRaises(DocumensoError):
            SignatureService._store_executed_document(docs["signature"], cv)

    def test_store_executed_document_download_failure(self):
        docs = self._make_docs()
        provider = self._mock_provider()
        provider.download_envelope_item.side_effect = DocumensoError("download failed")

        cv = frappe.get_doc("Contract Version", docs["version"].name)
        with self.assertRaises(DocumensoError):
            SignatureService._store_executed_document(docs["signature"], cv)
        self.assertEqual(cv.executed_document, None)

    # ------------------------------------------------------------------
    # process_document_completed (webhook path)
    # ------------------------------------------------------------------

    def test_webhook_completes_and_stores_executed_document(self):
        docs = self._make_docs()
        self._mock_provider()

        SignatureService.process_document_completed(
            self._completed_payload(docs["signature"].name)
        )

        cv = frappe.get_doc("Contract Version", docs["version"].name)
        sr = frappe.get_doc("Signature Request", docs["signature"].name)

        self.assertEqual(cv.status, VersionStatus.EXECUTED)
        self.assertEqual(sr.status, SignatureRequestStatus.COMPLETED)
        self.assertTrue(cv.executed_document)
        self.assertNotEqual(
            cv.executed_document,
            cv.document,
            "executed_document must never overwrite the original document",
        )

    def test_webhook_duplicate_delivery_creates_single_file(self):
        docs = self._make_docs()
        self._mock_provider()

        payload = self._completed_payload(docs["signature"].name)
        SignatureService.process_document_completed(payload)
        SignatureService.process_document_completed(payload)

        cv = frappe.get_doc("Contract Version", docs["version"].name)
        self.assertEqual(len(self._executed_files(cv.name)), 1)
        self.assertEqual(cv.status, VersionStatus.EXECUTED)

    def test_webhook_download_failure_rolls_back_and_retry_succeeds(self):
        docs = self._make_docs()
        provider = self._mock_provider()
        provider.download_envelope_item.side_effect = DocumensoError("transient failure")

        payload = self._completed_payload(docs["signature"].name)
        with self.assertRaises(DocumensoError):
            SignatureService.process_document_completed(payload)

        sr = frappe.get_doc("Signature Request", docs["signature"].name)
        cv = frappe.get_doc("Contract Version", docs["version"].name)
        self.assertEqual(sr.status, SignatureRequestStatus.PENDING)
        self.assertEqual(cv.status, VersionStatus.SIGNATURE_REQUESTED)
        self.assertEqual(len(self._executed_files(cv.name)), 0)

        provider.download_envelope_item.side_effect = None
        provider.download_envelope_item.return_value = FAKE_SIGNED_PDF

        SignatureService.process_document_completed(payload)

        cv = frappe.get_doc("Contract Version", docs["version"].name)
        sr = frappe.get_doc("Signature Request", docs["signature"].name)
        self.assertEqual(sr.status, SignatureRequestStatus.COMPLETED)
        self.assertEqual(cv.status, VersionStatus.EXECUTED)
        self.assertTrue(cv.executed_document)
        self.assertEqual(len(self._executed_files(cv.name)), 1)
