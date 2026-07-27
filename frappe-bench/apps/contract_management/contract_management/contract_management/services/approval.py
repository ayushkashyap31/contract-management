# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime

from contract_management.contract_management.constants.transitions import (
    VERSION_TRANSITIONS,
)
from contract_management.contract_management.constants.workflow import (
    APPROVAL_ROLES,
    ApprovalStatus,
    VersionStatus,
)
from contract_management.contract_management.services.notification import (
    NotificationService,
)
from contract_management.contract_management.services.workflow import (
    WorkflowService,
)


class ApprovalService:
    """Business logic for Approval documents."""

    @classmethod
    def create_for_version(cls, contract_version):
        """
        Create approval records for all approval-capable collaborators.
        """

        contract = frappe.get_doc("Contract", contract_version.contract)
        approvers = cls._get_approvers(contract)

        if not approvers:
            frappe.throw(
                _("At least one approver is required before submitting for review.")
            )

        for collaborator in approvers:
            approval = cls._create_approval(contract, contract_version, collaborator)

            try:
                NotificationService.notify_approval_assigned(approval)
            except Exception:
                frappe.log_error(
                    title=_("Approval Notification Failed"),
                    message=_(
                        "Approval: {0}\nApprover: {1}\n"
                        "Event: APPROVAL_ASSIGNED\n{2}"
                    ).format(
                        approval.name,
                        approval.approver,
                        frappe.get_traceback(),
                    ),
                )

    @classmethod
    def approve(cls, approval_name):
        """
        Approve an approval record.

        Args:
            approval_name: Name of the Approval document.

        Raises:
            frappe.ValidationError:
                If the approval is not in Pending status.
        """

        approval = frappe.get_doc("Approval", approval_name)

        if approval.status != ApprovalStatus.PENDING:
            frappe.throw(
                _("Only pending approvals can be approved."),
                frappe.ValidationError,
            )

        frappe.db.set_value(
            "Approval",
            approval_name,
            {
                "status": ApprovalStatus.APPROVED,
                "approval_date": now_datetime(),
            },
        )

        cls._update_collaborator_status(approval, ApprovalStatus.APPROVED)

        if cls._check_all_approved(approval.contract_version):
            cls._approve_version(approval.contract_version)

    @classmethod
    def reject(cls, approval_name):
        """
        Reject an approval record.

        Args:
            approval_name: Name of the Approval document.

        Raises:
            frappe.ValidationError:
                If the approval is not in Pending status.
        """

        approval = frappe.get_doc("Approval", approval_name)

        if approval.status != ApprovalStatus.PENDING:
            frappe.throw(
                _("Only pending approvals can be rejected."),
                frappe.ValidationError,
            )

        frappe.db.set_value(
            "Approval",
            approval_name,
            {
                "status": ApprovalStatus.REJECTED,
                "approval_date": now_datetime(),
            },
        )

        cls._update_collaborator_status(approval, ApprovalStatus.REJECTED)

        cls._reject_version(approval.contract_version)

    @classmethod
    def _check_all_approved(cls, contract_version_name):
        """
        Check if all approvals for a contract version are approved.

        Args:
            contract_version_name: Name of the Contract Version.

        Returns:
            bool: True if all approvals are Approved.
        """

        approvals = frappe.get_all(
            "Approval",
            filters={"contract_version": contract_version_name},
            pluck="status",
        )

        if not approvals:
            return False

        return all(status == ApprovalStatus.APPROVED for status in approvals)

    @classmethod
    def _update_collaborator_status(cls, approval, status):
        """
        Synchronize the collaborator's review_status on the Contract.

        Matches the collaborator row whose user equals the approval's
        approver field.

        Args:
            approval: Approval document.
            status: New status string to set on the collaborator.
        """

        contract = frappe.get_doc("Contract", approval.contract)

        for collaborator in contract.collaborators:
            if collaborator.user == approval.approver:
                collaborator.review_status = status
                contract.save()
                return

    @classmethod
    def _approve_version(cls, contract_version_name):
        """
        Transition the Contract Version to Approved status.

        Args:
            contract_version_name: Name of the Contract Version.
        """

        version = frappe.get_doc("Contract Version", contract_version_name)

        if not WorkflowService.can_transition(
            current_status=version.status,
            new_status=VersionStatus.APPROVED,
            transition_map=VERSION_TRANSITIONS,
        ):
            frappe.throw(
                _("Contract Version cannot be approved in its current state."),
                frappe.ValidationError,
            )

        version.status = VersionStatus.APPROVED
        version.save()

    @classmethod
    def _reject_version(cls, contract_version_name):
        """
        Transition the Contract Version to Rejected status.

        Args:
            contract_version_name: Name of the Contract Version.
        """

        version = frappe.get_doc("Contract Version", contract_version_name)

        if not WorkflowService.can_transition(
            current_status=version.status,
            new_status=VersionStatus.REJECTED,
            transition_map=VERSION_TRANSITIONS,
        ):
            frappe.throw(
                _("Contract Version cannot be rejected in its current state."),
                frappe.ValidationError,
            )

        version.status = VersionStatus.REJECTED
        version.save()

    @classmethod
    def _get_approvers(cls, contract):
        """Return collaborators that participate in approvals."""

        return [
            collaborator
            for collaborator in contract.collaborators
            if collaborator.role in APPROVAL_ROLES
        ]

    @staticmethod
    def _create_approval(contract, contract_version, collaborator):
        """Create a pending approval document."""

        approval = frappe.new_doc("Approval")

        approval.contract = contract.name
        approval.contract_version = contract_version.name
        approval.approver = collaborator.user
        approval.status = ApprovalStatus.PENDING

        approval.insert()

        return approval