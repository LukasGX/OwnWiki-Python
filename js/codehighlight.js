function openModal(text, showCloseBtn = true) {
	const modal = document.createElement("div");
	modal.classList.add("modal");

	const modalC = document.createElement("div");
	modalC.classList.add("modal-content");
	modalC.innerHTML = text;

	const close = document.createElement("i");
	close.classList.add("fas", "fa-xmark", "close");
	close.onclick = function () {
		this.parentElement.parentElement.remove();
	};

	if (showCloseBtn) modalC.appendChild(close);
	modal.appendChild(modalC);
	document.body.appendChild(modal);
}

function openWordlistModal(words) {
	let wordsReadable = "";
	words.forEach((word) => {
		wordsReadable += `<li>${word}</li>`;
	});

	openModal(`
	<h2>Wortliste</h2>
	<ul>
		${wordsReadable}
	</ul>
	`);
}

async function editRule(rule, isNew = false) {
	var data;

	const types = {
		"diff-length": "diff-length",
		wordlist: "wordlist",
		"capital-ratio": "capital-ratio",
		"repeat-word": "repeat-word"
	};
	const checks = { gt: ">=", lt: "<=", tf: "schlägt an" };
	const actions = { block: "Blockieren", warn: "Warnen" };

	// fetch rule data
	if (!isNew) {
		const response = await fetch("backend/autoCheckRuleGet.php", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ "rule-id": rule })
		});
		data = await response.json();
	} else {
		// default settings
		data = {
			enabled: true,
			pattern: { type: "diff-length", check: "gt", threshold: "" },
			action: { type: "block" }
		};
	}
	openModal(`
	<h2>Regel ${isNew == true ? "erstellen" : "bearbeiten"}</h2>
	${isNew == true ? "" : `<input type='hidden' name='rule-id' value='${rule}'>`}
	<input type='checkbox' name='rule-active' id='checkbox-rule-active' value='true' ${
		data.enabled === true ? "checked" : ""
	}> Aktiviert<br><br>
	${
		isNew == true
			? "<input type='text' name='rule-id' placeholder='Regel-ID'>"
			: ""
	}
	<input type='text' name='rule-name' id='input-rule-name' placeholder='Regel-Name' value='${
		data.name ?? ""
	}'>
	<select name='pattern-type' id='select-pattern-type'>
		${Object.keys(types)
			.map((t) =>
				t == (data.pattern && data.pattern.type)
					? `<option value='${t}' selected>${types[t]}</option>`
					: `<option value='${t}'>${types[t]}</option>`
			)
			.join("")}
	</select>
	<select name='pattern-check' id='select-pattern-check'>
		${Object.keys(checks)
			.map((c) =>
				c == (data.pattern && data.pattern.check)
					? `<option value='${c}' selected>${checks[c]}</option>`
					: `<option value='${c}'>${checks[c]}</option>`
			)
			.join("")}
	</select>
	<input type='text' name='pattern-threshold' id='input-pattern-threshold' placeholder='Schwellwert' value='${
		data.pattern.threshold ?? ""
	}'>
	<input type='text' name='pattern-wordlist' id='input-pattern-wordlist' placeholder='Wortliste' style='display: none;'>
	<p>Konsequenz</p>
	<select name='action-type' id='select-action-type'>
		${Object.keys(actions)
			.map((a) =>
				a == data.action.type
					? `<option value='${a}' selected>${actions[a]}</option>`
					: `<option value='${a}'>${actions[a]}</option>`
			)
			.join("")}
	</select>
	<input type='text' name='action-message' id='input-action-message' placeholder='Nachricht' value='${
		data.action.message ?? ""
	}' style='display: none;'>
	<button id='send' class='full'>Speichern</button>
	`);

	sel2();

	$("#select-pattern-type").on("change", function (e) {
		const value = $(this).val();
		if (value == "wordlist") {
			$("#input-pattern-wordlist").show();
			$("#select-pattern-check").val("tf").trigger("change");
		} else $("#input-pattern-wordlist").hide();
	});

	$("#select-pattern-check").on("change", function (e) {
		const value = $(this).val();
		if (value == "tf") $("#input-pattern-threshold").hide();
		else $("#input-pattern-threshold").show();
	});

	$("#select-action-type").on("change", function (e) {
		const value = $(this).val();
		if (value == "warn") $("#input-action-message").show();
		else $("#input-action-message").hide();
	});

	$("#select-pattern-type").trigger("change");
	$("#select-action-type").trigger("change");

	$("#send").on("click", async function () {
		const type = $("#select-pattern-type").val();
		const check = $("#select-pattern-check").val();
		const threshold = $("#input-pattern-threshold").val();
		let words = $("#input-pattern-wordlist")
			.val()
			.split(",")
			.map((w) => w.trim());
		words = words.filter((w) => w.length > 0);
		if (type == "wordlist" && words.length == 0) {
			alert("Bitte mindestens ein Wort in die Wortliste einfügen.");
			return;
		}
		if (
			(type == "diff-length" || type == "capital-ratio") &&
			(isNaN(threshold) || threshold.length == 0)
		) {
			alert("Bitte einen gültigen Schwellwert eingeben.");
			return;
		}
		if (
			type == "repeat-word" &&
			(isNaN(threshold) ||
				threshold.length == 0 ||
				parseInt(threshold) < 2)
		) {
			alert("Bitte einen gültigen Schwellwert (mindestens 2) eingeben.");
			return;
		}
		const ruleID = $("input[name='rule-id']").val();
		var response;
		if (!isNew) {
			response = await fetch("backend/autoCheckRuleEdit.php", {
				method: "POST",
				headers: {
					"Content-Type": "application/json"
				},
				body: JSON.stringify({
					"rule-id": ruleID,
					"rule-name": $("#input-rule-name").val(),
					"rule-active": $("#checkbox-rule-active").is(":checked")
						? "true"
						: "false",
					"pattern-type": type,
					"pattern-check": check,
					"pattern-threshold": threshold,
					"pattern-words": words,
					"action-type": $("#select-action-type").val(),
					"action-message": $("#input-action-message").val()
				})
			});
		} else {
			response = await fetch("backend/autoCheckRuleNew.php", {
				method: "POST",
				headers: {
					"Content-Type": "application/json"
				},
				body: JSON.stringify({
					"rule-id": ruleID,
					"rule-name": $("#input-rule-name").val(),
					"rule-active": $("#checkbox-rule-active").is(":checked")
						? "true"
						: "false",
					"pattern-type": type,
					"pattern-check": check,
					"pattern-threshold": threshold,
					"pattern-words": words,
					"action-type": $("#select-action-type").val(),
					"action-message": $("#input-action-message").val()
				})
			});
		}
		const data = await response.json();
		if (data.success) {
			window.location.reload();
		} else if (data.error) {
			alert(`Fehler: ${data.error}`);
		}
	});
}

function deleteRule(rule) {
	openModal(
		`
	<h2>Regel löschen</h2>
	<p>Möchten Sie die Regel wirklich löschen? Das kann nicht rückgängig gemacht werden!</p>
	<button id='confirmDelete' class='full extDeleteButton'>Löschen</button>
	<button id='cancelDelete' class='full cancelButton'>Abbrechen</button>
	`,
		false
	);

	$("#cancelDelete").on("click", function () {
		$(".modal").remove();
	});

	$("#confirmDelete").on("click", async function () {
		fetch("backend/autoCheckRuleDelete.php", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ "rule-id": rule })
		}).then((response) => {
			if (response.ok) {
				window.location.reload();
			} else {
				alert("Fehler beim Löschen der Regel.");
			}
		});
	});
}

const textareaElement = document.querySelector(".code");
const previewButton = document.querySelector(".preview-button");
const previewOutput = document.querySelector(".code-preview");
const saveButton = document.querySelector(".save-button");

if (previewButton) {
	previewButton.addEventListener("click", async function () {
		previewOutput.innerHTML = "<p>Loading...</p>";

		const codeContent = textareaElement.value;

		const response = await fetch("backend/renderAPI.php", {
			method: "POST",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify({ text: codeContent })
		});
		const data = await response.json();

		previewOutput.innerHTML = "";

		if (data.error) {
			previewOutput.innerHTML = `<p class="error">ERROR: ${data.error}</p>`;
			return;
		}

		if (data.success) {
			previewOutput.innerHTML = data.success;
		}
	});
}

if (saveButton) {
	saveButton.addEventListener("click", async function () {
		const urlParams = new URLSearchParams(window.location.search);
		const titleFromGet = urlParams.get("t") || "";
		const filename = urlParams.get("f") || "";

		const codeContent = textareaElement.value;

		let response;

		if (filename.endsWith("create")) {
			response = await fetch("backend/saveAPI.php", {
				method: "POST",
				headers: {
					"Content-Type": "application/json"
				},
				body: JSON.stringify({
					text: codeContent,
					title: titleFromGet
				})
			});
		} else if (filename.endsWith("edit")) {
			response = await fetch("backend/editAPI.php", {
				method: "POST",
				headers: {
					"Content-Type": "application/json"
				},
				body: JSON.stringify({
					text: codeContent,
					title: titleFromGet
				})
			});
		} else {
			console.error(`${filename} doesn't match any!`);
			return;
		}

		const data = await response.json();
		if (data.success) {
			window.location.href = `?f=${encodeURIComponent(titleFromGet)}`;
		} else if (data.error) {
			if (data.error == "Not allowed") {
				const extraInfo = data.extraInfo ?? "";
				openModal(
					`
                <h2>Bearbeitung blockiert</h2>
                <p>
                    Die Bearbeitung wurde von folgender automatischen Regel blockiert: <span class="codeh">${data.rule}</span>
                </p>
            `,
					false
				);
			} else if (data.error == "Warn") {
				const extraInfo = data.extraInfo ?? "";
				openModal(
					`
                <h2>Achtung</h2>
                <p>
                    Die Bearbeitung verstößt möglicherweise gegen folgende Regel: <span class="codeh">${data.rule}</span><br />
                    ${extraInfo}
                </p>
            `,
					false
				);
			} else {
				openModal(
					`
                <h2>Fehler</h2>
                <p>Ein Fehler ist aufgetreten.</p>
            `,
					true
				);
			}
		} else {
			openModal(
				`
            <h2>Fehler</h2>
            <p>Ein Fehler ist aufgetreten.</p>
        `,
				true
			);
		}
	});
}

// blocking
const blockBtn = document.getElementById("block-btn");
if (blockBtn) {
	blockBtn.addEventListener("click", async function () {
		console.log("executing!!!");

		const meId = ME_ID;
		const target = document.getElementById("target").value;
		const scope = $("#scope").val();
		const optCreateAccounts =
			document.getElementById("optCreateAccounts").value;
		const optSendEmails = document.getElementById("optSendEmails").value;
		const optOwnDiscussion =
			document.getElementById("optOwnDiscussion").value;
		const durationUntil = document.getElementById("datetimePicker").value;
		const reason = document.getElementById("reason").value;

		console.log(durationUntil);

		const response = await fetch("backend/blockAPI.php", {
			method: "POST",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify({
				target: target,
				scope: scope,
				optCreateAccounts: optCreateAccounts,
				optSendEmails: optSendEmails,
				optOwnDiscussion: optOwnDiscussion,
				durationUntil: durationUntil,
				reason: reason,
				meId: meId
			})
		});

		const data = await response.json();

		if (data.success) {
			// window.location.href = "?f=special:allusers";
		} else {
			console.error("Error while blocking user");
		}
	});
}

async function changeProtection(ns, name, protection) {
	await fetch("/api/v1/articles/protect", {
		method: "PATCH",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			namespace: ns,
			name: name,
			protected: protection
		})
	});

	window.location.reload();
}

const protectLink = document.getElementById("protect_link");
if (protectLink) {
	const page_split = PAGE.split(":");
	const ns = page_split[0];
	const name = page_split[1];

	let status;

	fetch(`/api/v1/articles/${ns}/${name}/protection`)
		.then((response) => {
			return response.json();
		})
		.then((data) => {
			status = data.status;
		})
		.catch((error) => {
			console.error("Fehler:", error);
		});

	protectLink.addEventListener("click", () => {
		openModal(
			`
		<h2>Schutzstatus ändern</h2>
		<button
			${status == "none" ? `class="highlighted" disabled` : ""}
			onclick="changeProtection('${ns}', '${name}', 'none')">
			Ungeschützt
		</button>
		<button
			${status == "semiprotected" ? `class="highlighted" disabled` : ""}
			onclick="changeProtection('${ns}', '${name}', 'semiprotected')">
			Nur für automatisch bestätigte Nutzer
		</button>
		<button
			${status == "protected" ? `class="highlighted" disabled` : ""}
			onclick="changeProtection('${ns}', '${name}', 'protected')">
			Nur für Administratoren
		</button>
		<button
			${status == "superprotected" ? `class="highlighted" disabled` : ""}
			onclick="changeProtection('${ns}', '${name}', 'superprotected')">
			Nur für UI-Administratoren
		</button>
		`,
			true
		);
	});
}

async function changeDeletion(ns, name, statusNow) {
	const method = statusNow ? "restore" : "delete";
	await fetch(`/api/v1/articles/${method}`, {
		method: "PATCH",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			namespace: ns,
			name: name,
			deletedBy: USER
		})
	});

	window.location.reload();
}

const deleteLink = document.getElementById("delete_link");
if (deleteLink) {
	const page_split = PAGE.split(":");
	const ns = page_split[0];
	const name = page_split[1];

	let status;

	fetch(`/api/v1/articles/${ns}/${name}/deleted`)
		.then((response) => {
			return response.json();
		})
		.then((data) => {
			status = data.status;
			deleteLink.textContent = status ? "Wiederherstellen" : "Löschen";
		})
		.catch((error) => {
			console.error("Fehler:", error);
		});

	deleteLink.addEventListener("click", () => {
		const word = status ? "wiederherstellen" : "löschen";
		openModal(`
			<h2>Seite ${word}</h2>
			<button onclick="changeDeletion('${ns}', '${name}', ${status})">Jetzt ${word}</button>
		`);
	});
}

async function movePage(ns, name) {
	const newNS = document.getElementById("new_ns_input").value;
	const newName = document.getElementById("new_name_input").value;
	const redirection = document.getElementById(
		"create_redirection_input"
	).checked;

	await fetch(`/api/v1/articles/move`, {
		method: "PATCH",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify({
			namespace: ns,
			name: name,
			newNamespace: newNS,
			newName: newName,
			createRedirection: redirection
		})
	});

	window.location.reload();
}

const moveLink = document.getElementById("move_link");
if (moveLink) {
	const page_split = PAGE.split(":");
	const ns = page_split[0];
	const name = page_split[1];

	moveLink.addEventListener("click", () => {
		openModal(`
			<h2>Seite verschieben</h2>
			Ziel:
			<input type="text" id="new_ns_input" value="${ns}" />
			<input type="text" id="new_name_input" value="${name}" />
			<input type="checkbox" id="create_redirection_input" checked />
			<label for="create_redirection_input">Weiterleitung erstellen</label><br /><br />
			<button onclick="movePage('${ns}', '${name}')">Jetzt verschieben</button>
		`);
	});
}

async function changeRoles(username, rolesObject) {
	const roleData = {};

	rolesObject.forEach((role) => {
		const roleName = role.name || role.id || role;
		const checkbox = document.querySelector(`input[name="${roleName}"]`);

		if (checkbox) {
			roleData[roleName] = checkbox.checked;
		}
	});

	try {
		const response = await fetch(`/api/v1/user/${username}/roles`, {
			method: "PATCH",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify({
				roles: roleData
			})
		});

		window.location.reload();
	} catch (error) {
		console.error("Fehler:", error);
	}
}

const userRolesLink = document.getElementById("user_roles_link");
if (userRolesLink) {
	const username = PAGE.split(":")[1];
	const roles = USERROLES;

	userRolesLink.addEventListener("click", async () => {
		try {
			const response = await fetch(`/static/roles.json`);
			const jsonObject = await response.json();

			let cleanRoles = roles.replace(/&#39;/g, '"');
			const userData = JSON.parse(cleanRoles);
			const userRolesArray = userData.roles || [];

			let boxes = "";
			jsonObject.forEach((role) => {
				const checked = userRolesArray.includes(role.name || role);
				boxes += `
                    <input type="checkbox" name="${role.name || role}" id="role_${role.name || role}" 
                           ${checked ? "checked" : ""} /> <label for="role_${role.name || role}">${role.name || role}</label><br />
                `;
			});

			openModal(`
                <h2>Benutzerrollen verwalten</h2>
                ${boxes}<br />
                <button id="saveRolesBtn" 
                        data-username="${username}"
                        data-roles='${JSON.stringify(jsonObject).replace(/'/g, "&#39;")}'>
                    Jetzt Rollen ändern
                </button>
            `);

			// ✅ EventListener nach Modal öffnen
			document
				.getElementById("saveRolesBtn")
				.addEventListener("click", () => {
					changeRoles(username, jsonObject);
				});
		} catch (error) {
			console.error("Fehler:", error);
			openModal(
				"<h2>Fehler</h2><p>Rollen konnten nicht geladen werden.</p>"
			);
		}
	});
}
