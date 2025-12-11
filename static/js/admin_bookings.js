
let currentBookingId = null;
const modal = document.getElementById('bookingModal');

document.addEventListener('DOMContentLoaded', function () {
    loadBookings();
});

async function loadBookings(flightFilter = '') {
    const container = document.getElementById('bookingsContainer');
    container.innerHTML = '<div class="loading">Loading bookings...</div>';

    try {
        const url = flightFilter ?
            `/admin/api/bookings?flight_number=${encodeURIComponent(flightFilter)}` :
            '/admin/api/bookings';

        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });

        if (response.status === 403) {
            container.innerHTML = '<div class="alert alert-error">Access denied. Admin privileges required.</div>';
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to load bookings');
        }

        const bookings = await response.json();
        displayBookings(bookings);

    } catch (error) {
        console.error('Error loading bookings:', error);
        container.innerHTML = '<div class="alert alert-error">Error loading bookings: ' + error.message + '</div>';
    }
}

function displayBookings(bookings) {
    const container = document.getElementById('bookingsContainer');

    if (bookings.length === 0) {
        container.innerHTML = '<div class="loading">No bookings found</div>';
        return;
    }

    container.innerHTML = bookings.map(booking => {
        const statusKey = `booking_status_${booking.id}`;
        const noteKey = `booking_note_${booking.id}`;
        const savedStatus = localStorage.getItem(statusKey);
        const savedNote = localStorage.getItem(noteKey) || '';

        return `
        <div class="booking-item">
            <div class="booking-header" onclick="openBookingModal('${booking.id}')">
                <div class="booking-flight">${booking.flight_number}</div>
                <div class="booking-id">ID: ${booking.id}</div>
            </div>
            <div class="booking-details" onclick="openBookingModal('${booking.id}')">
                <div class="booking-detail">
                    <span class="detail-label">Passenger:</span>
                    <span>${booking.passenger_name || booking.user_nickname}</span>
                </div>
                <div class="booking-detail">
                    <span class="detail-label">Seat:</span>
                    <span>${booking.seat} (${booking.serve_class})</span>
                </div>
                <div class="booking-detail">
                    <span class="detail-label">Status:</span>
                    <span class="${booking.valid ? 'valid-true' : 'valid-false'}">
                        ${booking.valid ? 'Valid' : 'Invalid'}
                    </span>
                </div>
            </div>

            <!-- Staff Controls -->
            <div class="staff-controls">
                <div class="status-buttons">
                    <button type="button" class="status-btn ${savedStatus === 'checkedIn' ? 'active' : ''}" onclick="toggleBookingStatus('${booking.id}', 'checkedIn', this)">Checked In</button>
                    <button type="button" class="status-btn ${savedStatus === 'boarded' ? 'active' : ''}" onclick="toggleBookingStatus('${booking.id}', 'boarded', this)">Boarded</button>
                </div>
                <input type="text"
                       class="note-input"
                       placeholder="Staff notes..."
                       value="${savedNote}"
                       oninput="setBookingNote('${booking.id}', this.value)">
            </div>
        </div>
        `;
    }).join('');
}

function toggleBookingStatus(bookingId, status, button) {
    const statusKey = `booking_status_${bookingId}`;
    const currentStatus = localStorage.getItem(statusKey);

    if (currentStatus === status) {
        button.classList.remove('active');
        localStorage.removeItem(statusKey);
    } else {
        const buttons = button.parentElement.querySelectorAll('.status-btn');
        buttons.forEach(btn => btn.classList.remove('active'));

        button.classList.add('active');
        localStorage.setItem(statusKey, status);
    }
}

function setBookingNote(bookingId, note) {
    localStorage.setItem(`booking_note_${bookingId}`, note);
}

function displayBookingModal(booking) {
    const modalBody = document.getElementById('modalBody');

    const paxServices = booking.pax_services || [];
    let totalPrice = 0;
    let servicesHtml = '';

    if (paxServices.length > 0) {
        servicesHtml = `
            <div class="form-group">
                <label>Selected Services:</label>
                <div class="services-list">
        `;

        paxServices.forEach(service => {
            const servicePrice = service.price || 0;
            totalPrice += servicePrice;
            servicesHtml += `
                    <div class="service-item">
                        <span class="service-name">${service.name || 'Unnamed Service'}</span>
                        <span class="service-price">$${servicePrice.toFixed(2)}</span>
                    </div>
            `;
        });

        servicesHtml += `
                </div>
            </div>
            <div class="form-group">
                <label>Total Services Price:</label>
                <input type="text" value="$${totalPrice.toFixed(2)}" readonly class="total-price">
            </div>
        `;
    } else {
        servicesHtml = `
            <div class="form-group">
                <label>Selected Services:</label>
                <div class="no-services">No additional services selected</div>
            </div>
        `;
    }

    const statusKey = `booking_status_${booking.id}`;
    const noteKey = `booking_note_${booking.id}`;

    const savedStatus = localStorage.getItem(statusKey);
    const savedNote = localStorage.getItem(noteKey) || '';

    modalBody.innerHTML = `
    <form id="bookingForm">
        <div class="form-group">
            <label for="bookingId">Booking ID:</label>
            <input type="text" id="bookingId" value="${booking.id}" readonly>
        </div>

        <div class="form-group">
            <label for="flightNumber">Flight Number:</label>
            <input type="text" id="flightNumber" name="flight_number" value="${booking.flight_number}" readonly>
        </div>

        <div class="form-group">
            <label for="passengerName">Passenger Name:</label>
            <input type="text" id="passengerName" name="passenger_name" value="${booking.passenger_name || ''}" placeholder="Enter passenger name">
        </div>

        <div class="form-group">
            <label for="seat">Seat:</label>
            <input type="text" id="seat" name="seat" value="${booking.seat}" required>
        </div>

        <div class="form-group">
            <label for="serveClass">Class:</label>
            <select id="serveClass" name="serve_class" required>
                <option value="economy" ${booking.serve_class === 'economy' ? 'selected' : ''}>Economy</option>
                <option value="business" ${booking.serve_class === 'business' ? 'selected' : ''}>Business</option>
                <option value="first" ${booking.serve_class === 'first' ? 'selected' : ''}>First Class</option>
            </select>
        </div>

        ${servicesHtml}

        <div class="status-section">
            <div class="form-group">
                <label>Passenger Status:</label>
                <div class="status-buttons-modal">
                    <button type="button" class="status-btn-modal ${savedStatus === 'checkedIn' ? 'active' : ''}" id="checkedInBtn">Checked In</button>
                    <button type="button" class="status-btn-modal ${savedStatus === 'boarded' ? 'active' : ''}" id="boardedBtn">Boarded</button>
                </div>
            </div>

            <div class="note-section">
                <label class="note-label" for="noteInput">Staff Notes:</label>
                <input type="text"
                       class="note-input"
                       id="noteInput"
                       placeholder="Enter staff notes..."
                       value="${savedNote}">
            </div>
        </div>

        <div class="form-group">
            <label for="boardingPass">Boarding Pass:</label>
            <input type="text" id="boardingPass" name="boarding_pass" value="${booking.boarding_pass || ''}" placeholder="No boarding pass generated" readonly>
        </div>

        <div class="form-group">
            <label>Flight Route:</label>
            <input type="text" value="${booking.departure || 'N/A'} → ${booking.arrival || 'N/A'}" readonly>
        </div>

        <div class="form-group">
            <label>Flight Date:</label>
            <input type="text" value="${booking.flight_datetime ? new Date(booking.flight_datetime * 1000).toLocaleString() : 'N/A'}" readonly>
        </div>

        <div class="form-group">
            <label for="userInfo">User Info:</label>
            <input type="text" value="${booking.user_nickname || 'N/A'} (Virtual ID: ${booking.user_virtual_id || 'N/A'}) - ${booking.user_group || 'N/A'}" readonly>
        </div>

        <div class="form-group">
            <label for="note">Notes:</label>
            <textarea id="note" name="note" placeholder="Additional notes...">${booking.note || ''}</textarea>
        </div>

        <div class="form-group">
            <label class="checkbox-label">
                <input type="checkbox" class="hidden-checkbox" name="valid" ${booking.valid ? 'checked' : ''}>
                <div class="checkbox-custom"></div>
                <span>Booking is Valid</span>
            </label>
        </div>

        <div class="form-group">
            <label>Created:</label>
            <input type="text" value="${new Date(booking.created_at * 1000).toLocaleString()}" readonly>
        </div>

        <div class="form-actions">
            <button type="button" class="cancel-btn" onclick="closeModal()">Cancel</button>
            <button type="submit" class="save-btn">Save Changes</button>
        </div>
    </form>
    `;

    initializeModalStatusButtons(booking.id, savedStatus);

    document.getElementById('bookingForm').addEventListener('submit', saveBookingChanges);
    modal.style.display = 'block';
}

function initializeModalStatusButtons(bookingId, savedStatus) {
    const checkedInBtn = document.getElementById('checkedInBtn');
    const boardedBtn = document.getElementById('boardedBtn');
    const noteInput = document.getElementById('noteInput');

    const statusKey = `booking_status_${bookingId}`;
    const noteKey = `booking_note_${bookingId}`;

    function toggleModalStatus(status, button) {
        const currentStatus = localStorage.getItem(statusKey);

        if (currentStatus === status) {
            button.classList.remove('active');
            localStorage.removeItem(statusKey);
        } else {
            checkedInBtn.classList.remove('active');
            boardedBtn.classList.remove('active');
            button.classList.add('active');
            localStorage.setItem(statusKey, status);
        }
    }

    if (savedStatus) {
        if (savedStatus === 'checkedIn') {
            checkedInBtn.classList.add('active');
        } else if (savedStatus === 'boarded') {
            boardedBtn.classList.add('active');
        }
    }

    checkedInBtn.addEventListener('click', () => {
        toggleModalStatus('checkedIn', checkedInBtn);
    });

    boardedBtn.addEventListener('click', () => {
        toggleModalStatus('boarded', boardedBtn);
    });

    noteInput.addEventListener('input', () => {
        localStorage.setItem(noteKey, noteInput.value);
    });
}

function applyFilters() {
    const flightFilter = document.getElementById('flightFilter').value;
    loadBookings(flightFilter);
}

function clearFilters() {
    document.getElementById('flightFilter').value = '';
    loadBookings();
}

async function openBookingModal(bookingId) {
    currentBookingId = bookingId;

    try {
        const response = await fetch(`/admin/api/bookings/${bookingId}`);
        if (!response.ok) {
            throw new Error('Failed to load booking details');
        }

        const booking = await response.json();
        displayBookingModal(booking);

    } catch (error) {
        console.error('Error loading booking details:', error);
        alert('Error loading booking details: ' + error.message);
    }
}

async function saveBookingChanges(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        flight_number: formData.get('flight_number'),
        passenger_name: formData.get('passenger_name'),
        seat: formData.get('seat'),
        serve_class: formData.get('serve_class'),
        pax_service: formData.get('pax_service'),
        boarding_pass: formData.get('boarding_pass'),
        note: formData.get('note'),
        valid: formData.get('valid') === 'on'
    };

    try {
        const response = await fetch(`/admin/api/bookings/${currentBookingId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error('Failed to update booking');
        }

        closeModal();
        loadBookings();
        alert('Booking updated successfully!');

    } catch (error) {
        console.error('Error updating booking:', error);
        alert('Error updating booking: ' + error.message);
    }
}

function closeModal() {
    modal.style.display = 'none';
    currentBookingId = null;
}

window.onclick = function (event) {
    if (event.target === modal) {
        closeModal();
    }
}

document.querySelector('.close').onclick = closeModal;
