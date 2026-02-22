// /js/register.js - OwnWiki Registration Validation (EMAIL 6-60 FIX)
document.addEventListener("DOMContentLoaded", function () {
	// Form fields
	const firstnameInput = document.getElementById("firstname");
	const lastnameInput = document.getElementById("lastname");
	const usernameInput = document.getElementById("username");
	const emailInput = document.getElementById("email");
	const pwInput = document.getElementById("password");
	const pwRepeatInput = document.getElementById("password-repeat");
	const form = document.querySelector("form");

	// Error message maps
	const errorMessages = {
		firstname: {
			empty: "Vorname ist erforderlich.",
			regex: "Nur Buchstaben (inkl. Umlaute), Leerzeichen und Bindestriche erlaubt.",
			length: "Vorname muss 1-30 Zeichen lang sein."
		},
		lastname: {
			empty: "Nachname ist erforderlich.",
			regex: "Nur Buchstaben (inkl. Umlaute), Leerzeichen und Bindestriche erlaubt.",
			length: "Nachname muss 2-50 Zeichen lang sein."
		},
		username: {
			empty: "Benutzername ist erforderlich.",
			regex: "Nur Buchstaben, Zahlen und Unterstriche erlaubt.",
			length: "Benutzername muss 3-20 Zeichen lang sein."
		},
		email: {
			empty: "E-Mail-Adresse ist erforderlich.",
			length: "E-Mail muss 6-60 Zeichen lang sein.",
			invalid: "Ungültige E-Mail-Adresse."
		},
		password: {
			empty: "Passwort ist erforderlich.",
			invalid:
				"Mind. 8 Zeichen mit Groß-/Kleinbuchstaben, Zahl und Sonderzeichen (!§$%&/()=?{}[]*+~#-_;,.:^°<>|).",
			forbidden: "Verboten: ' `\""
		},
		repeat: {
			empty: "Passwortbestätigung ist erforderlich.",
			mismatch: "Passwörter stimmen nicht überein."
		}
	};

	// Regex patterns (NUR Zeichenprüfung)
	const firstnameRegex = /^[a-zA-ZÄÖÜäöüß\s\-]+$/u;
	const lastnameRegex = /^[a-zA-ZÄÖÜäöüß\s\-]+$/u;
	const usernameRegex = /^[a-zA-Z0-9_]+$/;
	const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

	// Clear error
	function clearError(input, errorEl) {
		input.classList.remove("invalid");
		input.classList.add("valid");
		errorEl.textContent = "";
		errorEl.style.display = "none";
	}

	// Show error
	function showError(input, errorEl, message) {
		input.classList.remove("valid");
		input.classList.add("invalid");
		errorEl.textContent = message;
		errorEl.style.display = "block";
	}

	// UNIVERSAL VALIDATOR
	function validateField(input, regex, minLen, maxLen, errorKey) {
		const val = input.value.trim();
		const errorEl = document.getElementById(input.id + "-error");

		clearError(input, errorEl);

		// 1. EMPTY CHECK
		if (val === "") {
			showError(input, errorEl, errorMessages[errorKey].empty);
			return false;
		}

		// 2. LENGTH CHECK (JETZT AUCH EMAIL!)
		if (val.length < minLen || val.length > maxLen) {
			const lengthMsg =
				errorMessages[errorKey].length ||
				errorMessages[errorKey].length;
			showError(input, errorEl, lengthMsg);
			return false;
		}

		// 3. REGEX CHECK
		if (regex && !regex.test(val)) {
			const regexMsg =
				errorMessages[errorKey].regex ||
				errorMessages[errorKey].invalid;
			showError(input, errorEl, regexMsg);
			return false;
		}

		return true;
	}

	// Password validation
	function validatePassword(input) {
		const val = input.value;
		const errorEl = document.getElementById("password-error");

		clearError(input, errorEl);

		if (val === "") {
			showError(input, errorEl, errorMessages.password.empty);
			return false;
		}

		// Verbotene Zeichen prüfen
		if (/['"`]/.test(val)) {
			showError(input, errorEl, errorMessages.password.forbidden);
			return false;
		}

		// Requirements
		const hasLower = /[a-z]/.test(val);
		const hasUpper = /[A-Z]/.test(val);
		const hasDigit = /\d/.test(val);
		const hasSpecial = /[!§$%&\/()=?{}\[\]*+~#\-_;,.:^°<>|]/.test(val);
		const lengthOK = val.length >= 8;

		if (!lengthOK || !hasLower || !hasUpper || !hasDigit || !hasSpecial) {
			showError(input, errorEl, errorMessages.password.invalid);
			return false;
		}
		return true;
	}

	// Password repeat
	function validatePasswordRepeat() {
		const val = pwRepeatInput.value;
		const pw1 = pwInput.value;
		const errorEl = document.getElementById("password-repeat-error");

		clearError(pwRepeatInput, errorEl);

		if (val === "") {
			showError(pwRepeatInput, errorEl, errorMessages.repeat.empty);
			return false;
		}
		if (val !== pw1) {
			showError(pwRepeatInput, errorEl, errorMessages.repeat.mismatch);
			return false;
		}
		return true;
	}

	// Event handlers
	if (firstnameInput) {
		firstnameInput.addEventListener("input", () =>
			validateField(firstnameInput, firstnameRegex, 1, 30, "firstname")
		);
	}
	if (lastnameInput) {
		lastnameInput.addEventListener("input", () =>
			validateField(lastnameInput, lastnameRegex, 2, 50, "lastname")
		);
	}
	if (usernameInput) {
		usernameInput.addEventListener("input", () =>
			validateField(usernameInput, usernameRegex, 3, 20, "username")
		);
	}
	if (emailInput) {
		emailInput.addEventListener("input", () =>
			validateField(emailInput, emailRegex, 6, 60, "email")
		);
	}
	if (pwInput) {
		pwInput.addEventListener("input", () => {
			validatePassword(pwInput);
			if (pwRepeatInput) validatePasswordRepeat();
		});
	}
	if (pwRepeatInput) {
		pwRepeatInput.addEventListener("input", validatePasswordRepeat);
	}

	// Form submit
	if (form) {
		form.addEventListener("submit", function (e) {
			let isValid = true;

			if (firstnameInput)
				isValid =
					validateField(
						firstnameInput,
						firstnameRegex,
						1,
						30,
						"firstname"
					) && isValid;
			if (lastnameInput)
				isValid =
					validateField(
						lastnameInput,
						lastnameRegex,
						2,
						50,
						"lastname"
					) && isValid;
			if (usernameInput)
				isValid =
					validateField(
						usernameInput,
						usernameRegex,
						3,
						20,
						"username"
					) && isValid;
			if (emailInput)
				isValid =
					validateField(emailInput, emailRegex, 6, 60, "email") &&
					isValid;
			if (pwInput) isValid = validatePassword(pwInput) && isValid;
			if (pwRepeatInput) isValid = validatePasswordRepeat() && isValid;

			if (!isValid) {
				e.preventDefault();
				document.querySelector(".invalid")?.focus();
			}
		});
	}
});
