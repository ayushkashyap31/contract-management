frappe.query_reports["Expiring Contracts"] = {
	filters: [
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: [
				"",
				"Draft",
				"Under Review",
				"Approved",
				"Executed",
				"Expired",
				"Cancelled",
			],
		},
		{
			fieldname: "counterparty",
			label: __("Counterparty"),
			fieldtype: "Link",
			options: "Counterparty",
		},
		{
			fieldname: "expiration_date_from",
			label: __("Expiration Date From"),
			fieldtype: "Date",
		},
		{
			fieldname: "expiration_date_to",
			label: __("Expiration Date To"),
			fieldtype: "Date",
		},
	],
};
