const now = new Date();
const tomorrow = new Date(now);
tomorrow.setDate(tomorrow.getDate() + 1);
tomorrow.setSeconds(0);
tomorrow.setMilliseconds(0);

const distanceDisplay = document.querySelector("[data-display=distance]");

function updateDistanceDisplay(selectedDate) {
	if (!distanceDisplay) return;

	if (selectedDate) {
		const now = new Date();
		now.setSeconds(0);
		now.setMilliseconds(0);

		let start = new Date(now);
		let end = new Date(selectedDate);

		// Determine years
		let years = end.getFullYear() - start.getFullYear();

		// Determine months
		let months = end.getMonth() - start.getMonth();
		if (months < 0) {
			years--;
			months += 12;
		}

		// Determine days
		let days = end.getDate() - start.getDate();
		if (days < 0) {
			months--;
			if (months < 0) {
				years--;
				months += 12;
			}
			// Calculate the number of days in the previous month correctly
			const previousMonth = new Date(end.getFullYear(), end.getMonth(), 0);
			days += previousMonth.getDate();
		}

		// Determine hours and minutes
		let hours = end.getHours() - start.getHours();
		if (hours < 0) {
			days--;
			hours += 24;
			if (days < 0) {
				months--;
				if (months < 0) {
					years--;
					months += 12;
				}
				const previousMonth = new Date(end.getFullYear(), end.getMonth(), 0);
				days += previousMonth.getDate();
			}
		}

		let minutes = end.getMinutes() - start.getMinutes();
		if (minutes < 0) {
			hours--;
			minutes += 60;
			if (hours < 0) {
				days--;
				hours += 24;
				if (days < 0) {
					months--;
					if (months < 0) {
						years--;
						months += 12;
					}
					const previousMonth = new Date(end.getFullYear(), end.getMonth(), 0);
					days += previousMonth.getDate();
				}
			}
		}

		const y = years > 0 ? (years === 1 ? `${years} Jahr` : `${years} Jahre`) : "";
		const mo = months > 0 ? (months === 1 ? `${months} Monat` : `${months} Monate`) : "";
		const d = days > 0 ? (days === 1 ? `${days} Tag` : `${days} Tage`) : "";
		const h = hours > 0 ? `${hours}h` : "";
		const min = minutes > 0 ? `${minutes}min` : "";

		distanceDisplay.textContent = [y, mo, d, h, min].filter(Boolean).join(", ");
	} else {
		distanceDisplay.textContent = "Kein Datum gewählt";
	}
}

flatpickr("#datetimePicker", {
	enableTime: true,
	dateFormat: "d.m.Y H:i",
	time_24hr: true,
	locale: "de",
	wrap: false,
	allowInput: true,
	defaultDate: tomorrow,
	monthSelectorType: "static",
	onReady: function () {
		updateDistanceDisplay(tomorrow);
	},
	onChange: function (selectedDates) {
		if (selectedDates.length > 0) {
			updateDistanceDisplay(selectedDates[0]);
		} else {
			updateDistanceDisplay(null);
		}
	},
});
