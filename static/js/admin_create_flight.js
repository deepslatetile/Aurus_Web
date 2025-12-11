
let seatmaps = [];
let boardingStyles = [];
let availableServices = [];

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
        } else {
            console.error('Failed to load boarding styles:', boardingResponse.status);
            document.getElementById('boarding_pass_default').innerHTML = '<option value="">Error loading boarding styles</option>';
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

        if (style.type === 'boarding_style') {
            const drawFunc = style.data?.draw_function || 'default';
            option.textContent = `${style.name} (${drawFunc})`;
        }
        else {
            option.textContent = style.name;
        }

        select.appendChild(option);
    });
}

function populateServices() {
    const container = document.getElementById('servicesCheckboxes');
    container.innerHTML = '';

    if (availableServices.length === 0) {
        container.innerHTML = '<div class="loading-text">No services available. Create your first service!</div>';
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

    document.getElementById('boarding_pass_default').addEventListener('change', function () {
        const customInput = document.getElementById('boarding_pass_custom');
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

document.getElementById('previewBtn').addEventListener('click', function () {
    const formData = new FormData(document.getElementById('createFlightForm'));
    const previewSection = document.getElementById('previewSection');
    const previewContent = document.getElementById('flightPreview');

    const status = getComboValue('status', 'status_custom');
    const meal = getComboValue('meal', 'meal_custom');
    const seatmap = getComboValue('seatmap', 'seatmap_custom');
    const boardingPass = getComboValue('boarding_pass_default', 'boarding_pass_custom');

    if (!formData.get('flight_number') || !formData.get('aircraft')) {
        showAlert('Please fill in flight number and aircraft type first', 'error');
        return;
    }

    const selectedServices = Array.from(document.querySelectorAll('input[name="services"]:checked'))
        .map(checkbox => {
            const price = checkbox.getAttribute('data-price');
            return `${checkbox.value} ($${price})`;
        });

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

    if (selectedServices.length > 0) {
        previewHTML += `
            <div class="preview-item">
                <span class="preview-label">Services:</span>
                <span class="preview-value">${selectedServices.join(', ')}</span>
            </div>
        `;
    }

    previewHTML += `
        <div class="preview-item">
            <span class="preview-label">Quick Actions:</span>
            <span class="preview-value">
                <button type="button" class="btn-small" onclick="createDiscordWebhook()" style="margin-top: 5px;">
                    <i class="fab fa-discord"></i> Create Discord Notification
                </button>
            </span>
        </div>
    `;

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

document.getElementById('createFlightForm').addEventListener('submit', async function (e) {
    e.preventDefault();

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

    const requiredFields = [
        'flight_number', 'departure', 'arrival', 'datetime',
        'enroute', 'status', 'seatmap', 'aircraft', 'boarding_pass_default'
    ];

    const missingFields = requiredFields.filter(field => {
        if (field === 'datetime') return !formData.get('datetime');
        return !flightData[field];
    });

    if (missingFields.length > 0) {
        showAlert(`Please fill all required fields: ${missingFields.join(', ')}`, 'error');
        return;
    }

    if (departureDateTime <= new Date()) {
        showAlert('Departure time must be in the future', 'error');
        return;
    }

    const createBtn = document.getElementById('createBtn');
    createBtn.disabled = true;
    createBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';

    try {
        const response = await fetch('/api/post/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(flightData)
        });

        if (response.ok) {
            showAlert('Flight created successfully!', 'success');
            document.getElementById('createFlightForm').reset();
            document.getElementById('previewSection').style.display = 'none';

            const now = new Date();
            const departureTime = new Date(now.getTime() + 60 * 60 * 1000);

            document.getElementById('datetime').value = departureTime.toISOString().slice(0, 16);
            document.getElementById('enroute').value = '1h 30m';
            document.getElementById('status').value = 'Scheduled';
            document.getElementById('meal').value = 'Standard Meal Service';

            document.getElementById('status_custom').style.display = 'none';
            document.getElementById('meal_custom').style.display = 'none';
            document.getElementById('seatmap_custom').style.display = 'none';
            document.getElementById('boarding_pass_custom').style.display = 'none';

        } else {
            const error = await response.json();
            showAlert('Failed to create flight: ' + (error.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error creating flight:', error);
        showAlert('Error creating flight: ' + error.message, 'error');
    } finally {
        createBtn.disabled = false;
        createBtn.innerHTML = '<i class="fas fa-plus"></i> Create Flight';
    }
});

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

function createDiscordWebhook() {
    const formData = new FormData(document.getElementById('createFlightForm'));

    const flightData = {
        flight_number: formData.get('flight_number'),
        departure: formData.get('departure'),
        arrival: formData.get('arrival'),
        datetime: formData.get('datetime'),
        enroute: formData.get('enroute'),
        status: getComboValue('status', 'status_custom'),
        seatmap: getComboValue('seatmap', 'seatmap_custom'),
        aircraft: formData.get('aircraft'),
        meal: getComboValue('meal', 'meal_custom'),
        boarding_pass: getComboValue('boarding_pass_default', 'boarding_pass_custom'),
        timestamp: Date.now()
    };

    const selectedServices = Array.from(document.querySelectorAll('input[name="services"]:checked'))
        .map(checkbox => checkbox.value);

    if (selectedServices.length > 0) {
        flightData.services = selectedServices;
    }

    if (!flightData.flight_number || !flightData.departure || !flightData.arrival) {
        showAlert('Please fill in flight number, departure, and arrival before creating a webhook', 'error');
        return;
    }

    const encodedData = encodeURIComponent(JSON.stringify(flightData));

    window.open(`/admin/webhooks?flight_data=${encodedData}`, '_blank');
}

document.addEventListener('DOMContentLoaded', function () {
    console.log("Admin create flight page loaded, initializing...");

    loadConfigurations();
    setupComboInputs();
    setupServiceCreation();

    const now = new Date();
    const departureTime = new Date(now.getTime() + 60 * 60 * 1000);

    document.getElementById('datetime').value = departureTime.toISOString().slice(0, 16);
    document.getElementById('enroute').value = '1h 30m';
    document.getElementById('status').value = 'Scheduled';
    document.getElementById('meal').value = 'Standard Meal Service';

    console.log("Admin create flight page initialized successfully");

    const formActions = document.querySelector('.form-actions');
    const webhookBtn = document.createElement('button');
    webhookBtn.type = 'button';
    webhookBtn.id = 'webhookBtn';
    webhookBtn.className = 'btn-secondary';
    webhookBtn.innerHTML = '<i class="fab fa-discord"></i> Discord Webhook';
    webhookBtn.style.marginLeft = '10px';
    webhookBtn.addEventListener('click', createDiscordWebhook);

    const previewBtn = document.getElementById('previewBtn');
    previewBtn.parentNode.insertBefore(webhookBtn, previewBtn.nextSibling);
});
