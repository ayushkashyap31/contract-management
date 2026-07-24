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
			"fieldname": "signature_request",
			"label": "Signature Request",
			"fieldtype": "Link",
			"options": "Signature Request",
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
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Data",
			"width": 130,
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
			"fieldname": "modified",
			"label": "Modified",
			"fieldtype": "Datetime",
			"width": 160,
		},
	]


def get_data(filters):
	conditions = []

	if filters.get("status"):
		conditions.append("sr.status = %(status)s")
	else:
		conditions.append("sr.status IN ('Pending', 'Sent', 'Viewed')")

	if filters.get("requested_date_from"):
		conditions.append("sr.requested_on >= %(requested_date_from)s")

	if filters.get("requested_date_to"):
		conditions.append("sr.requested_on <= %(requested_date_to)s")

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	sql = f"""
		SELECT
			sr.name AS "signature_request",
			c.name AS "contract",
			c.contract_title AS "contract_title",
			cv.version_number AS "version",
			sr.status AS "status",
			sr.requested_on AS "requested_on",
			sr.modified AS "modified"
		FROM
			`tabSignature Request` sr
		LEFT JOIN
			`tabContract Version` cv ON cv.name = sr.contract_version
		LEFT JOIN
			`tabContract` c ON c.name = cv.contract
		WHERE
			{where_clause}
		ORDER BY
			sr.requested_on ASC
	"""

	rows = frappe.db.sql(sql, filters, as_dict=True)

	today = date.today()

	for row in rows:
		if row.get("requested_on"):
			row["days_pending"] = (today - row["requested_on"].date()).days
		else:
			row["days_pending"] = None

	return rows
