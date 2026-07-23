from collections.abc import Mapping, Set


class WorkflowService:
    """Utility methods for validating workflow transitions."""

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