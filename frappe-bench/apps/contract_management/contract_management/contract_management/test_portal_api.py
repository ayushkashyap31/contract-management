# Copyright (c) 2026, Ayush Kumar Kashyap and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from contract_management.contract_management.portal_api import (
    download_document,
    get_contract_detail,
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


class IntegrationTestPortalApi(IntegrationTestCase):
    """Integration tests for the Counterparty Portal API signing flow."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _make_user(self, email, full_name):
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = full_name
        user.flags.ignore_permissions = True
        user.insert(ignore_if_duplicate=True)
        return user

    def _make_file(self, cv_name="", df=None):
        from frappe.utils.file_manager import save_file

        pdf = (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R"
            b"/Resources<</Font<</F1 5 0 R>>>>/Parent 2 0 R>>endobj\n"
            b"4 0 obj<</Length 0>>stream\nendstream endobj\n"
            b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
            b"xref\n0 6\n0000000000 65535 f \n"
            b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n220\n%%EOF"
        )
        return save_file(
            fname="contract-test.pdf",
            content=pdf,
            dt="Contract Version",
            dn=cv_name,
            df=df,
            is_private=0,
        ).file_url

    def _make_executed_file(self, cv_name):
        """Attach a private signed PDF to a Contract Version's executed_document field.

        Mirrors SignatureService._store_executed_document: the File row is
        created with is_private=1 and linked to the Contract Version on the
        `executed_document` field.
        """
        from frappe.utils.file_manager import save_file

        return save_file(
            fname=f"{cv_name}-signed.pdf",
            content=FAKE_SIGNED_PDF,
            dt="Contract Version",
            dn=cv_name,
            df="executed_document",
            is_private=1,
        ).file_url

    def _make_docs(
        self,
        counterparty_user,
        counterparty_email,
        contract_version_status="Signature Requested",
        request_status="Pending",
        recipient_statuses=None,
    ):
        """Create Counterparty, Contract, Version, Signature Request + recipients.

        recipient_statuses is a list of (email, status). The counterparty
        recipient precedes any extra recipients in the list defaults to the
        counterparty email Pending.
        """
        if recipient_statuses is None:
            recipient_statuses = [(counterparty_email, "Pending")]

        counterparty = frappe.new_doc("Counterparty")
        counterparty.counterparty_name = "Test Counterparty"
        counterparty.counterparty_type = "Company"
        counterparty.contact_person = "Test Contact"
        counterparty.email = counterparty_email
        counterparty.portal_user = counterparty_user
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
            {"status": contract_version_status, "is_current": 1},
        )
        frappe.db.commit()

        sig = frappe.new_doc("Signature Request")
        sig.contract_version = cv.name
        sig.requested_by = counterparty_user
        sig.status = request_status
        sig.signing_url = "https://sign.example/documenso/abc"
        for email, status in recipient_statuses:
            signer = self._make_user(email, "Signer")
            sig.append(
                "signature_recipients",
                {
                    "signer": signer.name,
                    "email": email,
                    "signing_order": len(sig.signature_recipients) + 1,
                    "status": status,
                },
            )
        sig.save(ignore_permissions=True)

        return {
            "counterparty": counterparty,
            "contract": contract,
            "version": cv,
            "signature": sig,
        }

    def _make_executed_docs(self, user, email):
        """Create a fully executed contract with a private executed document."""
        docs = self._make_docs(
            user,
            email,
            contract_version_status="Executed",
            request_status="Completed",
            recipient_statuses=[(email, "Signed")],
        )
        executed_url = self._make_executed_file(docs["version"].name)
        frappe.db.set_value(
            "Contract Version",
            docs["version"].name,
            "executed_document",
            executed_url,
        )
        frappe.db.commit()
        docs["version"] = frappe.get_doc("Contract Version", docs["version"].name)
        return docs

    def _as_user(self, user, fn, *args, **kwargs):
        previous = frappe.session.user
        frappe.set_user(user)
        try:
            return fn(*args, **kwargs)
        finally:
            frappe.set_user(previous)

    def test_signing_url_provided_when_recipient_pending(self):
        user = self._make_user("portal1@example.com", "Portal One")
        docs = self._make_docs(user.name, "portal1@example.com")
        result = self._as_user(user.name, get_contract_detail, docs["contract"].name)

        self.assertTrue(result["can_sign"])
        self.assertEqual(result["signing_url"], "https://sign.example/documenso/abc")

    def test_signing_url_hidden_when_recipient_not_pending(self):
        user = self._make_user("portal2@example.com", "Portal Two")
        docs = self._make_docs(
            user.name,
            "portal2@example.com",
            recipient_statuses=[("portal2@example.com", "Signed")],
        )
        result = self._as_user(user.name, get_contract_detail, docs["contract"].name)

        self.assertIn("can_sign", result)
        self.assertIsNone(result["signing_url"])

    def test_signing_url_hidden_when_request_completed(self):
        user = self._make_user("portal3@example.com", "Portal Three")
        docs = self._make_docs(
            user.name,
            "portal3@example.com",
            contract_version_status="Executed",
            request_status="Completed",
            recipient_statuses=[("portal3@example.com", "Signed")],
        )
        result = self._as_user(user.name, get_contract_detail, docs["contract"].name)

        self.assertFalse(result["can_sign"])
        self.assertIsNone(result["signing_url"])

    def test_does_not_leak_another_recipients_url(self):
        user = self._make_user("portal4@example.com", "Portal Four")
        other_email = "internal-signer@example.com"
        docs = self._make_docs(
            user.name,
            "portal4@example.com",
            recipient_statuses=[
                ("portal4@example.com", "Signed"),
                (other_email, "Pending"),
            ],
        )
        result = self._as_user(user.name, get_contract_detail, docs["contract"].name)

        # The counterparty already signed → their turn is not pending, so even
        # though a different recipient is still pending, the URL must be hidden
        # (never leaked and not signable by the returning user).
        self.assertFalse(result["can_sign"])
        self.assertIsNone(result["signing_url"])

    def test_ownership_enforced(self):
        user_a = self._make_user("ownera@example.com", "Owner A")
        user_b = self._make_user("ownerb@example.com", "Owner B")
        docs = self._make_docs(user_a.name, "ownera@example.com")

        with self.assertRaises(frappe.PermissionError):
            self._as_user(user_b.name, get_contract_detail, docs["contract"].name)

    # --- executed document download ------------------------------------

    def test_executed_document_available_to_owner(self):
        user = self._make_user("portal1@example.com", "Portal One")
        docs = self._make_executed_docs(user.name, "portal1@example.com")

        frappe.response.clear()
        self._as_user(
            user.name,
            download_document,
            docs["version"].name,
            "executed",
        )

        self.assertEqual(frappe.response["type"], "download")
        self.assertEqual(frappe.response["display_content_as"], "attachment")
        self.assertEqual(
            frappe.response["filename"], f"{docs['version'].name}-signed.pdf"
        )
        # get_content() returns str for ASCII PDFs
        self.assertEqual(frappe.response["filecontent"], FAKE_SIGNED_PDF.decode())

    def test_executed_document_denied_for_another_counterparty(self):
        user_a = self._make_user("ownera@example.com", "Owner A")
        user_b = self._make_user("ownerb@example.com", "Owner B")
        docs = self._make_executed_docs(user_a.name, "ownera@example.com")

        with self.assertRaises(frappe.PermissionError):
            self._as_user(
                user_b.name,
                download_document,
                docs["version"].name,
                "executed",
            )

    def test_executed_document_missing(self):
        user = self._make_user("portal1@example.com", "Portal One")
        docs = self._make_docs(
            user.name,
            "portal1@example.com",
            contract_version_status="Executed",
            request_status="Completed",
            recipient_statuses=[("portal1@example.com", "Signed")],
        )
        frappe.db.set_value(
            "Contract Version", docs["version"].name, "executed_document", None
        )
        frappe.db.commit()

        with self.assertRaises(frappe.ValidationError):
            self._as_user(
                user.name,
                download_document,
                docs["version"].name,
                "executed",
            )

    def test_executed_document_denied_for_nonexecuted_version(self):
        user = self._make_user("portal2@example.com", "Portal Two")
        docs = self._make_docs(user.name, "portal2@example.com")
        # attach a signed file to the field but leave the version un-executed
        executed_url = self._make_executed_file(docs["version"].name)
        frappe.db.set_value(
            "Contract Version",
            docs["version"].name,
            "executed_document",
            executed_url,
        )
        frappe.db.commit()

        with self.assertRaises(frappe.ValidationError):
            self._as_user(
                user.name,
                download_document,
                docs["version"].name,
                "executed",
            )

    def test_executed_document_cannot_reach_arbitrary_file(self):
        """A client must not be able to fetch a file attached to a foreign version."""
        user_a = self._make_user("ownera@example.com", "Owner A")
        user_b = self._make_user("ownerb@example.com", "Owner B")
        docs_b = self._make_executed_docs(user_b.name, "ownerb@example.com")

        # Point user_a's version at user_b's executed file (which is attached
        # to docs_b's version) — must still be denied.
        foreign_url = frappe.db.get_value(
            "Contract Version", docs_b["version"].name, "executed_document"
        )
        docs_a = self._make_docs(user_a.name, "ownera@example.com")
        frappe.db.set_value(
            "Contract Version", docs_a["version"].name, "executed_document", foreign_url
        )
        frappe.db.set_value(
            "Contract Version", docs_a["version"].name, "status", "Executed"
        )
        frappe.db.commit()

        with self.assertRaises(frappe.ValidationError):
            self._as_user(
                user_a.name,
                download_document,
                docs_a["version"].name,
                "executed",
            )

    def test_executed_document_denied_for_guest(self):
        user = self._make_user("portal4@example.com", "Portal Four")
        docs = self._make_executed_docs(user.name, "portal4@example.com")

        with self.assertRaises(frappe.PermissionError):
            self._as_user(
                "Guest",
                download_document,
                docs["version"].name,
                "executed",
            )

    def test_executed_document_not_exposed_in_detail_payload(self):
        user = self._make_user("portal3@example.com", "Portal Three")
        docs = self._make_executed_docs(user.name, "portal3@example.com")

        result = self._as_user(
            user.name, get_contract_detail, docs["contract"].name
        )

        self.assertTrue(result["executed_document"]["available"])
        payload = str(result)
        self.assertNotIn("/private/files/", payload)
        self.assertNotIn("executed_document", str(result["current_version"]))

    def test_executed_document_denied_when_file_is_not_private(self):
        """Fail-closed: a public (non-private) file must never be served."""
        user = self._make_user("portal2@example.com", "Portal Two")
        docs = self._make_docs(user.name, "portal2@example.com")

        public_url = self._make_file(
            cv_name=docs["version"].name, df="executed_document"
        )
        frappe.db.set_value(
            "Contract Version",
            docs["version"].name,
            {"status": "Executed", "executed_document": public_url},
        )
        frappe.db.commit()

        with self.assertRaises(frappe.PermissionError):
            self._as_user(
                user.name,
                download_document,
                docs["version"].name,
                "executed",
            )

    def test_original_document_download_still_works(self):
        user = self._make_user("portal1@example.com", "Portal One")
        docs = self._make_docs(user.name, "portal1@example.com")

        frappe.response.clear()
        self._as_user(
            user.name,
            download_document,
            docs["version"].name,
        )

        self.assertEqual(frappe.response["type"], "download")
        self.assertEqual(frappe.response["display_content_as"], "inline")
        self.assertEqual(frappe.response["filecontent"], FAKE_SIGNED_PDF.decode())
        self.assertNotIn("-signed.pdf", frappe.response["filename"])