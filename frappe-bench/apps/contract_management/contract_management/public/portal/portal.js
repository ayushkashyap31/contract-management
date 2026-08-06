const { createApp, reactive, ref, computed, watch } = Vue;

/* ------------------------------------------------------------------
   Store
------------------------------------------------------------------- */
const store = reactive({
	user: null,
	counterparty: null,
	contracts: [],
	phase: "loading",
	route: { view: "dashboard" },
});

const api = (method, args = {}) =>
	frappe.call({
		method: `contract_management.contract_management.portal_api.${method}`,
		args,
		freeze: false,
	});

/* ------------------------------------------------------------------
   Helpers
------------------------------------------------------------------- */
const STATUS_TONE = {
	"Under Review": "tone-amber",
	"Signature Requested": "tone-indigo",
	Approved: "tone-blue",
	Executed: "tone-emerald",
	Draft: "tone-gray",
	Rejected: "tone-red",
	Cancelled: "tone-red",
	Expired: "tone-gray",
	Superseded: "tone-gray",
	Pending: "tone-amber",
	Sent: "tone-indigo",
	Viewed: "tone-indigo",
	Completed: "tone-emerald",
	Declined: "tone-red",
};

const DOT_COLOR = {
	"tone-amber": "#f59e0b",
	"tone-indigo": "#6366f1",
	"tone-blue": "#3b82f6",
	"tone-emerald": "#10b981",
	"tone-red": "#ef4444",
	"tone-gray": "#9ca3af",
};

const icons = {
	brand: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>`,
	eye: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`,
	pen: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>`,
	check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg>`,
	chevron: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>`,
	logout: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>`,
	empty: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>`,
	alert: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
	back: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>`,
	file: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>`,
	calendar: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
	user: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 0 0-16 0"/></svg>`,
	activity: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
	external: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`,
	clock: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
	users: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
};

function fmtDate(d) {
	if (!d) return "";
	const dt = new Date(String(d).length === 10 ? `${d}T00:00:00` : d);
	if (isNaN(dt.getTime())) return d;
	return dt.toLocaleDateString("en-US", {
		month: "short",
		day: "numeric",
		year: "numeric",
	});
}

function fmtDateTime(d) {
	if (!d) return "";
	const dt = new Date(String(d).length === 10 ? `${d}T00:00:00` : d);
	if (isNaN(dt.getTime())) return d;
	return dt.toLocaleString("en-US", {
		month: "short",
		day: "numeric",
		hour: "numeric",
		minute: "2-digit",
	});
}

function timeAgo(d) {
	if (!d) return "";
	const dt = new Date(String(d).length === 10 ? `${d}T00:00:00` : d);
	if (isNaN(dt.getTime())) return "";
	const seconds = Math.floor((Date.now() - dt.getTime()) / 1000);
	if (seconds < 45) return "Just now";
	const minutes = Math.floor(seconds / 60);
	if (minutes < 60) return `${minutes}m ago`;
	const hours = Math.floor(minutes / 60);
	if (hours < 24) return `${hours}h ago`;
	const days = Math.floor(hours / 24);
	if (days < 7) return `${days}d ago`;
	return fmtDate(d);
}

function recipientTone(status) {
	const s = (status || "").toUpperCase();
	if (s === "SIGNED") return "tone-emerald";
	if (s === "DECLINED") return "tone-red";
	if (s === "VIEWED") return "tone-indigo";
	return "tone-gray";
}

function openDetail(contract) {
	store.route = { view: "detail", contract: contract.name };
	history.pushState({ portal: "detail", contract: contract.name }, "");
}

function goBack() {
	if (history.state && history.state.portal === "detail") {
		history.back();
	} else {
		store.route = { view: "dashboard" };
	}
}

window.addEventListener("popstate", (e) => {
	store.route =
		e.state && e.state.portal === "detail" && e.state.contract
			? { view: "detail", contract: e.state.contract }
			: { view: "dashboard" };
});

function initials(name) {
	if (!name) return "?";
	const parts = name.trim().split(/\s+/);
	const first = parts[0] ? parts[0][0] : "";
	const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
	return (first + last).toUpperCase();
}

function loadDashboard() {
	store.phase = "loading";
	api("get_dashboard")
		.then((r) => {
			if (r.message && Array.isArray(r.message.contracts)) {
				store.contracts = r.message.contracts;
				store.phase = "ready";
			} else {
				store.phase = "error";
			}
		})
		.catch(() => {
			store.phase = "error";
		});
}

function refreshDashboard() {
	api("get_dashboard")
		.then((r) => {
			if (r.message && Array.isArray(r.message.contracts)) {
				store.contracts = r.message.contracts;
			}
		})
		.catch(() => {
			/* keep the last known list on a silent refresh failure */
		});
}

/* ------------------------------------------------------------------
   Components
------------------------------------------------------------------- */
const StatusBadge = {
	props: ["status"],
	setup(props) {
		return { tone: STATUS_TONE[props.status] || "tone-gray" };
	},
	template: `
		<span class="badge" :class="tone">
			<span class="badge-dot"></span>{{ status }}
		</span>
	`,
};

const StatCard = {
	props: ["label", "count", "helper", "tone", "icon"],
	template: `
		<div class="stat-card">
			<div class="stat-top">
				<span class="stat-icon" :class="tone" v-html="icon"></span>
				<span class="stat-label">{{ label }}</span>
			</div>
			<div class="stat-count">{{ count }}</div>
			<div class="stat-helper">{{ helper }}</div>
		</div>
	`,
};

const ContractRow = {
	components: { StatusBadge },
	props: ["contract"],
	setup(props) {
		const tone = computed(
			() => STATUS_TONE[props.contract.version_status] || "tone-gray"
		);
		const dates = computed(() => {
			const eff = fmtDate(props.contract.effective_date);
			const exp = fmtDate(props.contract.expiration_date);
			if (eff && exp) return `${eff}<span class="date-sep">→</span>${exp}`;
			if (eff) return `Effective ${eff}`;
			if (exp) return `Until ${exp}`;
			return "";
		});
		const dotColor = computed(() => DOT_COLOR[tone.value]);
		return { tone, dates, dotColor, icons, openDetail };
	},
	template: `
		<div class="contract-row" role="button" tabindex="0"
			@click="openDetail(contract)" @keydown.enter="openDetail(contract)" @keydown.space.prevent="openDetail(contract)">
			<div class="row-main">
				<span class="status-dot" :style="{ backgroundColor: dotColor }"></span>
				<div class="row-main-text">
					<div class="row-title">{{ contract.contract_title }}</div>
					<div class="row-meta">{{ contract.name }} · v{{ contract.version_number }}</div>
				</div>
			</div>
			<status-badge :status="contract.version_status" />
			<div class="row-dates" v-html="dates"></div>
			<span class="row-chevron" v-html="icons.chevron"></span>
		</div>
	`,
};

const ContractList = {
	components: { ContractRow },
	setup() {
		const filter = ref("all");
		const total = computed(() => store.contracts.length);
		const filtered = computed(() => {
			const c = store.contracts;
			if (filter.value === "action") {
				return c.filter(
					(x) =>
						x.version_status === "Under Review" ||
						x.version_status === "Signature Requested"
				);
			}
			if (filter.value === "executed") {
				return c.filter((x) => x.version_status === "Executed");
			}
			return c;
		});
		return { store, filter, total, filtered, icons };
	},
	template: `
		<section class="list-section">
			<div class="list-head">
				<h2 class="list-title">Your Contracts<span class="list-count">{{ total }}</span></h2>
				<div class="segmented">
					<button :class="{ active: filter === 'all' }" @click="filter = 'all'">All</button>
					<button :class="{ active: filter === 'action' }" @click="filter = 'action'">Needs Action</button>
					<button :class="{ active: filter === 'executed' }" @click="filter = 'executed'">Executed</button>
				</div>
			</div>
			<div class="contract-list" v-if="filtered.length">
				<contract-row v-for="c in filtered" :key="c.name" :contract="c" />
			</div>
			<div class="empty-state" v-else>
				<span class="empty-icon" v-html="icons.empty"></span>
				<p class="empty-title">Nothing here yet</p>
				<p class="empty-sub">{{ total ? 'No contracts match this filter.' : 'Contracts shared with you will appear here.' }}</p>
			</div>
		</section>
	`,
};

const DashboardPage = {
	components: { StatCard, ContractList },
	setup() {
		const greetingName = computed(() =>
			store.counterparty?.counterparty_name
				? `, ${store.counterparty.counterparty_name}`
				: ""
		);
		const counts = computed(() => {
			const c = store.contracts;
			return {
				pendingReview: c.filter((x) => x.version_status === "Under Review").length,
				pendingSignature: c.filter(
					(x) => x.version_status === "Signature Requested"
				).length,
				executed: c.filter((x) => x.version_status === "Executed").length,
			};
		});
		return { greetingName, counts, icons };
	},
	template: `
		<div>
			<section class="greeting">
				<h1 class="greeting-title">Welcome back{{ greetingName }}.</h1>
				<p class="greeting-sub">Here's an overview of your contracts.</p>
			</section>
			<section class="stats-grid">
				<stat-card label="Pending Review" :count="counts.pendingReview"
					helper="Awaiting your review" tone="tone-amber" :icon="icons.eye" />
				<stat-card label="Pending Signature" :count="counts.pendingSignature"
					helper="Awaiting your signature" tone="tone-indigo" :icon="icons.pen" />
				<stat-card class="executed" label="Executed" :count="counts.executed"
					helper="Signed &amp; in effect" tone="tone-emerald" :icon="icons.check" />
			</section>
			<contract-list />
		</div>
	`,
};

const PortalHeader = {
	setup() {
		const displayName = computed(
			() => store.counterparty?.counterparty_name || store.user || ""
		);
		const userInitials = computed(() => initials(displayName.value));
		const logout = () => {
			window.location.href = "/logout";
		};
		return { displayName, userInitials, logout, icons };
	},
	template: `
		<header class="portal-header">
			<div class="portal-header-inner">
				<div class="brand">
					<span class="brand-mark" v-html="icons.brand"></span>
					<span class="brand-name">Counterparty Portal</span>
				</div>
				<div class="portal-user">
					<span class="user-avatar">{{ userInitials }}</span>
					<span class="user-name">{{ displayName }}</span>
					<button class="logout-btn" @click="logout">
						Logout <span v-html="icons.logout"></span>
					</button>
				</div>
			</div>
		</header>
	`,
};

const ContractSummary = {
	components: { StatusBadge },
	props: ["version", "lastActivity"],
	setup() {
		return { timeAgo, fmtDateTime };
	},
	template: `
		<div class="summary-strip">
			<div class="summary-cell">
				<span class="summary-label">Current Status</span>
				<status-badge :status="version.status" />
			</div>
			<div class="summary-cell">
				<span class="summary-label">Current Version</span>
				<span class="summary-value">Version {{ version.version_number }}</span>
			</div>
			<div class="summary-cell">
				<span class="summary-label">Last Activity</span>
				<span class="summary-value" :title="fmtDateTime(lastActivity)">{{ timeAgo(lastActivity) || "—" }}</span>
			</div>
		</div>
	`,
};

const OverviewCard = {
	props: ["data"],
	setup() {
		return { icons, fmtDate };
	},
	template: `
		<section class="detail-card">
			<div class="detail-card-head">
				<span class="detail-card-icon tone-blue" v-html="icons.file"></span>
				<div>
					<h3 class="detail-card-title">Overview</h3>
					<p class="detail-card-sub">Key details of this contract</p>
				</div>
			</div>
			<div class="detail-meta-grid">
				<div class="detail-value">
					<span class="detail-value-label">Counterparty</span>
					<span class="detail-value-text">{{ data.counterparty.counterparty_name }}</span>
				</div>
				<div class="detail-value">
					<span class="detail-value-label">Effective date</span>
					<span class="detail-value-text">{{ fmtDate(data.contract.effective_date) || "—" }}</span>
				</div>
				<div class="detail-value">
					<span class="detail-value-label">Expiration date</span>
					<span class="detail-value-text">{{ fmtDate(data.contract.expiration_date) || "—" }}</span>
				</div>
				<div class="detail-value">
					<span class="detail-value-label">Created</span>
					<span class="detail-value-text">{{ fmtDate(data.contract.creation) }}</span>
				</div>
			</div>
		</section>
	`,
};

const DocumentCard = {
	props: ["version"],
	setup(props) {
		const fileName = computed(() => {
			const doc = props.version.document;
			return doc ? String(doc).split("/").pop() : "";
		});
		const docUrl = computed(
			() =>
				`/api/method/contract_management.contract_management.portal_api.download_document?contract_version=${encodeURIComponent(props.version.name)}`
		);
		return { fileName, docUrl, icons };
	},
	template: `
		<section class="detail-card document-card">
			<div class="document-visual" v-html="icons.file"></div>
			<div class="document-body" v-if="version.document">
				<span class="document-eyebrow">Version {{ version.version_number }} · {{ fileName }}</span>
				<h3 class="detail-card-title">Contract Document</h3>
				<p class="document-sub">This is the working version of the agreement shared with you.</p>
			</div>
			<div class="document-body" v-else>
				<span class="document-eyebrow">Version {{ version.version_number }}</span>
				<h3 class="detail-card-title">No document yet</h3>
				<p class="document-sub">No document has been uploaded for this version.</p>
			</div>
			<div class="document-actions">
				<a class="primary-btn" v-if="version.document" :href="docUrl" target="_blank" rel="noopener">
					View document <span v-html="icons.external"></span>
				</a>
			</div>
		</section>
	`,
};

const ApprovalCard = {
	components: { StatusBadge },
	props: {
		approval: { type: Object, default: null },
		contractName: { type: String, default: "" },
		canReview: { type: Boolean, default: false },
	},
	emits: ["done"],
	setup(props, { emit }) {
		const decision = reactive({ remarks: "", busy: false, error: "", done: null });

		const submit = (action) => {
			if (decision.busy) return;
			decision.busy = true;
			decision.error = "";
			api("review_contract", {
				contract_name: props.contractName,
				action,
				remarks: decision.remarks,
			})
				.then((r) => {
					decision.done = action;
					decision.busy = false;
					// Let the success confirmation render, then refresh the
					// panel with the server-confirmed state.
					setTimeout(() => emit("done", action), 1400);
				})
				.catch((e) => {
					decision.busy = false;
					decision.error =
						e && e.message ? e.message : "Could not submit your decision. Please try again.";
				});
		};

		return { decision, submit, icons, fmtDateTime };
	},
	template: `
		<section class="detail-card side-card">
			<div class="detail-card-head">
				<span class="detail-card-icon tone-amber" v-html="icons.eye"></span>
				<div class="head-flex">
					<h3 class="detail-card-title">Approval</h3>
					<status-badge v-if="approval" :status="approval.status" />
				</div>
			</div>

			<template v-if="approval">
				<div class="side-rows">
					<div class="side-row">
						<span class="side-label">Reviewer</span>
						<span class="side-value">{{ approval.approver_name }}</span>
					</div>
					<div class="side-row" v-if="approval.status !== 'Pending'">
						<span class="side-label">Decided</span>
						<span class="side-value">{{ approval.approval_date ? fmtDateTime(approval.approval_date) : '—' }}</span>
					</div>
				</div>
				<p class="card-footnote" v-if="approval.remarks">{{ approval.remarks }}</p>
			</template>
			<p class="card-empty" v-else>No review has been requested for this version.</p>

			<div class="approval-success" v-if="decision.done">
				<span class="success-icon" v-html="icons.check"></span>
				<span>{{ decision.done === 'approve' ? 'Contract approved' : 'Contract rejected' }}</span>
			</div>

			<div class="approval-panel" v-else-if="canReview && approval && approval.status === 'Pending'">
				<label class="approval-label" for="approval-remarks">Remarks</label>
				<textarea id="approval-remarks" class="remarks-input" rows="3"
					v-model="decision.remarks"
					:disabled="decision.busy"
					placeholder="Add a note for the reviewer…"></textarea>
				<p class="approval-error" v-if="decision.error">{{ decision.error }}</p>
				<div class="approval-actions">
					<button class="reject-btn" :disabled="decision.busy" @click="submit('reject')">
						{{ decision.busy ? 'Submitting…' : 'Reject' }}
					</button>
					<button class="primary-btn approve-btn" :disabled="decision.busy" @click="submit('approve')">
						{{ decision.busy ? 'Submitting…' : 'Approve' }}
					</button>
				</div>
			</div>
		</section>
	`,
};

const SignatureCard = {
	components: { StatusBadge },
	props: ["signature"],
	setup() {
		return { icons, fmtDateTime, recipientTone };
	},
	template: `
		<section class="detail-card side-card">
			<div class="detail-card-head">
				<span class="detail-card-icon tone-indigo" v-html="icons.pen"></span>
				<div class="head-flex">
					<h3 class="detail-card-title">Signature</h3>
					<status-badge v-if="signature" :status="signature.status" />
				</div>
			</div>
			<template v-if="signature">
				<div class="side-rows">
					<div class="side-row">
						<span class="side-label">Requested</span>
						<span class="side-value">{{ fmtDateTime(signature.requested_on) }}</span>
					</div>
					<div class="side-row" v-if="signature.completed_on">
						<span class="side-label">Completed</span>
						<span class="side-value">{{ fmtDateTime(signature.completed_on) }}</span>
					</div>
				</div>
				<div class="recipient-head">
					<span v-html="icons.users"></span>
					Recipients
				</div>
				<div class="recipient-list">
					<span v-for="r in signature.recipients" :key="r.email" class="recipient-chip" :class="recipientTone(r.status)">
						<span class="recipient-dot"></span>
						<span class="recipient-email">{{ r.email }}</span>
						<span class="recipient-status">{{ r.status }}</span>
					</span>
				</div>
			</template>
			<p class="card-empty" v-else>No signature has been requested for this version.</p>
		</section>
	`,
};

const ActivityTimeline = {
	props: ["timeline"],
	setup() {
		const dotFor = (tone) => DOT_COLOR[tone] || "#9ca3af";
		return { icons, fmtDateTime, dotFor };
	},
	template: `
		<section class="timeline-card">
			<div class="detail-card-head">
				<span class="detail-card-icon tone-gray" v-html="icons.activity"></span>
				<div>
					<h3 class="detail-card-title">Activity</h3>
					<p class="detail-card-sub">What's been happening with this contract</p>
				</div>
			</div>
			<ol class="timeline" v-if="timeline.length">
				<li v-for="(e, i) in timeline" :key="i" class="timeline-item">
					<span class="timeline-dot" :style="{ backgroundColor: dotFor(e.tone) }"></span>
					<div class="timeline-body">
						<div class="timeline-title">{{ e.title }}</div>
						<div class="timeline-sub" v-if="e.subtitle">{{ e.subtitle }}</div>
					</div>
					<div class="timeline-at">{{ fmtDateTime(e.at) }}</div>
				</li>
			</ol>
			<p class="card-empty" v-else>No activity recorded yet.</p>
		</section>
	`,
};

const ContractDetailPage = {
	components: {
		StatusBadge,
		ContractSummary,
		OverviewCard,
		DocumentCard,
		ApprovalCard,
		SignatureCard,
		ActivityTimeline,
	},
	props: ["contractName"],
	setup(props) {
		const state = reactive({ phase: "loading", data: null });

		const load = () => {
			state.phase = "loading";
			state.data = null;
			api("get_contract_detail", { contract_name: props.contractName })
				.then((r) => {
					if (r.message) {
						state.data = r.message;
						state.phase = "ready";
					} else {
						state.phase = "error";
					}
				})
				.catch(() => {
					state.phase = "error";
				});
		};

		load();

		return { state, load, goBack, icons };
	},
	template: `
		<div class="detail-page">
			<button class="back-link" @click="goBack">
				<span v-html="icons.back"></span> Back to contracts
			</button>

			<div v-if="state.phase === 'loading'" class="detail-loading">
				<div class="skeleton skeleton-heading"></div>
				<div class="skeleton skeleton-summary"></div>
				<div class="skeleton skeleton-card" v-for="i in 2" :key="i"></div>
			</div>

			<div class="error-state" v-else-if="state.phase === 'error'">
				<span class="error-icon" v-html="icons.alert"></span>
				<p class="error-title">Couldn't load this contract</p>
				<p class="error-sub">Something went wrong. Please try again.</p>
				<button class="retry-btn" @click="load">Retry</button>
			</div>

			<template v-else-if="state.data">
				<header class="detail-header">
					<div class="detail-heading">
						<h1 class="detail-title">{{ state.data.contract.contract_title }}</h1>
						<div class="detail-metas">
							<span class="detail-meta">{{ state.data.contract.name }}</span>
							<span class="detail-meta">Version {{ state.data.current_version.version_number }}</span>
						</div>
					</div>
					<status-badge :status="state.data.current_version.status" />
				</header>

				<contract-summary :version="state.data.current_version" :last-activity="state.data.last_activity" />

				<div class="detail-columns">
					<div class="detail-main">
						<overview-card :data="state.data" />
						<document-card :version="state.data.current_version" />
					</div>
					<aside class="detail-aside">
						<approval-card
							:approval="state.data.approval"
							:contract-name="state.data.contract.name"
							:can-review="state.data.can_review"
							@done="load" />
						<signature-card :signature="state.data.signature" />
					</aside>
				</div>

				<activity-timeline :timeline="state.data.timeline" />
			</template>
		</div>
	`,
};

const PortalShell = {
	components: { PortalHeader, DashboardPage, ContractDetailPage },
	setup() {
		watch(
			() => store.route.view,
			(view) => {
				if (view === "dashboard" && store.phase === "ready") {
					refreshDashboard();
				}
			}
		);
		return { store, loadDashboard, icons };
	},
	template: `
		<div class="portal-shell">
			<portal-header />
			<main class="portal-main">
				<contract-detail-page
					v-if="store.route.view === 'detail'"
					:contract-name="store.route.contract" />
				<div v-else-if="store.phase === 'loading'">
					<div class="stats-grid">
						<div class="skeleton stat-card"></div>
						<div class="skeleton stat-card"></div>
						<div class="skeleton stat-card"></div>
					</div>
					<div class="skeleton contract-row"></div>
					<div class="skeleton contract-row" style="margin-top: 0.625rem;"></div>
					<div class="skeleton contract-row last" style="margin-top: 0.625rem;"></div>
				</div>
				<div class="error-state" v-else-if="store.phase === 'error'">
					<span class="error-icon" v-html="icons.alert"></span>
					<p class="error-title">Couldn't load your contracts</p>
					<p class="error-sub">Something went wrong. Please try again.</p>
					<button class="retry-btn" @click="loadDashboard">Retry</button>
				</div>
				<dashboard-page v-else />
			</main>
		</div>
	`,
};

/* ------------------------------------------------------------------
   Bootstrap
------------------------------------------------------------------- */
frappe.ready(() => {
	const app = createApp({
		components: { PortalShell },
		setup() {
			api("get_session_info")
				.then((r) => {
					if (r.message) {
						store.user = r.message.user;
						store.counterparty = r.message.counterparty;
					}
					loadDashboard();
				})
				.catch(() => {
					store.phase = "error";
				});
			return { store };
		},
		template: `<portal-shell />`,
	});

	app.mount("#portal-app");
});
