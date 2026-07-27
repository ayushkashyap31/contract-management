# Copyright (c) 2026, Ayush Kumar Kashyap and contributors
# For license information, please see license.txt

"""
WebhookAuthenticator — validates Documenso webhook request authenticity.

Extracts the X-Documenso-Secret header from incoming webhook requests and
compares it against the configured secret using constant-time comparison.
"""

import hmac

import frappe

from docusign_integration.exceptions import (
    DocumensoConfigurationError,
    DocumensoError,
)
from docusign_integration.integration_config import DOCUMENSO_SETTINGS_DOCTYPE

logger = frappe.logger(__name__)


class DocumensoWebhookAuthError(DocumensoError):
    """Raised when Documenso webhook authentication fails."""


class WebhookAuthenticator:
    """Validates Documenso webhook request authenticity.

    Extracts the ``X-Documenso-Secret`` header from the incoming request
    and compares it against the configured secret using constant-time
    comparison to prevent timing attacks.
    """

    HEADER = "X-Documenso-Secret"

    @classmethod
    def verify(cls, headers: dict[str, str]) -> None:
        """Verify the authenticity of a Documenso webhook request.

        Args:
            headers: HTTP headers from the webhook request.

        Raises:
            DocumensoWebhookAuthError: If the incoming secret header
                is missing or does not match the configured value.
            DocumensoConfigurationError: If the webhook secret has
                not been configured in Documenso Settings.
        """

        received = cls._extract_secret(headers)

        if not received:
            raise DocumensoWebhookAuthError(
                "Missing X-Documenso-Secret header."
            )

        settings = frappe.get_cached_doc(DOCUMENSO_SETTINGS_DOCTYPE)
        expected = settings.get_password("webhook_secret")

        if not expected:
            raise DocumensoConfigurationError(
                "Webhook secret is not configured in Documenso Settings."
            )

        if not hmac.compare_digest(received, expected):
            raise DocumensoWebhookAuthError(
                "Invalid webhook secret."
            )

    @classmethod
    def _extract_secret(cls, headers: dict[str, str]) -> str | None:
        """Extract the webhook secret header using case-insensitive lookup.

        Args:
            headers: HTTP headers dict.

        Returns:
            The header value, or None if not present.
        """

        lowered = {k.lower(): v for k, v in headers.items()}
        return lowered.get(cls.HEADER.lower())
