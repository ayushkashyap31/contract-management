import frappe


def execute(filters=None):
	filters = filters or {}

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
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
			"fieldname": "counterparty",
			"label": "Counterparty",
			"fieldtype": "Link",
			"options": "Counterparty",
			"width": 180,
		},
		{
			"fieldname": "current_version",
			"label": "Current Version",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "effective_date",
			"label": "Effective Date",
			"fieldtype": "Date",
			"width": 130,
		},
		{
			"fieldname": "expiration_date",
			"label": "Expiration Date",
			"fieldtype": "Date",
			"width": 130,
		},
		{
			"fieldname": "owner",
			"label": "Owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 180,
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
		conditions.append("c.status = %(status)s")

	if filters.get("counterparty"):
		conditions.append("c.counterparty = %(counterparty)s")

	if filters.get("effective_date_from"):
		conditions.append("c.effective_date >= %(effective_date_from)s")

	if filters.get("effective_date_to"):
		conditions.append("c.effective_date <= %(effective_date_to)s")

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	sql = f"""
		SELECT
			c.name AS "contract",
			c.contract_title AS "contract_title",
			c.counterparty AS "counterparty",
			cv.version_number AS "current_version",
			c.status AS "status",
			c.effective_date AS "effective_date",
			c.expiration_date AS "expiration_date",
			c.owner AS "owner",
			c.modified AS "modified"
		FROM
			`tabContract` c
		LEFT JOIN
			`tabCounterparty` cp ON cp.name = c.counterparty
		LEFT JOIN
			`tabContract Version` cv ON cv.contract = c.name AND cv.is_current = 1
		WHERE
			{where_clause}
		ORDER BY
			c.modified DESC
	"""

	return frappe.db.sql(sql, filters, as_dict=True)
