frappe.query_reports["Pending Approvals"] = {
	filters: [
		{
			fieldname: "approver",
			label: __("Approver"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: [
				"",
				"Pending",
				"Approved",
				"Rejected",
			],
		},
		{
			fieldname: "requested_date_from",
			label: __("Requested Date From"),
			fieldtype: "Date",
		},
		{
			fieldname: "requested_date_to",
			label: __("Requested Date To"),
			fieldtype: "Date",
		},
	],
};
