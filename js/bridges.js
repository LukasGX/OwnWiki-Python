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
