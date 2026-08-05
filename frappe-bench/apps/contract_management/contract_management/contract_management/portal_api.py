import frappe


def _get_counterparty_for_user(user=None):
	"""Return the Counterparty linked to the given portal user (or session user).

	Guards all portal APIs: only the counterparty user themselves may access
	their portal data. Returns None for Guest / unlinked / disabled accounts.
	"""
	user = user or frappe.session.user

	if not user or user == "Guest":
		return None

	counterparties = frappe.get_all(
		"Counterparty",
		filters={"portal_user": user, "portal_enabled": 1},
		fields=["name", "counterparty_name", "email"],
		limit=1,
	)

	if not counterparties:
		return None

	return counterparties[0]


def _require_counterparty():
	counterparty = _get_counterparty_for_user()
	if not counterparty:
		frappe.throw(
			"Your account does not have access to the portal. Contact your administrator.",
			frappe.PermissionError,
		)
	return counterparty


@frappe.whitelist()
def get_session_info():
	"""Return the logged-in portal user's identity (used by the portal shell)."""
	counterparty = _get_counterparty_for_user()
	return {
		"user": frappe.session.user,
		"counterparty": counterparty,
	}


_CONTRACT_ROW_SQL = """
	SELECT
		cv.contract AS name,
		c.contract_title,
		c.status,
		cv.status AS version_status,
		cv.version_number,
		c.effective_date,
		c.expiration_date,
		c.modified
	FROM `tabContract Version` cv
	JOIN `tabContract` c ON c.name = cv.contract
	WHERE c.counterparty = %(counterparty)s
		AND cv.is_current = 1
		AND c.docstatus = 1
	ORDER BY FIELD(cv.status, 'Signature Requested', 'Under Review', 'Approved', 'Draft', 'Executed', 'Expired', 'Cancelled'),
		c.modified DESC
"""


@frappe.whitelist()
def get_dashboard():
	"""Return the portal dashboard data for the logged-in counterparty.

	Counts are derived client-side from the single `contracts` list.
	"""
	counterparty = _require_counterparty()

	contracts = frappe.db.sql(
		_CONTRACT_ROW_SQL,
		{"counterparty": counterparty.name},
		as_dict=True,
	)

	return {
		"counterparty": counterparty,
		"contracts": contracts,
	}
