// Contract Portal — Login page
// Posts to Frappe's built-in /api/method/login endpoint (no custom auth).

frappe.ready(() => {
	const form = document.getElementById("login-form");
	if (!form) return;

	const email = document.getElementById("login_email");
	const password = document.getElementById("login_password");
	const submit = document.getElementById("login-submit");
	const label = submit.querySelector(".btn-label");
	const toggle = document.getElementById("pw-toggle");
	const errorBox = document.getElementById("login-error");
	const errorText = document.getElementById("login-error-text");
	const helpLink = document.getElementById("login-help-link");

	const showError = (message) => {
		errorText.textContent = message;
		errorBox.classList.add("visible");
	};

	const clearError = () => errorBox.classList.remove("visible");

	const setLoading = (on) => {
		submit.disabled = on;
		submit.classList.toggle("loading", on);
		email.disabled = on;
		password.disabled = on;
		label.textContent = on ? "Signing you in..." : "Sign in";
	};

	const invalid = (field) => {
		field.classList.add("invalid");
		field.focus();
	};

	const friendlyError = (status, data) => {
		const raw = (data && data.message) || "";
		const lower = String(raw).toLowerCase();

		if (status === 401 || lower.includes("invalid") || lower.includes("credentials")) {
			return "That email and password combination didn't match our records. Please try again.";
		}
		if (status === 403 || lower.includes("not permitted") || lower.includes("disabled")) {
			return "Your account doesn't have access to the portal yet. Please contact your contract manager.";
		}
		if (status === 429 || lower.includes("too many") || lower.includes("rate")) {
			return "Too many sign-in attempts. Please wait a moment and try again.";
		}
		return "We couldn't sign you in right now. Please try again in a moment.";
	};

	toggle.addEventListener("click", () => {
		const show = password.type === "password";
		password.type = show ? "text" : "password";
		toggle.classList.toggle("is-visible", show);
		toggle.setAttribute("aria-label", show ? "Hide password" : "Show password");
		toggle.setAttribute("aria-pressed", String(show));
		password.focus();
	});

	[email, password].forEach((field) => {
		field.addEventListener("input", () => {
			clearError();
			field.classList.remove("invalid");
		});
	});

	helpLink.addEventListener("click", (event) => event.preventDefault());

	form.addEventListener("submit", (event) => {
		event.preventDefault();
		clearError();

		if (!email.value.trim()) {
			showError("Please enter your email address.");
			invalid(email);
			return;
		}
		if (!password.value) {
			showError("Please enter your password.");
			invalid(password);
			return;
		}

		setLoading(true);

		fetch("/api/method/login", {
			method: "POST",
			headers: {
				Accept: "application/json",
				"Content-Type": "application/x-www-form-urlencoded",
				...(frappe.csrf_token ? { "X-Frappe-CSRF-Token": frappe.csrf_token } : {}),
			},
			body: new URLSearchParams({
				cmd: "login",
				usr: email.value.trim(),
				pwd: password.value,
			}),
		})
			.then(async (response) => {
				let data = {};
				try {
					data = await response.json();
				} catch (e) {
					/* non-JSON response */
				}
				if (response.ok) {
					window.location.href = "/portal";
					return;
				}
				throw { status: response.status, data };
			})
			.catch((error) => {
				setLoading(false);
				showError(friendlyError(error.status, error.data));
				password.value = "";
				password.focus();
			});
	});
});
