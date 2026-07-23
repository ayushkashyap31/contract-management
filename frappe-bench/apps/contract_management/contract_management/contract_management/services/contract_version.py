"""
Business service for Contract Version workflow operations.
"""

import frappe
from frappe import _

from contract_management.contract_management.constants.transitions import (
    VERSION_TRANSITIONS,
)
from contract_management.contract_management.constants.workflow import VersionStatus
from contract_management.contract_management.services.workflow import WorkflowService


class ContractVersionService:
    """Business operations for Contract Version."""

    @staticmethod
    def submit_for_review(version):
        """
        Submit a contract version for review.

        Args:
            version: Contract Version document.

        Raises:
            frappe.ValidationError:
                If the workflow transition is invalid.
        """

        if not WorkflowService.can_transition(
            current_status=version.status,
            new_status=VersionStatus.UNDER_REVIEW,
            transition_map=VERSION_TRANSITIONS,
        ):
            frappe.throw(
                _("Contract Version cannot be submitted for review."),
                frappe.ValidationError,
            )

        version.status = VersionStatus.UNDER_REVIEW
        version.save()

        return version