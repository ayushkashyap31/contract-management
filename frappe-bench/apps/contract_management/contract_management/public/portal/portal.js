const { createApp, reactive, ref, computed } = Vue;

/* ------------------------------------------------------------------
   Store
------------------------------------------------------------------- */
const store = reactive({
	user: null,
	counterparty: null,
	contracts: [],
	phase: "loading",
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
		return { tone, dates, dotColor, icons };
	},
	template: `
		<div class="contract-row">
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

const PortalShell = {
	components: { PortalHeader, DashboardPage },
	setup() {
		return { store, loadDashboard, icons };
	},
	template: `
		<div class="portal-shell">
			<portal-header />
			<main class="portal-main">
				<div v-if="store.phase === 'loading'">
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
