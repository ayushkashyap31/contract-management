import frappe
from datetime import date


def execute(filters=None):
	filters = filters or {}

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
		{
			"fieldname": "approval",
			"label": "Approval",
			"fieldtype": "Link",
			"options": "Approval",
			"width": 140,
		},
		{
			"fieldname": "contract",
			"label": "Contract",
			"fieldtype": "Link",
			"options": "Contract",
			"width": 140,
		},
		{
			"fieldname": "contract_title",
			"label": "Contract Title",
			"fieldtype": "Data",
			"width": 250,
		},
		{
			"fieldname": "version",
			"label": "Version",
			"fieldtype": "Int",
			"width": 80,
		},
		{
			"fieldname": "approver",
			"label": "Approver",
			"fieldtype": "Link",
			"options": "User",
			"width": 180,
		},
		{
			"fieldname": "approval_role",
			"label": "Approval Role",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"fieldname": "requested_on",
			"label": "Requested On",
			"fieldtype": "Datetime",
			"width": 170,
		},
		{
			"fieldname": "days_pending",
			"label": "Days Pending",
			"fieldtype": "Int",
			"width": 110,
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "modified",
			"label": "Modified",
			"fieldtype": "Datetime",
			"width": 160,
		},
	]


def get_data(filters):
	conditions = []

	if filters.get("approver"):
		conditions.append("a.approver = %(approver)s")

	if filters.get("status"):
		conditions.append("a.status = %(status)s")
	else:
		conditions.append("a.status = 'Pending'")

	if filters.get("requested_date_from"):
		conditions.append("a.creation >= %(requested_date_from)s")

	if filters.get("requested_date_to"):
		conditions.append("a.creation <= %(requested_date_to)s")

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	sql = f"""
		SELECT
			a.name AS "approval",
			a.contract AS "contract",
			c.contract_title AS "contract_title",
			cv.version_number AS "version",
			a.approver AS "approver",
			collab.role AS "approval_role",
			a.creation AS "requested_on",
			a.status AS "status",
			a.modified AS "modified"
		FROM
			`tabApproval` a
		LEFT JOIN
			`tabContract` c ON c.name = a.contract
		LEFT JOIN
			`tabContract Version` cv ON cv.name = a.contract_version
		LEFT JOIN
			`tabCollaborator` collab
				ON collab.parent = a.contract
				AND collab.parentfield = 'collaborators'
				AND collab.user = a.approver
		WHERE
			{where_clause}
		ORDER BY
			a.creation ASC
	"""

	rows = frappe.db.sql(sql, filters, as_dict=True)

	today = date.today()

	for row in rows:
		if row.get("requested_on"):
			row["days_pending"] = (today - row["requested_on"].date()).days
		else:
			row["days_pending"] = None

	return rows
