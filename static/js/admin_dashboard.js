
function goToEditFlight() {
    const flightNumber = document.getElementById('flightNumberInput').value.trim();
    if (!flightNumber) {
        alert('Please enter a flight number');
        return;
    }
    window.location.href = `/admin/edit_flight?id=${encodeURIComponent(flightNumber)}`;
}

// Allow Enter key to submit the flight number
document.getElementById('flightNumberInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        goToEditFlight();
    }
});