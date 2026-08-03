"""
Documenso webhook event name constants.

Centralises event name strings to avoid duplication and enforce
consistency across the webhook dispatch layer.
"""


class DocumensoWebhookEvent:
    """Documenso webhook event name constants.

    Each attribute maps to the ``event`` field value sent by Documenso
    in the webhook payload. Used by ``WebhookDispatcher`` to route
    events to handlers.

    Usage::

        from contract_management.contract_management.constants.webhook_events import (
            DocumensoWebhookEvent,
        )

        event = DocumensoWebhookEvent.DOCUMENT_COMPLETED
    """

    DOCUMENT_COMPLETED: str = "DOCUMENT_COMPLETED"
    """Document fully signed by all recipients."""

    DOCUMENT_DELETED: str = "DOCUMENT_DELETED"
    """Document removed from Documenso."""

    DOCUMENT_REJECTED: str = "DOCUMENT_REJECTED"
    """Document declined by a recipient."""

    DOCUMENT_SENT: str = "DOCUMENT_SENT"
    """Document dispatched to recipients for signature."""

    RECIPIENT_COMPLETED: str = "RECIPIENT_COMPLETED"
    """Individual recipient completed their signing task."""

    RECIPIENT_SIGNED: str = "RECIPIENT_SIGNED"
    """Individual recipient signed the document."""
