
let aircraftList = [];

async function loadFleetData() {
    try {
        const container = document.getElementById('fleetContainer');
        container.innerHTML = `
            <div class="loading-container">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading fleet information...</p>
            </div>
        `;

        const response = await fetch('/api/get/about_us?group=fleet&active=true');
        if (!response.ok) {
            throw new Error('Failed to load fleet data');
        }

        aircraftList = await response.json();
        renderFleet();

    } catch (error) {
        console.error('Error loading fleet:', error);
        const container = document.getElementById('fleetContainer');
        container.innerHTML = `
            <div class="no-results">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Unable to load fleet information. Please try again later.</p>
            </div>
        `;
    }
}

function renderFleet() {
    const container = document.getElementById('fleetContainer');

    if (aircraftList.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <i class="fas fa-plane-slash"></i>
                <p>No aircraft found in our fleet.</p>
            </div>
        `;
        return;
    }

    const typeFilter = document.getElementById('typeFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;

    let filteredAircraft = aircraftList;

    if (typeFilter !== 'all') {
        filteredAircraft = filteredAircraft.filter(aircraft =>
            aircraft.fleet_type === typeFilter
        );
    }

    if (statusFilter !== 'all') {
        if (statusFilter === 'active') {
            filteredAircraft = filteredAircraft.filter(aircraft => aircraft.is_active);
        } else if (statusFilter === 'maintenance') {
            filteredAircraft = filteredAircraft.filter(aircraft => !aircraft.is_active);
        }
    }

    if (filteredAircraft.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <p>No aircraft found matching your filters.</p>
                <button onclick="resetFilters()" class="btn-secondary" style="margin-top: 1rem;">
                    <i class="fas fa-redo"></i> Reset Filters
                </button>
            </div>
        `;
        return;
    }

    filteredAircraft.sort((a, b) => (a.display_order || 0) - (b.display_order || 0));

    container.innerHTML = filteredAircraft.map(aircraft => `
        <div class="fleet-card">
            <div class="fleet-image">
                ${aircraft.image ?
            `<img src="${aircraft.image}" alt="${aircraft.name}" loading="lazy">` :
            `<div class="placeholder"><i class="fas fa-plane"></i></div>`
        }
            </div>
            <div class="fleet-content">
                <h3 class="fleet-title">${aircraft.name}</h3>
                <div class="fleet-registration">
                    <i class="fas fa-hashtag"></i>
                    <span>${aircraft.registration_number || 'N/A'}</span>
                </div>
                <div class="fleet-details">
                    <div class="detail-item">
                        <span class="label">Type:</span>
                        <span>${getAircraftTypeLabel(aircraft.fleet_type)}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">Capacity:</span>
                        <span>${aircraft.capacity ? aircraft.capacity + ' passengers' : 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">First Flight:</span>
                        <span>${aircraft.first_flight || 'N/A'}</span>
                    </div>
                </div>
                ${aircraft.description ? `
                    <div class="fleet-description">
                        ${aircraft.description}
                    </div>
                ` : ''}
                <div class="fleet-status ${aircraft.is_active ? 'status-active' : 'status-maintenance'}">
                    ${aircraft.is_active ? 'Active' : 'Maintenance'}
                </div>
            </div>
        </div>
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

function resetFilters() {
    document.getElementById('typeFilter').value = 'all';
    document.getElementById('statusFilter').value = 'all';
    renderFleet();
}

document.addEventListener('DOMContentLoaded', function () {
    loadFleetData();
    document.getElementById('typeFilter').addEventListener('change', renderFleet);
    document.getElementById('statusFilter').addEventListener('change', renderFleet);
    document.getElementById('resetFilters').addEventListener('click', resetFilters);
});
