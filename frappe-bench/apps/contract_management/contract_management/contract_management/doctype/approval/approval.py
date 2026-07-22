# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class Approval(Document):
    def validate(self):
        """Run before every save."""
        self.normalize_fields()
        self.validate_required_fields()
        self.set_approval_date()
        self.validate_duplicate_pending_approval()

    def normalize_fields(self):
        """Normalize user input."""

        if self.remarks:
            self.remarks = self.remarks.strip()

    def validate_required_fields(self):
        """Ensure mandatory fields are present."""

        if not self.contract:
            frappe.throw(_("Contract is required."))

        if not self.approver:
            frappe.throw(_("Approver is required."))

        if not self.status:
            frappe.throw(_("Status is required."))

    def set_approval_date(self):
        """Automatically manage the approval date based on status."""

        if self.status == "Approved":
            if not self.approval_date:
                self.approval_date = now_datetime()
        else:
            self.approval_date = None

    def validate_duplicate_pending_approval(self):
        """Prevent multiple pending approvals for the same contract and approver."""

        if self.status != "Pending":
            return

        existing = frappe.db.exists(
            "Approval",
            {
                "contract": self.contract,
                "approver": self.approver,
                "status": "Pending",
                "name": ["!=", self.name],
            },
        )

        if existing:
            frappe.throw(
                _(
                    "A pending approval already exists for this approver and contract."
                )
            )