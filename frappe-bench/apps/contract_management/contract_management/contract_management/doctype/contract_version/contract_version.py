# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document

from contract_management.contract_management.constants.workflow import VersionStatus


class ContractVersion(Document):
    def before_save(self):
        """Run before saving the document."""
        if self.is_current:
            self.set_as_current_version()

    def validate(self):
        """Run before every save."""
        self.normalize_fields()
        self.validate_required_fields()
        self.validate_unique_version_number()
        self.validate_status_consistency()
        self.validate_current_version_exists()

    def normalize_fields(self):
        """Normalize user input."""
        if self.notes:
            self.notes = self.notes.strip()

    def validate_required_fields(self):
        """Ensure mandatory fields are present."""
        if not self.contract:
            frappe.throw(_("Contract is required."))
        if self.version_number is None:
            frappe.throw(_("Version Number is required."))
        if self.version_number <= 0:
            frappe.throw(_("Version Number must be greater than zero."))
        if not self.status:
            frappe.throw(_("Status is required."))

    def validate_unique_version_number(self):
        """Ensure version numbers are unique within a contract."""
        existing = frappe.db.exists(
            "Contract Version",
            {
                "contract": self.contract,
                "version_number": self.version_number,
                "name": ["!=", self.name],
            },
        )
        if existing:
            frappe.throw(
                _("Version {0} already exists for this contract.").format(
                    self.version_number
                )
            )

    def validate_status_consistency(self):
        """Ensure status and current version flag are consistent."""
        if self.is_current and self.status == VersionStatus.SUPERSEDED:
            frappe.throw(
                _("A current version cannot have the status 'Superseded'.")
            )

    def validate_current_version_exists(self):
        """
        Prevent unsetting is_current if this would leave the contract
        with zero current versions.
        """
        if self.is_current:
            return

        # Only relevant if this document was previously the current version.
        previous = self.get_doc_before_save()
        was_current = bool(previous and previous.is_current)
        if not was_current:
            return

        other_current = frappe.db.exists(
            "Contract Version",
            {
                "contract": self.contract,
                "is_current": 1,
                "name": ["!=", self.name],
            },
        )
        if not other_current:
            frappe.throw(
                _(
                    "Cannot unset 'Current Version' - the contract must always "
                    "have exactly one current version. Mark another version as "
                    "current first."
                )
            )

    def set_as_current_version(self):
        """
        Make this the only current version for the contract.
        Uses a row lock to avoid a race condition where two concurrent
        saves could each leave more than one version marked current.
        """
        current_versions = frappe.db.sql(
            """
            SELECT name FROM `tabContract Version`
            WHERE contract=%s AND is_current=1 AND name!=%s
            FOR UPDATE
            """,
            (self.contract, self.name),
            as_dict=True,
        )
        for row in current_versions:
            frappe.db.set_value(
                "Contract Version",
                row.name,
                "is_current",
                0,
                update_modified=False,
            )