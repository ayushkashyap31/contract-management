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


_USER_FULL_NAME = {}


def _user_full_name(user):
	if not user:
		return ""
	if user not in _USER_FULL_NAME:
		_USER_FULL_NAME[user] = frappe.db.get_value("User", user, "full_name") or user
	return _USER_FULL_NAME[user]


@frappe.whitelist()
def get_contract_detail(contract_name):
	"""Return everything the Contract Detail page needs for one contract.

	Dereads doctypes via raw DB access (mirroring `get_dashboard`) so the
	counterparty user is not blocked by absent desktop permission rules; the
	ownership check below is the real access control.

	Payload includes future-ready `can_review` / `can_sign` flags that the
	frontend does not render yet.
	"""
	counterparty = _require_counterparty()

	contract = frappe.db.get_value(
		"Contract",
		contract_name,
		[
			"name",
			"contract_title",
			"status",
			"effective_date",
			"expiration_date",
			"creation",
			"counterparty",
		],
		as_dict=True,
	)

	if not contract or contract.get("counterparty") != counterparty.name:
		frappe.throw(
			"You don't have access to this contract.", frappe.PermissionError
		)

	counterparty["counterparty_type"] = frappe.db.get_value(
		"Counterparty", counterparty.name, "counterparty_type"
	)
	counterparty["contact_person"] = frappe.db.get_value(
		"Counterparty", counterparty.name, "contact_person"
	)

	current_version = None
	versions = frappe.db.get_all(
		"Contract Version",
		filters={"contract": contract_name},
		fields=["name", "version_number", "status", "document", "creation"],
		order_by="version_number asc",
	)
	version_num = {v["name"]: v["version_number"] for v in versions}

	# current = is_current=1
	current_rows = frappe.db.get_all(
		"Contract Version",
		filters={"contract": contract_name, "is_current": 1},
		fields=["name", "version_number", "status", "document", "creation"],
		limit=1,
	)
	if current_rows:
		current_version = current_rows[0]
	# fall back to newest if the flag is missing
	if not current_version and versions:
		current_version = versions[-1]

	# --- approvals (all, for the narrative timeline) ---
	approvals = frappe.db.get_all(
		"Approval",
		filters={"contract": contract_name},
		fields=[
			"name",
			"approver",
			"status",
			"remarks",
			"approval_date",
			"contract_version",
		],
		order_by="creation asc",
	)

	# --- signature requests (all, plus recipients for the current version) ---
	version_names = list(version_num.keys())
	signature_requests = []
	if version_names:
		signature_requests = frappe.db.get_all(
			"Signature Request",
			filters={"contract_version": ["in", version_names]},
			fields=[
				"name",
				"contract_version",
				"status",
				"requested_by",
				"requested_on",
				"completed_on",
			],
			order_by="requested_on asc",
		)

	def _add(event_list, type_, title, at, subtitle=None, tone=""):
		if at:
			event_list.append(
				{
					"type": type_,
					"title": title,
					"subtitle": subtitle,
					"at": str(at),
					"tone": tone,
				}
			)

	timeline = []
	_add(timeline, "created", "Contract created", contract["creation"])

	for v in versions:
		vn = v["version_number"]
		status = v["status"]
		if status == "Under Review":
			_add(timeline, "review", "Sent for review", v["creation"], f"Version {vn}", "amber")
		elif status == "Draft":
			_add(timeline, "draft", f"Version {vn} drafted", v["creation"], "", "gray")
		elif status == "Executed":
			_add(timeline, "executed", "Contract executed", v["creation"], f"Version {vn}", "emerald")

	for ap in approvals:
		if ap["status"] == "Approved":
			_add(
				timeline,
				"approved",
				"Approved by " + _user_full_name(ap["approver"]),
				ap["approval_date"] or ap["creation"],
				"Review approved",
				"blue",
			)
		elif ap["status"] == "Rejected":
			_add(
				timeline,
				"rejected",
				"Review declined",
				ap["approval_date"] or ap["creation"],
				ap["remarks"],
				"red",
			)

	for sr in signature_requests:
		vn = version_num.get(sr["contract_version"])
		sub = f"Version {vn}" if vn is not None else None
		_add(timeline, "sign", "Signature requested", sr["requested_on"], sub, "indigo")
		if sr["completed_on"]:
			_add(timeline, "signed", "Signature completed", sr["completed_on"], sub, "emerald")

	timeline.sort(key=lambda e: e["at"], reverse=True)

	latest_approval = None
	if current_version:
		rows = frappe.db.get_all(
			"Approval",
			filters={"contract_version": current_version["name"]},
			fields=["name", "approver", "status", "remarks", "approval_date"],
			order_by="creation desc",
			limit=1,
		)
		if rows:
			latest_approval = rows[0]
			latest_approval["approver_name"] = _user_full_name(latest_approval["approver"])

	latest_signature = None
	if current_version:
		rows = frappe.db.get_all(
			"Signature Request",
			filters={"contract_version": current_version["name"]},
			fields=["name", "status", "requested_on", "completed_on", "requested_by"],
			order_by="requested_on desc",
			limit=1,
		)
		if rows:
			latest_signature = rows[0]
			latest_signature["recipients"] = frappe.db.get_all(
				"Signature Recipient",
				filters={"parent": latest_signature["name"]},
				fields=["signer", "email", "status", "signed_on"],
				order_by="idx asc",
			)

	can_review = bool(current_version) and current_version["status"] == "Under Review"
	can_sign = False
	if (
		current_version
		and current_version["status"] == "Signature Requested"
		and latest_signature
	):
		can_sign = latest_signature["status"] in {"Pending", "Sent", "Viewed"}

	return {
		"contract": {
			"name": contract["name"],
			"contract_title": contract["contract_title"],
			"status": contract["status"],
			"effective_date": contract["effective_date"],
			"expiration_date": contract["expiration_date"],
			"creation": contract["creation"],
		},
		"counterparty": counterparty,
		"current_version": current_version,
		"approval": latest_approval,
		"signature": latest_signature,
		"timeline": timeline,
		"last_activity": timeline[0]["at"] if timeline else None,
		"can_review": can_review,
		"can_sign": can_sign,
	}


@frappe.whitelist()
def download_document(contract_version):
	"""Stream the uploaded document for a Contract Version to the portal user.

	The document is attached to `Contract Version`, whose file permission is
	gated on the (System-Manager-only) doctype read rights, so a direct
	/private/files/ URL 403s for portal users. This whitelisted endpoint
	re-enforces counterparty ownership and streams the bytes instead.
	"""
	counterparty = _require_counterparty()

	version = frappe.db.get_value(
		"Contract Version",
		contract_version,
		["name", "contract", "document"],
		as_dict=True,
	)
	if not version or not version.document:
		frappe.throw("No document is available for this version.")

	contract_counterparty = frappe.db.get_value(
		"Contract", version.contract, "counterparty"
	)
	if contract_counterparty != counterparty.name:
		frappe.throw(
			"You don't have access to this document.", frappe.PermissionError
		)

	file_doc = frappe.db.get_value(
		"File", {"file_url": version.document}, "name"
	)
	if not file_doc:
		frappe.throw("The document file could not be found.")

	file_name = frappe.db.get_value("File", file_doc, "file_name") or version.document.rsplit("/", 1)[-1]

	frappe.response["type"] = "download"
	frappe.response["display_content_as"] = (
		"inline" if file_name.lower().endswith(".pdf") else "attachment"
	)
	frappe.response["filename"] = file_name
	frappe.response["filecontent"] = frappe.get_doc("File", file_doc).get_content()
