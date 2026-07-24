frappe.query_reports["Contract Summary"] = {
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
			fieldname: "effective_date_from",
			label: __("Effective Date From"),
			fieldtype: "Date",
		},
		{
			fieldname: "effective_date_to",
			label: __("Effective Date To"),
			fieldtype: "Date",
		},
	],
};
