
let seatmaps = [];
let boardingStyles = [];
let availableServices = [];
let currentFlightId = null;

function getFlightIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id');
}

async function loadFlightData(flightId) {
    try {
        const response = await fetch(`/api/get/schedule/${flightId}`);
        if (!response.ok) {
            throw new Error('Failed to load flight data');
        }

        const flightData = await response.json();
        populateForm(flightData);

    } catch (error) {
        console.error('Error loading flight data:', error);
        showAlert('Error loading flight data: ' + error.message, 'error');
    }
}

function populateForm(flightData) {
    document.getElementById('flightId').value = flightData.id;
    document.getElementById('flightNumber').value = flightData.flight_number;
    document.getElementById('departure').value = flightData.departure;
    document.getElementById('arrival').value = flightData.arrival;
    document.getElementById('aircraft').value = flightData.aircraft;
    document.getElementById('enroute').value = flightData.enroute;

    const date = new Date(flightData.datetime * 1000);
    const datetimeString = date.toISOString().slice(0, 16);
    document.getElementById('datetime').value = datetimeString;

    setComboValue('status', 'status_custom', flightData.status);

    setComboValue('meal', 'meal_custom', flightData.meal);

    setComboValue('seatmap', 'seatmap_custom', flightData.seatmap);

    document.getElementById('boarding_pass_default').value = flightData.boarding_pass_default;

    try {
        const services = JSON.parse(flightData.pax_service || '[]');
        services.forEach(serviceName => {
            const checkbox = document.querySelector(`input[name="services"][value="${serviceName}"]`);
            if (checkbox) {
                checkbox.checked = true;
            }
        });
    } catch (e) {
        console.error('Error parsing services:', e);
    }
}

function setComboValue(selectId, customInputId, value) {
    const select = document.getElementById(selectId);
    const customInput = document.getElementById(customInputId);

    let optionExists = false;
    for (let option of select.options) {
        if (option.value === value) {
            optionExists = true;
            break;
        }
    }

    if (optionExists) {
        select.value = value;
        customInput.style.display = 'none';
    } else {
        select.value = 'custom';
        customInput.value = value;
        customInput.style.display = 'block';
    }
}

async function loadConfigurations() {
    try {
        const seatmapsResponse = await fetch('/api/get/flight_configs/cabin_layout');
        if (seatmapsResponse.ok) {
            const seatmapsData = await seatmapsResponse.json();
            seatmaps = seatmapsData.configs || [];
            populateSeatmaps();
        }

        const boardingResponse = await fetch('/api/get/flight_configs/boarding_style');
        if (boardingResponse.ok) {
            const boardingData = await boardingResponse.json();
            boardingStyles = boardingData.configs || [];
            populateBoardingStyles();
        }

        const servicesResponse = await fetch('/api/get/flight_configs/service');
        if (servicesResponse.ok) {
            const servicesData = await servicesResponse.json();
            availableServices = servicesData.configs || [];
            populateServices();
        }

    } catch (error) {
        console.error('Error loading configurations:', error);
        showAlert('Error loading configuration data', 'error');
    }
}

function populateSeatmaps() {
    const select = document.getElementById('seatmap');
    select.innerHTML = '<option value="">Select or enter custom...</option>';

    if (seatmaps.length === 0) {
        select.innerHTML += '<option value="custom">Enter custom seatmap...</option>';
        return;
    }

    seatmaps.forEach(seatmap => {
        const option = document.createElement('option');
        option.value = seatmap.name;
        const seats = seatmap.data?.seats || 'N/A';
        const layout = seatmap.data?.layout || 'N/A';
        option.textContent = `${seatmap.name} (${seats} seats, ${layout})`;
        select.appendChild(option);
    });

    select.innerHTML += '<option value="custom">Enter custom seatmap...</option>';
}

function populateBoardingStyles() {
    const select = document.getElementById('boarding_pass_default');
    select.innerHTML = '<option value="">Select boarding pass style...</option>';

    if (boardingStyles.length === 0) {
        select.innerHTML = '<option value="">No boarding styles available</option>';
        return;
    }

    boardingStyles.forEach(style => {
        const option = document.createElement('option');
        option.value = style.name;

        const drawFunc = style.data?.draw_function || 'default';
        option.textContent = `${style.name} (${drawFunc})`;
        select.appendChild(option);
    });
}

function populateServices() {
    const container = document.getElementById('servicesCheckboxes');
    container.innerHTML = '';

    if (availableServices.length === 0) {
        container.innerHTML = '<div class="loading-text">No services available</div>';
        return;
    }

    availableServices.forEach(service => {
        const checkboxItem = document.createElement('div');
        checkboxItem.className = 'checkbox-item';

        const price = service.data?.price || 0;
        const category = service.data?.category || 'general';

        checkboxItem.innerHTML = `
            <input type="checkbox" id="service_${service.id}" name="services" value="${service.name}" data-price="${price}">
            <label for="service_${service.id}">
                ${service.name}
                <br><small style="color: #8fa3d8;">${service.description || ''}</small>
            </label>
            <span class="service-price">$${price.toFixed(2)}</span>
        `;

        container.appendChild(checkboxItem);
    });
}

function setupComboInputs() {
    document.getElementById('status').addEventListener('change', function () {
        const customInput = document.getElementById('status_custom');
        if (this.value === 'custom') {
            customInput.style.display = 'block';
            customInput.required = true;
        } else {
            customInput.style.display = 'none';
            customInput.required = false;
        }
    });
    document.getElementById('meal').addEventListener('change', function () {
        const customInput = document.getElementById('meal_custom');
        if (this.value === 'custom') {
            customInput.style.display = 'block';
        } else {
            customInput.style.display = 'none';
        }
    });

    document.getElementById('seatmap').addEventListener('change', function () {
        const customInput = document.getElementById('seatmap_custom');
        if (this.value === 'custom') {
            customInput.style.display = 'block';
            customInput.required = true;
        } else {
            customInput.style.display = 'none';
            customInput.required = false;
        }
    });
}

function getComboValue(selectId, customInputId) {
    const select = document.getElementById(selectId);

    if (selectId === 'boarding_pass_default') {
        return select.value;
    }

    const customInput = document.getElementById(customInputId);
    if (select.value === 'custom' && customInput.value.trim()) {
        return customInput.value.trim();
    }
    return select.value;
}

document.getElementById('editFlightForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const flightId = document.getElementById('flightId').value;
    const formData = new FormData(this);

    const status = getComboValue('status', 'status_custom');
    const meal = getComboValue('meal', 'meal_custom');
    const seatmap = getComboValue('seatmap', 'seatmap_custom');
    const boardingPass = getComboValue('boarding_pass_default', 'boarding_pass_custom');

    const departureDateTime = new Date(formData.get('datetime'));
    const datetime = Math.floor(departureDateTime.getTime() / 1000);

    const flightData = {
        flight_number: formData.get('flight_number'),
        departure: formData.get('departure'),
        arrival: formData.get('arrival'),
        datetime: datetime,
        enroute: formData.get('enroute'),
        status: status,
        seatmap: seatmap,
        aircraft: formData.get('aircraft'),
        meal: meal,
        pax_service: JSON.stringify(Array.from(document.querySelectorAll('input[name="services"]:checked'))
            .map(checkbox => checkbox.value)),
        boarding_pass_default: boardingPass
    };

    const updateBtn = document.getElementById('updateBtn');
    updateBtn.disabled = true;
    updateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';

    try {
        const response = await fetch(`/api/put/schedule/${flightId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(flightData)
        });

        if (response.ok) {
            showAlert('Flight updated successfully!', 'success');
        } else {
            const error = await response.json();
            showAlert('Failed to update flight: ' + (error.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error updating flight:', error);
        showAlert('Error updating flight: ' + error.message, 'error');
    } finally {
        updateBtn.disabled = false;
        updateBtn.innerHTML = '<i class="fas fa-save"></i> Update Flight';
    }
});

document.getElementById('deleteBtn').addEventListener('click', function () {
    const flightNumber = document.getElementById('flightNumber').value;
    document.getElementById('deleteFlightNumber').textContent = flightNumber;
    document.getElementById('deleteModal').style.display = 'flex';
});

document.querySelector('#deleteModal .close').addEventListener('click', closeDeleteModal);
document.getElementById('cancelDeleteBtn').addEventListener('click', closeDeleteModal);
document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDelete);

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

async function confirmDelete() {
    const flightId = document.getElementById('flightId').value;
    const deleteBtn = document.getElementById('confirmDeleteBtn');

    deleteBtn.disabled = true;
    deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

    try {
        const response = await fetch(`/api/delete/schedule/${flightId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('Flight deleted successfully!', 'success');
            setTimeout(() => {
                window.location.href = '/admin/bookings';
            }, 1500);
        } else {
            const error = await response.json();
            showAlert('Failed to delete flight: ' + (error.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error deleting flight:', error);
        showAlert('Error deleting flight: ' + error.message, 'error');
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Delete Flight';
        closeDeleteModal();
    }
}

document.getElementById('previewBtn').addEventListener('click', function () {
    const formData = new FormData(document.getElementById('editFlightForm'));
    const previewSection = document.getElementById('previewSection');
    const previewContent = document.getElementById('flightPreview');

    const status = getComboValue('status', 'status_custom');
    const meal = getComboValue('meal', 'meal_custom');
    const seatmap = getComboValue('seatmap', 'seatmap_custom');
    const boardingPass = getComboValue('boarding_pass_default', 'boarding_pass_custom');

    let previewHTML = `
        <div class="preview-item">
            <span class="preview-label">Flight Number:</span>
            <span class="preview-value">${formData.get('flight_number') || 'N/A'}</span>
        </div>
        <div class="preview-item">
            <span class="preview-label">Aircraft:</span>
            <span class="preview-value">${formData.get('aircraft') || 'N/A'}</span>
        </div>
        <div class="preview-item">
            <span class="preview-label">Route:</span>
            <span class="preview-value">${formData.get('departure') || 'N/A'} → ${formData.get('arrival') || 'N/A'}</span>
        </div>
        <div class="preview-item">
            <span class="preview-label">Departure:</span>
            <span class="preview-value">${formatDateTime(formData.get('datetime')) || 'N/A'}</span>
        </div>
        <div class="preview-item">
            <span class="preview-label">Duration:</span>
            <span class="preview-value">${formData.get('enroute') || 'N/A'}</span>
        </div>
        <div class="preview-item">
            <span class="preview-label">Status:</span>
            <span class="preview-value">${status || 'N/A'}</span>
        </div>
        <div class="preview-item">
            <span class="preview-label">Meal Service:</span>
            <span class="preview-value">${meal || 'N/A'}</span>
        </div>
        <div class="preview-item">
            <span class="preview-label">Seatmap:</span>
            <span class="preview-value">${seatmap || 'N/A'}</span>
        </div>
        <div class="preview-item">
            <span class="preview-label">Boarding Pass Style:</span>
            <span class="preview-value">${boardingPass || 'N/A'}</span>
        </div>
    `;

    const selectedServices = Array.from(document.querySelectorAll('input[name="services"]:checked'))
        .map(checkbox => {
            const price = checkbox.getAttribute('data-price');
            return `${checkbox.value} ($${price})`;
        });

    if (selectedServices.length > 0) {
        previewHTML += `
            <div class="preview-item">
                <span class="preview-label">Services:</span>
                <span class="preview-value">${selectedServices.join(', ')}</span>
            </div>
        `;
    }

    previewContent.innerHTML = previewHTML;
    previewSection.style.display = 'block';
    previewSection.scrollIntoView({ behavior: 'smooth' });
});

function formatDateTime(datetimeString) {
    if (!datetimeString) return 'N/A';
    try {
        const date = new Date(datetimeString);
        return date.toLocaleString();
    } catch (e) {
        return datetimeString;
    }
}

function showAlert(message, type) {
    const alertsContainer = document.getElementById('adminAlerts');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;

    alertsContainer.appendChild(alert);

    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 0.5s ease';
        setTimeout(() => alert.remove(), 500);
    }, 5000);

    alert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

document.addEventListener('DOMContentLoaded', function () {
    const flightId = getFlightIdFromUrl();

    if (!flightId) {
        showAlert('No flight ID provided', 'error');
        return;
    }

    currentFlightId = flightId;

    loadConfigurations();
    setupComboInputs();
    loadFlightData(flightId);

    console.log("Admin edit flight page initialized for flight ID:", flightId);
});
