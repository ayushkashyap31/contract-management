# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

"""
WebhookService — orchestrator for incoming Documenso webhook events.

Receives parsed webhook payloads from the API endpoint and delegates
event routing to ``WebhookDispatcher``. No event-routing logic or
business processing resides in this module.
"""

from __future__ import annotations

from typing import Any

import frappe

from contract_management.contract_management.services.webhook_dispatcher import (
    WebhookDispatcher,
)

logger = frappe.logger(__name__)


class WebhookService:
    """Orchestrator for incoming Documenso webhook events.

    Receives parsed webhook payloads from the API endpoint and delegates
    event routing to ``WebhookDispatcher``. No event-specific logic or
    routing decisions reside in this class.
    """

    @classmethod
    def handle(
        cls,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> None:
        """Process an incoming Documenso webhook payload.

        Validates the payload and forwards it to ``WebhookDispatcher``
        for event routing and handler invocation.

        Args:
            payload: The parsed JSON body of the webhook request.
            headers: The HTTP headers of the webhook request.
                No longer used for authentication — retained for
                backward compatibility.

        Raises:
            TypeError: If payload is not a dictionary.
        """

        WebhookDispatcher.dispatch(payload=payload)
