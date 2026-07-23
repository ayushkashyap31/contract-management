# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from contract_management.contract_management.constants.workflow import ApprovalStatus
from contract_management.contract_management.services.approval import ApprovalService


class Approval(Document):
    def validate(self):
        """Run before every save."""
        self.normalize_fields()
        self.validate_required_fields()
        self.set_approval_date()
        self.validate_duplicate_pending_approval()
        self.validate_status_change()

    @frappe.whitelist()
    def approve(self):
        """Approve this approval record."""
        return ApprovalService.approve(self.name)

    @frappe.whitelist()
    def reject(self):
        """Reject this approval record."""
        return ApprovalService.reject(self.name)

    def normalize_fields(self):
        """Normalize user input."""

        if self.remarks:
            self.remarks = self.remarks.strip()

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

        if self.status == ApprovalStatus.PENDING:
            self.approval_date = None
        elif not self.approval_date:
            self.approval_date = now_datetime()

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

    def validate_status_change(self):
        """Prevent direct status changes to final states via form edit."""

        if self.is_new():
            return

        doc_before_save = self.get_doc_before_save()
        if not doc_before_save:
            return

        if doc_before_save.status != self.status:
            frappe.throw(
                _(
                    "Approval status cannot be changed directly. "
                    "Use the Approve or Reject action."
                )
            )