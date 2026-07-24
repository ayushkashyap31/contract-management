frappe.query_reports["Pending Signature Requests"] = {
	filters: [
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: [
				"",
				"Draft",
				"Pending",
				"Sent",
				"Viewed",
				"Completed",
				"Declined",
				"Cancelled",
				"Expired",
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
