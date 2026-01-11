function logout() {
	fetch("/api/v1/user/logout", {
		method: "POST",
		credentials: "same-origin"
	}).then((response) => {
		if (response.ok) {
			window.location.reload();
		} else {
			alert("Logout failed.");
		}
	});
}

function updatePreview() {
	const content = document.getElementById("content").value;
	fetch(`/api/v1/articles/preview?md=${encodeURIComponent(content)}`, {
		method: "GET",
		credentials: "same-origin"
	})
		.then((response) => {
			if (response.ok) {
				return response.text();
			} else {
				throw new Error("Preview update failed.");
			}
		})
		.then((html) => {
			document.getElementById("preview").innerHTML = html;
		})
		.catch((error) => {
			console.error(error);
		});
}

function saveFile() {
	const content = document.getElementById("content").value;
	const splitPage = PAGE.split(":");
	const namespace = splitPage[0];
	const name = splitPage[1];
	fetch("/api/v1/articles/save", {
		method: "PATCH",
		credentials: "same-origin",
		headers: {
			"Content-Type": "application/json",
			Accept: "application/json"
		},
		body: JSON.stringify({
			namespace: namespace,
			name: name,
			content: content
		})
	})
		.then((response) => {
			if (response.ok) {
				return response.text();
			} else {
				throw new Error("Saving failed.");
			}
		})
		.then(() => {
			window.location.href = `/wiki/${namespace}:${name}`;
		})
		.catch((error) => {
			console.error(error);
		});
}

function createFile() {
	const content = document.getElementById("content").value;
	const title = document.getElementById("title").value;
	const splitPage = PAGE.split(":");
	const namespace = splitPage[0];
	const name = splitPage[1];
	fetch("/api/v1/articles/create", {
		method: "PUT",
		credentials: "same-origin",
		headers: {
			"Content-Type": "application/json",
			Accept: "application/json"
		},
		body: JSON.stringify({
			namespace: namespace,
			name: name,
			title: title,
			content: content
		})
	})
		.then((response) => {
			if (response.ok) {
				return response.text();
			} else {
				throw new Error("Creating failed.");
			}
		})
		.then(() => {
			window.location.href = `/wiki/${namespace}:${name}`;
		})
		.catch((error) => {
			console.error(error);
		});
}

const previewBtn = document.getElementById("update-preview");
if (previewBtn) {
	previewBtn.addEventListener("click", (event) => {
		event.preventDefault();
		updatePreview();
	});
}

const saveBtn = document.getElementById("save");
if (saveBtn) {
	saveBtn.addEventListener("click", (event) => {
		event.preventDefault();
		saveFile();
	});
}

const createBtn = document.getElementById("create");
if (createBtn) {
	createBtn.addEventListener("click", (event) => {
		event.preventDefault();
		createFile();
	});
}
