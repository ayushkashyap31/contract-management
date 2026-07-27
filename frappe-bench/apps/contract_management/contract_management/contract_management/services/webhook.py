# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

"""
WebhookService — entry point for incoming Documenso webhook events.

Receives raw webhook payloads from the API endpoint and handles routing
to the appropriate business service. Event-specific processing will be
implemented in future phases.
"""

from typing import Any

import frappe

logger = frappe.logger(__name__)


class WebhookService:
    """Entry point for processing incoming Documenso webhook events.

    This service receives raw webhook payloads from the API endpoint
    and handles routing to the appropriate business service based on
    event type. Event-specific processing will be implemented in
    future phases.
    """

    @classmethod
    def handle(
        cls,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> None:
        """Process an incoming Documenso webhook payload.

        Validates the payload structure and records receipt.
        Event routing and business logic will be added in
        subsequent phases.

        Args:
            payload: The parsed JSON body of the webhook request.
            headers: The HTTP headers of the webhook request.
                Reserved for future authentication use.

        Raises:
            TypeError: If payload is not a dictionary.
        """

        if not isinstance(payload, dict):
            raise TypeError("Webhook payload must be a dictionary.")

        logger.info(
            "Documenso webhook received - event: %s, top-level keys: %s",
            payload.get("event"),
            list(payload.keys()),
        )
