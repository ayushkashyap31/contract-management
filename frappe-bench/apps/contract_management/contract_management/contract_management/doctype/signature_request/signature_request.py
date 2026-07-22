# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class SignatureRequest(Document):
    def validate(self):
        """Run before every save."""
        self.normalize_fields()
        self.validate_required_fields()
        self.set_requested_on()
        self.set_completed_on()
        self.validate_duplicate_active_request()

        self.validate_unique_signer_emails()
        self.validate_unique_signing_order()
        self.validate_signing_order_sequence()
        self.update_recipient_signed_on()

    def normalize_fields(self):
        """Normalize user input."""

        if self.envelope_id:
            self.envelope_id = self.envelope_id.strip()

        if self.signing_url:
            self.signing_url = self.signing_url.strip()

    def validate_required_fields(self):
        """Ensure mandatory fields are present."""

        if not self.contract_version:
            frappe.throw(_("Contract Version is required."))

        if not self.requested_by:
            frappe.throw(_("Requested By is required."))

        if not self.status:
            frappe.throw(_("Status is required."))

    def set_requested_on(self):
        """Automatically set the request timestamp."""

        if not self.requested_on:
            self.requested_on = now_datetime()

    def set_completed_on(self):
        """Automatically manage completion timestamp."""

        if self.status == "Completed":
            if not self.completed_on:
                self.completed_on = now_datetime()
        else:
            self.completed_on = None

    def validate_duplicate_active_request(self):
        """Prevent multiple active signature requests."""

        active_statuses = [
            "Draft",
            "Pending",
            "Sent",
            "Viewed",
        ]

        if self.status not in active_statuses:
            return

        existing = frappe.db.exists(
            "Signature Request",
            {
                "contract_version": self.contract_version,
                "status": ["in", active_statuses],
                "name": ["!=", self.name],
            },
        )

        if existing:
            frappe.throw(
                _("An active Signature Request already exists for this Contract Version.")
            )

    def validate_unique_signer_emails(self):
        """Ensure recipient emails are unique."""

        emails = set()

        for recipient in self.signature_recipients:
            email = recipient.email.strip().lower()

            if email in emails:
                frappe.throw(
                    _("Duplicate signer email: {0}").format(email)
                )

            emails.add(email)

    def validate_unique_signing_order(self):
        """Ensure signing order values are unique."""

        orders = set()

        for recipient in self.signature_recipients:

            if recipient.signing_order in orders:
                frappe.throw(
                    _("Duplicate signing order: {0}").format(
                        recipient.signing_order
                    )
                )

            orders.add(recipient.signing_order)

    def validate_signing_order_sequence(self):
        """Ensure signing order starts at 1 with no gaps."""

        if not self.signature_recipients:
            return

        orders = sorted(
            recipient.signing_order
            for recipient in self.signature_recipients
        )

        expected = list(range(1, len(orders) + 1))

        if orders != expected:
            frappe.throw(
                _("Signing order must be sequential starting from 1.")
            )

    def update_recipient_signed_on(self):
        """Automatically manage recipient signed timestamps."""

        for recipient in self.signature_recipients:

            if recipient.status == "Signed":
                if not recipient.signed_on:
                    recipient.signed_on = now_datetime()
            else:
                recipient.signed_on = None