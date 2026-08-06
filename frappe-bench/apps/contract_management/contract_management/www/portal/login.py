import frappe

from contract_management.contract_management.portal_api import _get_counterparty_for_user


def get_context(context):
	context.title = "Contract Portal"
	context.no_cache = 1
	context.body_class = "portal-login"

	if frappe.session.user != "Guest" and _get_counterparty_for_user():
		frappe.local.flags.redirect_location = "/portal"
		raise frappe.Redirect