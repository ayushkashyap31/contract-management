from collections.abc import Mapping, Set

from frappe.model.document import Document
from frappe.model.workflow import apply_workflow


class WorkflowService:
    """Utility methods for validating and applying workflow transitions."""

    @staticmethod
    def can_transition(
        current_status: str,
        new_status: str,
        transition_map: Mapping[str, Set[str]],
    ) -> bool:
        """
        Return True if a transition from the current status
        to the new status is allowed.
        """

        allowed_states = transition_map.get(current_status, frozenset())
        return new_status in allowed_states

    @staticmethod
    def apply_action(
        doc: Document,
        action: str,
        ignore_permissions: bool = False,
    ) -> Document:
        """
        Apply a configured Frappe workflow action to a document.

        Resolves the active workflow for the document's doctype and applies
        the action through Frappe's workflow engine, which validates the
        transition against the configured transition table and role rules
        before updating the workflow state field and saving the document.

        Args:
            doc: Document to transition. Must already be persisted.
            action: Name of the workflow action to apply. The name must
                match an action configured on the doctype's active workflow.
            ignore_permissions: Skip document permission checks. The
                workflow transition rules are still enforced. Intended
                for background and webhook driven transitions.

        Returns:
            Document: The document after the transition has been applied.

        Raises:
            frappe.ValidationError:
                If the action is not permitted from the document's current
                state, or the doctype has no active workflow.
        """

        if ignore_permissions:
            doc.flags.ignore_permissions = True

        try:
            return apply_workflow(doc, action)
        finally:
            if ignore_permissions:
                doc.flags.ignore_permissions = False
