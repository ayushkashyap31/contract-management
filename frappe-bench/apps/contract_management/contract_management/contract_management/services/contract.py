"""
Business service for Contract operations.
"""

import frappe
from frappe import _
from frappe.model.document import Document

from contract_management.contract_management.constants.workflow import (
    VersionStatus,
)


class ContractService:
    """Business operations for Contract."""

    @staticmethod
    def get_initial_version_values(contract: Document) -> dict:
        """
        Compute initial values for a new draft version of a contract.

        The values prefill a new, unsaved Contract Version form. The user
        attaches the required document and saves normally, keeping the
        mandatory field validation intact.

        Args:
            contract: Contract document.

        Returns:
            dict: Initial field values for the new Contract Version:
                contract, version_number, status, is_current.

        Raises:
            frappe.ValidationError:
                If the contract is not submitted.
        """

        ContractService._validate_submitted(contract)

        next_version_number = ContractService._get_next_version_number(
            contract.name
        )

        return {
            "contract": contract.name,
            "version_number": next_version_number,
            "status": VersionStatus.DRAFT,
            "is_current": 1,
        }

    @staticmethod
    def _validate_submitted(contract: Document) -> None:
        """Ensure only submitted contracts can spawn new versions."""

        if contract.docstatus != 1:
            frappe.throw(
                _("Only submitted contracts can have new versions created."),
                frappe.ValidationError,
            )

    @staticmethod
    def _get_next_version_number(contract_name: str) -> int:
        """
        Return the next version number for the contract.

        The next number is one greater than the highest existing version
        number. Contracts without any versions start at version 1.
        """

        latest_version = frappe.db.get_value(
            "Contract Version",
            {"contract": contract_name},
            "version_number",
            order_by="version_number desc",
        )

        return (latest_version or 0) + 1
