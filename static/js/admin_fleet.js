
let fleetData = [];
let currentAircraftId = null;

const modal = document.getElementById('aircraftModal');
const modalTitle = document.getElementById('modalTitle');
const aircraftForm = document.getElementById('aircraftForm');
const closeBtn = document.querySelector('.close');
const cancelBtn = document.getElementById('cancelAircraftBtn');

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

async function loadFleetData() {
    try {
        const response = await fetch('/api/get/about_us?group=fleet');
        if (!response.ok) throw new Error('Failed to load fleet data');

        fleetData = await response.json();
        renderFleetTable();

    } catch (error) {
        console.error('Error loading fleet:', error);
        showAlert('Failed to load fleet data: ' + error.message, 'error');
    }
}

function renderFleetTable() {
    const tbody = document.getElementById('fleetTableBody');

    if (fleetData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="loading-cell">
                    <i class="fas fa-plane-slash"></i>
                    <p>No aircraft found. Add your first aircraft!</p>
                </td>
            </tr>
        `;
        return;
    }

    fleetData.sort((a, b) => (a.display_order || 0) - (b.display_order || 0));

    tbody.innerHTML = fleetData.map(aircraft => `
        <tr>
            <td>${aircraft.name}</td>
            <td>${getAircraftTypeLabel(aircraft.fleet_type)}</td>
            <td><code>${aircraft.registration_number || 'N/A'}</code></td>
            <td>${aircraft.capacity || 'N/A'}</td>
            <td>${aircraft.first_flight || 'N/A'}</td>
            <td>
                <span class="status-badge ${aircraft.is_active ? 'badge-active' : 'badge-inactive'}">
                    ${aircraft.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <div class="action-buttons">
                    <button onclick="editAircraft(${aircraft.id})" class="btn-small btn-edit">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button onclick="toggleAircraftStatus(${aircraft.id}, ${aircraft.is_active})" 
                            class="btn-small btn-toggle ${aircraft.is_active ? '' : 'inactive'}">
                        <i class="fas fa-power-off"></i> ${aircraft.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button onclick="deleteAircraft(${aircraft.id})" class="btn-small btn-delete">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function getAircraftTypeLabel(type) {
    const types = {
        'narrow-body': 'Narrow-Body',
        'wide-body': 'Wide-Body',
        'regional': 'Regional',
        'cargo': 'Cargo'
    };
    return types[type] || type;
}

function openModal(isEdit = false) {
    modal.style.display = 'flex';
    modalTitle.textContent = isEdit ? 'Edit Aircraft' : 'Add New Aircraft';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    modal.style.display = 'none';
    currentAircraftId = null;
    aircraftForm.reset();
    document.body.style.overflow = 'auto';
}

function editAircraft(id) {
    const aircraft = fleetData.find(a => a.id === id);
    if (!aircraft) return;

    currentAircraftId = id;

    document.getElementById('aircraftId').value = aircraft.id;
    document.getElementById('aircraftName').value = aircraft.name || '';
    document.getElementById('fleetType').value = aircraft.fleet_type || '';
    document.getElementById('registrationNumber').value = aircraft.registration_number || '';
    document.getElementById('capacity').value = aircraft.capacity || '';
    document.getElementById('firstFlight').value = aircraft.first_flight || '';
    document.getElementById('displayOrder').value = aircraft.display_order || 0;
    document.getElementById('aircraftDescription').value = aircraft.description || '';
    document.getElementById('aircraftImage').value = aircraft.image || '';
    document.getElementById('aircraftStatus').value = aircraft.is_active ? 'true' : 'false';

    openModal(true);
}

async function toggleAircraftStatus(id, currentStatus) {
    if (!confirm(`Are you sure you want to ${currentStatus ? 'deactivate' : 'activate'} this aircraft?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/put/about_us/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: !currentStatus })
        });

        if (response.ok) {
            showAlert(`Aircraft ${currentStatus ? 'deactivated' : 'activated'} successfully!`, 'success');
            loadFleetData();
        } else {
            const error = await response.json();
            showAlert('Failed to update aircraft: ' + (error.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error updating aircraft:', error);
        showAlert('Error updating aircraft: ' + error.message, 'error');
    }
}

async function deleteAircraft(id) {
    if (!confirm('Are you sure you want to delete this aircraft? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/delete/about_us/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('Aircraft deleted successfully!', 'success');
            loadFleetData();
        } else {
            const error = await response.json();
            showAlert('Failed to delete aircraft: ' + (error.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error deleting aircraft:', error);
        showAlert('Error deleting aircraft: ' + error.message, 'error');
    }
}

aircraftForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = Object.fromEntries(formData);

    if (data.capacity) data.capacity = parseInt(data.capacity);
    if (data.first_flight) data.first_flight = parseInt(data.first_flight);
    if (data.display_order) data.display_order = parseInt(data.display_order);
    data.is_active = data.is_active === 'true';

    const submitBtn = this.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        let response;
        if (currentAircraftId) {
            response = await fetch(`/api/put/about_us/${currentAircraftId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } else {
            response = await fetch('/api/post/about_us', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }

        if (response.ok) {
            showAlert(`Aircraft ${currentAircraftId ? 'updated' : 'created'} successfully!`, 'success');
            closeModal();
            loadFleetData();
        } else {
            const error = await response.json();
            showAlert('Failed to save aircraft: ' + (error.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error saving aircraft:', error);
        showAlert('Error saving aircraft: ' + error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Save Aircraft';
    }
});

document.addEventListener('DOMContentLoaded', function () {
    loadFleetData();

    document.getElementById('addAircraftBtn').addEventListener('click', () => openModal(false));
    document.getElementById('refreshBtn').addEventListener('click', loadFleetData);

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    window.addEventListener('click', function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });
});
