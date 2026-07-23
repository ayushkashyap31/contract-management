# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from contract_management.contract_management.constants.workflow import ApprovalStatus


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




    #updated the validate required fields to include contract version as well since approval is for a specific version of the contract
    
    def validate_required_fields(self):
        """Ensure mandatory fields are present."""

        if not self.contract:
            frappe.throw(_("Contract is required."))

        if not self.contract_version:
            frappe.throw(_("Contract Version is required."))

        if not self.approver:
            frappe.throw(_("Approver is required."))

        if not self.status:
            frappe.throw(_("Status is required."))



    def set_approval_date(self):
        """Automatically manage the approval date based on status."""

        if self.status == ApprovalStatus.APPROVED:
            if not self.approval_date:
                self.approval_date = now_datetime()
        else:
            self.approval_date = None


# updater the validate_duplicate_pending_approval method to check for duplicate pending approvals for the same contract version and approver

    def validate_duplicate_pending_approval(self):
        """Prevent multiple pending approvals for the same version and approver."""

        if self.status != ApprovalStatus.PENDING:
            return

        existing = frappe.db.exists(
            "Approval",
            {
                "contract_version": self.contract_version,
                "approver": self.approver,
                "status": ApprovalStatus.PENDING,
                "name": ["!=", self.name],
            },
        )

        if existing:
            frappe.throw(
                _(
                    "A pending approval already exists for this approver "
                    "for this contract version."
                )
            )