# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

"""
Documenso webhook endpoint.

Thin controller that receives incoming Documenso webhook events and delegates
them to WebhookService. No business logic lives here.
"""

import json

import frappe
from frappe import _

from contract_management.contract_management.services.webhook import WebhookService
from contract_management.contract_management.services.webhook_auth import (
    DocumensoWebhookAuthError,
    WebhookAuthenticator,
)
from docusign_integration.exceptions import DocumensoConfigurationError

logger = frappe.logger(__name__)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def handle_webhook() -> dict[str, str]:
    """Receive incoming Documenso webhook events.

    Parses the raw JSON request body, authenticates the request using
    ``X-Documenso-Secret`` header verification, and delegates to
    WebhookService for processing.

    Returns:
        dict: Standard acknowledgment with status and message.

    Raises:
        frappe.ValidationError: If the request body is missing or
            is not a valid JSON object.
    """

    raw = frappe.request.data

    if not raw:
        frappe.throw(
            _("Empty request body."),
            frappe.ValidationError,
        )

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        frappe.throw(
            _("Invalid JSON in request body."),
            frappe.ValidationError,
        )

    if not isinstance(payload, dict):
        frappe.throw(
            _("Webhook payload must be a JSON object."),
            frappe.ValidationError,
        )

    headers = dict(frappe.request.headers)

    try:
        WebhookAuthenticator.verify(headers=headers)
    except DocumensoConfigurationError:
        logger.exception("Documenso webhook configuration error.")
        raise
    except DocumensoWebhookAuthError:
        logger.warning(
            "Documenso webhook authentication failed - event: %s, ip: %s",
            payload.get("event"),
            frappe.local.request_ip,
        )
        frappe.response.http_status_code = 401
        return {"status": "error", "message": "Unauthorized"}

    try:
        WebhookService.handle(payload=payload, headers=headers)
    except Exception:
        logger.exception("Documenso webhook processing failed.")
        raise

    return {
        "status": "ok",
        "message": "Webhook received.",
    }
