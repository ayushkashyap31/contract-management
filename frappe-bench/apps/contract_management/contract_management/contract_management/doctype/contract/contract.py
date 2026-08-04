# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from contract_management.contract_management.services.contract import (
    ContractService,
)


class Contract(Document):
    def validate(self):
        """Run before every save."""
        self.normalize_fields()
        self.validate_required_fields()
        self.validate_dates()
        self.validate_unique_collaborators()

    @frappe.whitelist()
    def create_version(self):
        """
        Compute initial values for a new draft version of this contract.

        Returns:
            dict: Initial field values for the new Contract Version:
                contract, version_number, status, is_current.
        """
        return ContractService.get_initial_version_values(self)

    def normalize_fields(self):
        """Normalize user input."""

        if self.contract_title:
            self.contract_title = self.contract_title.strip()

    def validate_required_fields(self):
        """Ensure mandatory text fields are not empty after trimming."""

        if not self.contract_title:
            frappe.throw(_("Contract Title cannot be empty."))

    def validate_dates(self):
        """Validate contract dates."""

        if (
            self.effective_date
            and self.expiration_date
            and self.effective_date > self.expiration_date
        ):
            frappe.throw(
                _("Effective Date cannot be later than Expiration Date.")
            )

    def validate_unique_collaborators(self):
        """Ensure the same user is not added multiple times."""

        seen_users = set()

        for collaborator in self.collaborators:
            if not collaborator.user:
                continue

            if collaborator.user in seen_users:
                frappe.throw(
                    _(
                        "User '{0}' cannot be added more than once as a collaborator."
                    ).format(collaborator.user)
                )

            seen_users.add(collaborator.user)