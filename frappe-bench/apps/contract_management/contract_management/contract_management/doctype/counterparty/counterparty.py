# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe import _

import frappe


class Counterparty(Document):
    def validate(self):
        """Run before every save."""
        self.normalize_fields()
        self.validate_required_fields()

    def normalize_fields(self):
        """Normalize user input."""

        if self.counterparty_name:
            self.counterparty_name = self.counterparty_name.strip()

        if self.contact_person:
            self.contact_person = self.contact_person.strip()

        if self.email:
            self.email = self.email.strip().lower()

        if self.address:
            self.address = self.address.strip()

    def validate_required_fields(self):
        """Ensure mandatory text fields are not empty after trimming."""

        if not self.counterparty_name:
            frappe.throw(_("Counterparty Name cannot be empty."))

        if not self.contact_person:
            frappe.throw(_("Contact Person cannot be empty."))

        if not self.email:
            frappe.throw(_("Email cannot be empty."))