const { createApp, reactive, ref, computed } = Vue;

const store = reactive({
	user: null,
	counterparty: null,
	loading: false,
	error: null,
});

const api = (method, args = {}) =>
	frappe.call({
		method: `contract_management.contract_management.portal_api.${method}`,
		args,
		freeze: false,
	});

const PortalShell = {
	setup() {
		const userEmail = computed(() => store.user || "Guest");
		const counterpartyName = computed(() => store.counterparty?.counterparty_name || "");
		const logout = () => {
			window.location.href = "/logout";
		};
		return { userEmail, counterpartyName, logout, store };
	},
	template: `
		<div class="portal-shell">
			<header class="portal-header">
				<div class="portal-header-inner">
					<h1 class="portal-title">Counterparty Portal</h1>
					<div class="portal-user">
						<span class="portal-user-email">{{ counterpartyName ? counterpartyName + ' (' + userEmail + ')' : userEmail }}</span>
						<button class="btn btn-sm btn-outline-light" @click="logout">Logout</button>
					</div>
				</div>
			</header>
			<main class="portal-main">
				<div class="portal-card">
					<p class="mb-0">{{ store.user ? 'Welcome to your contract portal.' : 'Not logged in.' }}</p>
				</div>
			</main>
		</div>
	`,
};

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
				})
				.catch(() => {
					store.error = "Could not load your session.";
				});
			return { store };
		},
		template: `<portal-shell />`,
	});

	app.mount("#portal-app");
});
