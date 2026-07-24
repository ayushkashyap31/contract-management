# Copyright (c) 2026, Ayush Kashyap and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DocumensoSettings(Document):
    """Configuration for the Documenso integration."""

    def validate(self):
        self._validate_base_url()

    def _validate_base_url(self):
        """Normalize and validate the configured base URL."""
        if not self.base_url:
            return

        self.base_url = self.base_url.strip().rstrip("/")

        if not self.base_url.startswith(("http://", "https://")):
            frappe.throw("Base URL must start with http:// or https://")