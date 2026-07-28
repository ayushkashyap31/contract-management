# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

"""
WebhookDispatcher — routes incoming Documenso webhook events to handlers.

Maintains a dictionary-based dispatch table mapping event names to their
corresponding handler methods. Unknown events are logged and silently
ignored. No business logic, database updates, or workflow transitions
reside in this module.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import frappe

from contract_management.contract_management.constants.webhook_events import (
    DocumensoWebhookEvent,
)
from contract_management.contract_management.services.signature import (
    SignatureService,
)

Handler = Callable[[dict[str, Any]], None]

logger = frappe.logger(__name__)


class WebhookDispatcher:
    """Routes Documenso webhook events to registered handler methods.

    Maintains a dispatch table that maps event name strings to handler
    methods. Each handler receives the full payload and performs only
    structured logging with TODO markers for future implementation.
    Unknown events are logged and silently ignored — no exception is
    raised.

    This class is intentionally stateless. All methods are classmethods
    or staticmethods to allow direct invocation without instantiation.

    Usage::

        WebhookDispatcher.dispatch(payload)
    """

    _dispatch_table: dict[str, Handler] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def dispatch(cls, payload: dict[str, Any]) -> None:
        """Route a webhook payload to the appropriate handler.

        Extracts the ``event`` field from the payload and looks up the
        corresponding handler in the dispatch table. If the event is
        recognised the handler is invoked; otherwise the event name is
        logged and processing ends silently.

        Args:
            payload: The parsed Documenso webhook payload. Must contain
                an ``event`` key whose value is a string.

        Raises:
            TypeError: If payload is not a dictionary.
        """

        if not isinstance(payload, dict):
            raise TypeError("Webhook payload must be a dictionary.")

        event = payload.get("event", "")

        if not isinstance(event, str) or not event.strip():
            logger.info(
                "Documenso webhook received without valid event field.",
            )
            return

        event = event.strip()

        logger.info(
            "Documenso webhook received - event: %s",
            event,
        )

        handler = cls._get_handler(event)

        if handler is None:
            logger.warning(
                "Documenso webhook unsupported event: %s",
                event,
            )
            return

        logger.info(
            "Documenso webhook dispatched event: %s to handler: %s",
            event,
            handler.__name__,
        )

        handler(payload)

    # ------------------------------------------------------------------
    # Dispatch table
    # ------------------------------------------------------------------

    @classmethod
    def _get_handler(
        cls,
        event: str,
    ) -> Handler | None:
        """Return the handler for *event*, or ``None`` if unknown.

        Args:
            event: The webhook event name to look up.

        Returns:
            The handler callable, or ``None`` if the event is not
            recognised.
        """

        if cls._dispatch_table is None:
            cls._dispatch_table = {
                DocumensoWebhookEvent.DOCUMENT_COMPLETED:  cls._handle_document_completed,
                DocumensoWebhookEvent.DOCUMENT_DELETED:    cls._handle_document_deleted,
                DocumensoWebhookEvent.DOCUMENT_REJECTED:   cls._handle_document_rejected,
                DocumensoWebhookEvent.DOCUMENT_SENT:       cls._handle_document_sent,
                DocumensoWebhookEvent.RECIPIENT_COMPLETED: cls._handle_recipient_completed,
                DocumensoWebhookEvent.RECIPIENT_SIGNED:    cls._handle_recipient_signed,
            }

        return cls._dispatch_table.get(event)

    # ------------------------------------------------------------------
    # Placeholder handlers
    # ------------------------------------------------------------------

    @staticmethod
    def _handle_document_completed(payload: dict[str, Any]) -> None:
        """Handle ``document.completed`` event.

        Extracts the inner document payload and delegates to
        ``SignatureService.process_document_completed`` for
        all business processing.
        """

        document_payload = payload.get("payload", {})
        SignatureService.process_document_completed(
            document_payload=document_payload,
        )

    @staticmethod
    def _handle_document_deleted(_payload: dict[str, Any]) -> None:
        """Handle ``document.deleted`` event.

        TODO ― Phase 5: Implement document deletion handling.

            - Cancel local signature request if pending.
            - Notify relevant parties.
        """

        logger.info(
            "Documenso event 'document.deleted' received — "
            "TODO: implement document deletion handling.",
        )

    @staticmethod
    def _handle_document_rejected(_payload: dict[str, Any]) -> None:
        """Handle ``document.rejected`` event.

        TODO ― Phase 5: Implement document rejection handling.

            - Mark signature request as declined.
            - Notify contract owner.
            - Update contract version status.
        """

        logger.info(
            "Documenso event 'document.rejected' received — "
            "TODO: implement document rejection handling.",
        )

    @staticmethod
    def _handle_document_sent(_payload: dict[str, Any]) -> None:
        """Handle ``document.sent`` event.

        TODO ― Phase 5: Implement document sent tracking.

            - Mark signature request as sent.
            - Notify recipients.
        """

        logger.info(
            "Documenso event 'document.sent' received — "
            "TODO: implement document sent tracking.",
        )

    @staticmethod
    def _handle_recipient_completed(_payload: dict[str, Any]) -> None:
        """Handle ``recipient.completed`` event.

        TODO ― Phase 5: Implement recipient completion tracking.

            - Mark signature recipient as signed.
            - Check if all recipients completed.
            - Trigger document completion if all signed.
        """

        logger.info(
            "Documenso event 'recipient.completed' received — "
            "TODO: implement recipient completion tracking.",
        )

    @staticmethod
    def _handle_recipient_signed(_payload: dict[str, Any]) -> None:
        """Handle ``recipient.signed`` event.

        TODO ― Phase 5: Implement recipient signed tracking.

            - Mark signature recipient as signed.
            - Record signing timestamp.
            - Check if all recipients have signed.
        """

        logger.info(
            "Documenso event 'recipient.signed' received — "
            "TODO: implement recipient signed tracking.",
        )
