import frappe
from frappe import _
from frappe.exceptions import ValidationError

DOCUMENSO_SETTINGS_DOCTYPE = "Documenso Settings"


def get_settings():
    """Load and return Documenso integration settings.

    Returns:
        frappe.document.Document: The Documenso Settings document.

    Raises:
        frappe.exceptions.ValidationError: If integration is disabled.
    """
    settings = frappe.get_cached_doc(DOCUMENSO_SETTINGS_DOCTYPE)

    if not settings.enabled:

        frappe.throw(
            _("Documenso integration is disabled."),
            ValidationError,
        )

    return settings
