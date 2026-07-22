from collections.abc import Mapping, Set


class WorkflowService:
    """Utility methods for validating workflow transitions."""

    @staticmethod
    def can_transition(
        current_status: str,
        next_status: str,
        transitions: Mapping[str, Set[str]],
    ) -> bool:
        """
        Return True if a transition from the current status
        to the next status is allowed.
        """
        
        allowed_states = transitions.get(current_status, frozenset())
        return next_status in allowed_states