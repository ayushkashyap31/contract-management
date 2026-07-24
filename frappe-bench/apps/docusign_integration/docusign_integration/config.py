"""
Configuration helpers for the Documenso integration.
"""

import frappe

from docusign_integration.exceptions import DocumensoConfigurationError

DOCUMENSO_SETTINGS_DOCTYPE = "Documenso Settings"


def get_settings():
    """Return the cached Documenso integration settings."""
    settings = frappe.get_cached_doc(DOCUMENSO_SETTINGS_DOCTYPE)

    if not settings.enabled:
        raise DocumensoConfigurationError(
            "Documenso integration is disabled."
        )

    return settings