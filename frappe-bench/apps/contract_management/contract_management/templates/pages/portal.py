import frappe

from contract_management.contract_management.portal_api import _get_counterparty_for_user


def get_context(context):
	context.title = "Counterparty Portal"
	context.no_cache = 1
	context.no_breadcrumbs = 1

	if frappe.session.user == "Guest" or not _get_counterparty_for_user():
		frappe.local.flags.redirect_location = "/login?redirect-to=/portal"
		raise frappe.Redirect