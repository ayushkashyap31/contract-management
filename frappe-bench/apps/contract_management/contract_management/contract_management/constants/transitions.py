"""
Workflow transition definitions.

These transition maps define the valid state transitions
for workflow-enabled DocTypes.
"""

from contract_management.contract_management.constants.workflow import VersionStatus


VERSION_TRANSITIONS = {
    VersionStatus.DRAFT: {
        VersionStatus.UNDER_REVIEW,
    },
    VersionStatus.UNDER_REVIEW: {
        VersionStatus.APPROVED,
        VersionStatus.REJECTED,
    },
    VersionStatus.REJECTED: {
        VersionStatus.DRAFT,
    },
    VersionStatus.APPROVED: {
        VersionStatus.SIGNATURE_REQUESTED,
        VersionStatus.SUPERSEDED,
    },
    VersionStatus.SIGNATURE_REQUESTED: {
        VersionStatus.EXECUTED,
        VersionStatus.APPROVED,  # Allow restoring when a signature request is cancelled
    },
    VersionStatus.EXECUTED: set(),
    VersionStatus.SUPERSEDED: set(),
}