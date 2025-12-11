
let bookingData = {
    selectedFlight: null,
    flightDetails: null,
    passengerInfo: {},
    selectedServices: [],
    selectedSeat: null,
    selectedSeatPrice: 0,
    seatmapConfig: null,
    existingBookings: [],
    bookingId: null,
    servicePrices: {},
    boardingPassStyle: 'default'
};

function formatDate(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${day}.${month} ${hours}:${minutes}`;
}

async function getCurrentUser() {
    try {
        const response = await fetch('/api/auth/me');
        if (response.ok) {
            const user = await response.json();
            return user;
        }
        return -1;
    } catch (error) {
        console.error('Error getting user:', error);
        return -1;
    }
}

function showStep(stepNumber) {
    document.querySelectorAll('.booking-step').forEach(step => {
        step.classList.remove('active');
    });
    const stepElement = document.getElementById('step' + stepNumber);
    if (stepElement) {
        stepElement.classList.add('active');
    }

    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
    });
    const stepIndicator = document.querySelector('.step[data-step="' + stepNumber + '"]');
    if (stepIndicator) {
        stepIndicator.classList.add('active');
    }

    if (stepNumber === 4) {
        loadSeatmap();
    } else if (stepNumber === 5) {
        updateConfirmationSummary();
    }
}

function nextStep(stepNumber) {
    if (stepNumber === 2 && !bookingData.selectedFlight) {
        alert('Please select a flight first');
        return;
    }
    if (stepNumber === 3) {
        const passengerName = document.getElementById('passengerName').value;
        const discordId = document.getElementById('discordId').value;
        const userId = document.getElementById('userId').value;

        if (!passengerName || !discordId || !userId) {
            alert('Please fill in all required passenger information');
            return;
        }

        bookingData.passengerInfo = {
            name: passengerName,
            discordId: discordId,
            userId: userId,
            specialRequests: document.getElementById('specialRequests').value
        };
        loadServices();
    }
    if (stepNumber === 4) {

    }
    if (stepNumber === 5 && !bookingData.selectedSeat) {
        alert('Please select a seat first');
        return;
    }

    showStep(stepNumber);
}

function prevStep(stepNumber) {
    showStep(stepNumber);
}


async function loadFlights() {
    const flightList = document.getElementById('flightList');
    if (!flightList) return;

    flightList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Loading flights...</p></div>';

    try {
        const response = await fetch('/api/get/schedule');

        if (!response.ok) {
            throw new Error('Failed to load flights');
        }

        const flights = await response.json();

        if (flights.length === 0) {
            flightList.innerHTML = '<div class="no-flights">No flights available</div>';
            return;
        }

        flightList.innerHTML = flights.map(flight => {
            const safeFlightNumber = flight.flight_number.replace(/'/g, "\\'");
            return `
            <div class="flight-card" onclick="selectFlight('${safeFlightNumber}')" data-flight="${flight.flight_number}">
                <div class="flight-header">
                    <div class="flight-number">Flight ${flight.flight_number}</div>
                    <div class="flight-status status-${flight.status.toLowerCase()}">${flight.status}</div>
                </div>
                <div class="flight-details">
                    <div class="route-info">
                        <div class="airport">${flight.departure}</div>
                        <div class="city">Departure</div>
                    </div>
                    <div class="route-arrow">
                        <i class="fas fa-long-arrow-alt-right"></i>
                    </div>
                    <div class="route-info">
                        <div class="airport">${flight.arrival}</div>
                        <div class="city">Arrival</div>
                    </div>
                </div>
                <div class="time-info">
                    <div class="datetime">${formatDate(new Date(flight.datetime * 1000))}</div>
                    <div class="duration">Enroute: ${flight.enroute}</div>
                </div>
                <div class="flight-meta">
                    <div class="meta-item">
                        <div class="meta-label">Aircraft</div>
                        <div class="meta-value">${flight.aircraft}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Flying</div>
                        <div class="meta-value">${flight.flying_count || 0} passengers</div>
                    </div>
                </div>
            </div>
            `;
        }).join('');

        const searchInput = document.getElementById('flightSearch');
        if (searchInput) {
            searchInput.addEventListener('input', function () {
                const searchTerm = this.value.toLowerCase();
                const flightCards = document.querySelectorAll('.flight-card');

                flightCards.forEach(card => {
                    const text = card.textContent.toLowerCase();
                    card.style.display = text.includes(searchTerm) ? 'block' : 'none';
                });
            });
        }

    } catch (error) {
        console.error('Error loading flights:', error);
        flightList.innerHTML = '<div class="error">Failed to load flights. Please try again.</div>';
    }
}

function selectFlight(flightNumber) {
    document.querySelectorAll('.flight-card').forEach(card => {
        card.classList.remove('selected');
    });

    const selectedCard = document.querySelector('.flight-card[data-flight="' + flightNumber + '"]');
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }

    const selectFlightBtn = document.getElementById('selectFlightBtn');
    if (selectFlightBtn) {
        selectFlightBtn.disabled = false;
    }

    bookingData.selectedFlight = flightNumber;

    loadFlightDetails(flightNumber);
}

async function loadFlightDetails(flightNumber) {
    try {
        const response = await fetch('/api/get/schedule');
        if (response.ok) {
            const flights = await response.json();
            const flight = flights.find(f => f.flight_number === flightNumber);

            if (flight) {
                bookingData.flightDetails = flight;
                bookingData.boardingPassStyle = flight.boarding_pass_default || 'default';
                console.log('Flight details loaded:', flight);
                console.log('Boarding pass style:', bookingData.boardingPassStyle);
                await loadExistingBookings(flightNumber);
            }
        }
    } catch (error) {
        console.error('Error loading flight details:', error);
    }
}

async function loadExistingBookings(flightNumber) {
    try {
        const response = await fetch('/api/get/bookings/' + flightNumber);
        if (response.ok) {
            bookingData.existingBookings = await response.json();
            console.log('Existing bookings loaded:', bookingData.existingBookings);
        }
    } catch (error) {
        console.error('Error loading existing bookings:', error);
    }
}

async function checkAuthStatus() {
    const user = await getCurrentUser();
    const authInfo = document.getElementById('authInfo');

    if (user && authInfo) {
        authInfo.style.display = 'block';
        bookingData.userInfo = user;
    } else {
        if (authInfo) {
            authInfo.style.display = 'none';
        }
    }
}

async function loadProfileInfo() {
    const user = await getCurrentUser();
    if (user) {
        const passengerName = document.getElementById('passengerName');
        const discordId = document.getElementById('discordId');
        const userId = document.getElementById('userId');

        if (passengerName) passengerName.value = user.nickname || '';
        if (discordId) discordId.value = user.social_id || '';
        if (userId) userId.value = user.virtual_id || '';

        bookingData.userId = user.id;
        bookingData.userVirtualId = user.virtual_id;
    }
}

async function loadServices() {
    const servicesList = document.getElementById('servicesList');
    if (!servicesList) return;

    servicesList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Loading services...</p></div>';

    try {
        if (!bookingData.flightDetails || !bookingData.flightDetails.pax_service) {
            servicesList.innerHTML = '<div class="no-services">No additional services available for this flight</div>';
            return;
        }

        const servicesString = bookingData.flightDetails.pax_service;
        console.log('Services string from flight:', servicesString);

        let availableServices = [];

        if (servicesString && servicesString.trim() !== '') {
            try {
                const serviceNames = JSON.parse(servicesString);
                if (Array.isArray(serviceNames)) {
                    const servicesResponse = await fetch('/api/get/flight_configs/service');
                    if (servicesResponse.ok) {
                        const servicesData = await servicesResponse.json();
                        console.log('All services from config:', servicesData);

                        availableServices = serviceNames.map(serviceName => {
                            const serviceConfig = servicesData.configs.find(config => config.name === serviceName);
                            if (serviceConfig) {
                                return {
                                    name: serviceConfig.name,
                                    price: serviceConfig.data?.price || 0,
                                    description: serviceConfig.description || ''
                                };
                            } else {
                                return {
                                    name: serviceName,
                                    price: 0,
                                    description: ''
                                };
                            }
                        });
                    } else {
                        availableServices = serviceNames.map(serviceName => ({
                            name: serviceName,
                            price: 0
                        }));
                    }
                } else {
                    const serviceNames = servicesString.split(',').map(s => s.trim()).filter(s => s !== '');
                    availableServices = serviceNames.map(serviceName => ({
                        name: serviceName,
                        price: 0
                    }));
                }
            } catch (e) {
                const serviceNames = servicesString.split(',').map(s => s.trim()).filter(s => s !== '');
                availableServices = serviceNames.map(serviceName => ({
                    name: serviceName,
                    price: 0
                }));
            }
        }

        console.log('Available services with prices:', availableServices);

        if (availableServices.length === 0) {
            servicesList.innerHTML = '<div class="no-services">No additional services available for this flight</div>';
            return;
        }

        servicesList.innerHTML = availableServices.map(service => {
            const safeServiceName = service.name.replace(/'/g, "\\'").replace(/"/g, '\\"');

            return `
                <div class="service-item" onclick="toggleService('${safeServiceName}', ${service.price})" data-service="${safeServiceName}">
                    <div class="service-header">
                        <div class="service-name">${service.name}</div>
                        <div class="service-price">λu ${service.price}</div>
                    </div>
                    ${service.description ? '<div class="service-description">' + service.description + '</div>' : ''}
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Error loading services:', error);
        servicesList.innerHTML = '<div class="error">Failed to load services. Please try again.</div>';
    }
}

function toggleService(serviceName, servicePrice) {
    const serviceItem = document.querySelector('.service-item[data-service="' + serviceName + '"]');
    const existingServiceIndex = bookingData.selectedServices.findIndex(s => s.name === serviceName);

    if (existingServiceIndex === -1) {
        bookingData.selectedServices.push({
            name: serviceName,
            price: servicePrice
        });
        if (serviceItem) {
            serviceItem.classList.add('selected');
        }
    } else {
        bookingData.selectedServices.splice(existingServiceIndex, 1);
        if (serviceItem) {
            serviceItem.classList.remove('selected');
        }
    }

    updateSelectedServicesList();
}

function updateSelectedServicesList() {
    const selectedList = document.getElementById('selectedServicesList');
    if (!selectedList) return;

    if (bookingData.selectedServices.length === 0) {
        selectedList.innerHTML = '<p class="no-services">No services selected</p>';
        return;
    }

    selectedList.innerHTML = bookingData.selectedServices.map(service => {
        const safeServiceName = service.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
        return `
        <div class="selected-service-item">
            <div class="service-info">
                <span class="service-name">${service.name}</span>
                <span class="service-price">λu ${service.price}</span>
            </div>
            <button class="remove-service" onclick="removeService('${safeServiceName}')">
                <i class="fas fa-times"></i>
            </button>
        </div>
        `;
    }).join('');
}

function removeService(serviceName) {
    const index = bookingData.selectedServices.findIndex(s => s.name === serviceName);
    if (index !== -1) {
        bookingData.selectedServices.splice(index, 1);

        const serviceItem = document.querySelector('.service-item[data-service="' + serviceName + '"]');
        if (serviceItem) {
            serviceItem.classList.remove('selected');
        }

        updateSelectedServicesList();
    }
}

async function loadSeatmap() {
    console.log('Loading seatmap...');

    if (!bookingData.selectedFlight || !bookingData.flightDetails) {
        console.error('No flight selected or flight details missing');
        const seatmap = document.getElementById('seatmap');
        if (seatmap) {
            seatmap.innerHTML = '<div class="error">Please select a flight first</div>';
        }
        return;
    }

    const seatmap = document.getElementById('seatmap');
    if (!seatmap) return;

    seatmap.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Loading seatmap...</p></div>';

    try {
        const seatmapConfigName = bookingData.flightDetails.seatmap;
        console.log('Loading seatmap config:', seatmapConfigName);

        if (!seatmapConfigName) {
            seatmap.innerHTML = '<div class="error">Seatmap configuration not available for this flight</div>';
            return;
        }

        const configResponse = await fetch('/api/get/flight_configs/cabin_layout');
        if (!configResponse.ok) {
            throw new Error('Failed to load cabin layouts');
        }

        const configData = await configResponse.json();
        console.log('Found cabin layouts:', configData);

        const seatmapConfig = configData.configs.find(config => config.name === seatmapConfigName);

        if (!seatmapConfig) {
            throw new Error('Seatmap config not found: ' + seatmapConfigName);
        }

        console.log('Found seatmap config:', seatmapConfig);

        if (seatmapConfig.data) {
            bookingData.seatmapConfig = seatmapConfig.data;
            console.log('Parsed seatmap config:', bookingData.seatmapConfig);
            renderSeatmap();
        } else {
            seatmap.innerHTML = '<div class="error">Seatmap configuration data is empty</div>';
        }

    } catch (error) {
        console.error('Error loading seatmap:', error);
        seatmap.innerHTML = '<div class="error">Failed to load seatmap: ' + error.message + '</div>';
    }
}

function renderSeatmap() {
    if (!bookingData.seatmapConfig) {
        console.error('No seatmap config available');
        const seatmap = document.getElementById('seatmap');
        if (seatmap) {
            seatmap.innerHTML = '<div class="error">No seatmap configuration available</div>';
        }
        return;
    }

    const seatmap = document.getElementById('seatmap');
    if (!seatmap) return;

    const config = bookingData.seatmapConfig;

    console.log('Rendering seatmap with config:', config);

    let seatmapHTML = '';

    if (!config.classes || !Array.isArray(config.classes) || config.classes.length === 0) {
        seatmap.innerHTML = '<div class="error">No cabin classes defined in seatmap configuration</div>';
        return;
    }

    config.classes.forEach(cabinClass => {
        seatmapHTML += '<div class="cabin-class">';

        if (!cabinClass.rows || !Array.isArray(cabinClass.rows) || cabinClass.rows.length < 2) {
            seatmapHTML += '<div class="error">Invalid row configuration</div></div>';
            return;
        }

        if (!cabinClass.seat_letters || !Array.isArray(cabinClass.seat_letters)) {
            seatmapHTML += '<div class="error">Invalid seat letters configuration</div></div>';
            return;
        }

        for (let row = cabinClass.rows[0]; row <= cabinClass.rows[1]; row++) {
            seatmapHTML += '<div class="seat-row">';
            seatmapHTML += '<div class="row-number">' + row + '</div>';
            seatmapHTML += '<div class="seats">';

            const aisles = cabinClass.aisles_after || [];
            const seatsPerRow = cabinClass.seat_letters.length;

            for (let i = 0; i < seatsPerRow; i++) {
                const seatLetter = cabinClass.seat_letters[i];
                const seatId = row + seatLetter;
                const seatStatus = getSeatStatus(seatId);
                const seatClass = getSeatClassType(cabinClass.name);
                const seatPrice = getSeatPrice(seatId, cabinClass);

                seatmapHTML += createSeatHTML(seatId, seatLetter, seatStatus, seatClass, seatPrice);

                if (aisles.includes(i + 1)) {
                    seatmapHTML += '<div class="aisle" title="Aisle"></div>';
                }
            }

            seatmapHTML += '</div></div>';
        }

        seatmapHTML += '</div>';
    });

    seatmap.innerHTML = seatmapHTML;
    console.log('Seatmap rendered successfully');
}

function getSeatClassType(className) {
    switch (className) {
        case 'First':
            return 'first-class';
        case 'Business':
            return 'business-class';
        case 'Economy':
            return 'economy-class';
        default:
            return 'economy-class';
    }
}

function getSeatPrice(seatId, cabinClass) {
    if (cabinClass.seat_prices && cabinClass.seat_prices[seatId]) {
        return cabinClass.seat_prices[seatId];
    }
    return cabinClass.base_price || 0;
}

function getSeatStatus(seatId) {
    if (bookingData.seatmapConfig.disabled_seats &&
        bookingData.seatmapConfig.disabled_seats.includes(seatId)) {
        return 'disabled';
    }

    if (bookingData.existingBookings &&
        bookingData.existingBookings.some(booking => booking.seat === seatId)) {
        return 'occupied';
    }

    return 'available';
}

function createSeatHTML(seatId, seatLetter, status, seatClass, price) {
    const priceDisplay = price > 0 ? '<div class="seat-price">λu ' + price + '</div>' : '';

    return '<div class="seat ' + seatClass + ' ' + status + '" onclick="selectSeat(\'' + seatId + '\', ' + price + ')" data-seat="' + seatId + '" title="Seat ' + seatId + ' - λu ' + price + '">' + seatLetter + priceDisplay + '</div>';
}

function selectSeat(seatId, price) {
    const seatElement = document.querySelector('.seat[data-seat="' + seatId + '"]');

    if (!seatElement || seatElement.classList.contains('occupied') || seatElement.classList.contains('disabled')) {
        return;
    }

    document.querySelectorAll('.seat').forEach(seat => {
        seat.classList.remove('selected');
    });

    seatElement.classList.add('selected');

    const confirmSeatBtn = document.getElementById('confirmSeatBtn');
    if (confirmSeatBtn) {
        confirmSeatBtn.disabled = false;
    }

    bookingData.selectedSeat = seatId;
    bookingData.selectedSeatPrice = price;

    updateSeatInfo(seatId, price);
}

function updateSeatInfo(seatId, price) {
    const seatDisplay = document.getElementById('selectedSeatDisplay');
    const seatDetails = document.getElementById('seatDetails');
    const priceInfo = document.getElementById('priceInfo');
    const priceAmount = document.getElementById('priceAmount');

    if (seatDisplay) seatDisplay.textContent = seatId;
    if (priceAmount) priceAmount.textContent = 'λu ' + price;
    if (priceInfo) priceInfo.style.display = 'block';

    let detailsHTML = '';
    const row = parseInt(seatId.match(/\d+/)[0]);
    const seatLetter = seatId.match(/[A-Z]/)[0];

    const cabinClass = bookingData.seatmapConfig.classes.find(cls =>
        row >= cls.rows[0] && row <= cls.rows[1]
    );

    if (cabinClass) {
        detailsHTML += '<p><strong>Class:</strong> ' + cabinClass.name + '</p>';
    }

    if (seatDetails) {
        seatDetails.innerHTML = detailsHTML || '<p>No additional information available</p>';
    }
}

function updateConfirmationSummary() {
    const servicesTotal = bookingData.selectedServices.reduce((total, service) => total + (service.price || 0), 0);
    const totalPrice = bookingData.selectedSeatPrice + servicesTotal;

    const flightSummary = document.getElementById('flightSummary');
    if (flightSummary && bookingData.flightDetails) {
        flightSummary.innerHTML = `
            <div class="summary-item">
                <span class="summary-label">Flight:</span>
                <span class="summary-value">${bookingData.flightDetails.flight_number}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Route:</span>
                <span class="summary-value">${bookingData.flightDetails.departure} → ${bookingData.flightDetails.arrival}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Date:</span>
                <span class="summary-value">${formatDate(new Date(bookingData.flightDetails.datetime * 1000))}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Aircraft:</span>
                <span class="summary-value">${bookingData.flightDetails.aircraft}</span>
            </div>
        `;
    }

    const passengerSummary = document.getElementById('passengerSummary');
    if (passengerSummary) {
        const passengerName = document.getElementById('passengerName').value;
        const discordId = document.getElementById('discordId').value;
        const userId = document.getElementById('userId').value;
        const specialRequests = document.getElementById('specialRequests').value;

        let passengerHTML = `
            <div class="summary-item">
                <span class="summary-label">Name:</span>
                <span class="summary-value">${passengerName}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Discord ID:</span>
                <span class="summary-value">${discordId}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Roblox ID:</span>
                <span class="summary-value">${userId}</span>
            </div>
        `;

        if (specialRequests) {
            passengerHTML += `
                <div class="summary-item">
                    <span class="summary-label">Special Requests:</span>
                    <span class="summary-value">${specialRequests}</span>
                </div>
            `;
        }

        passengerSummary.innerHTML = passengerHTML;
    }

    const servicesSummary = document.getElementById('servicesSummary');
    if (servicesSummary) {
        if (bookingData.selectedServices.length > 0) {
            servicesSummary.innerHTML = bookingData.selectedServices.map(service => `
                <div class="summary-item">
                    <span class="summary-label">${service.name}:</span>
                    <span class="summary-value">λu ${service.price}</span>
                </div>
            `).join('');
        } else {
            servicesSummary.innerHTML = '<p class="no-services">No additional services selected</p>';
        }
    }

    const seatSummary = document.getElementById('seatSummary');
    if (seatSummary && bookingData.selectedSeat) {
        seatSummary.innerHTML = `
            <div class="summary-item">
                <span class="summary-label">Seat:</span>
                <span class="summary-value">${bookingData.selectedSeat}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Class:</span>
                <span class="summary-value">${getSeatClass(bookingData.selectedSeat)}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Seat Price:</span>
                <span class="summary-value">λu ${bookingData.selectedSeatPrice}</span>
            </div>
        `;
    }

    const priceSummary = document.getElementById('priceSummary');
    if (priceSummary) {
        let priceHTML = `
            <div class="summary-item">
                <span class="summary-label">Seat Price:</span>
                <span class="summary-value">λu ${bookingData.selectedSeatPrice}</span>
            </div>
        `;

        if (servicesTotal > 0) {
            priceHTML += `
                <div class="summary-item">
                    <span class="summary-label">Services Total:</span>
                    <span class="summary-value">λu ${servicesTotal}</span>
                </div>
            `;
        }

        priceHTML += `
            <div class="summary-item total-price">
                <span class="summary-label">Total:</span>
                <span class="summary-value">λu ${totalPrice}</span>
            </div>
        `;

        priceSummary.innerHTML = priceHTML;
    }
}

function getSeatClass(seatId) {
    if (!bookingData.seatmapConfig || !bookingData.seatmapConfig.classes) {
        return 'Economy';
    }

    const row = parseInt(seatId.match(/\d+/)[0]);

    if (isNaN(row)) {
        return 'Economy';
    }

    for (const cabinClass of bookingData.seatmapConfig.classes) {
        if (cabinClass.rows && row >= cabinClass.rows[0] && row <= cabinClass.rows[1]) {
            return cabinClass.name || 'Economy';
        }
    }

    return 'Economy';
}

async function completeBooking() {
    const completeBtn = document.getElementById('completeBookingBtn');
    if (!completeBtn) return;

    completeBtn.disabled = true;
    completeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

    try {
        const passengerName = document.getElementById('passengerName').value;
        const discordId = document.getElementById('discordId').value;
        const userId = document.getElementById('userId').value;
        const specialRequests = document.getElementById('specialRequests').value;

        if (!passengerName || !discordId || !userId) {
            throw new Error('Please fill in all required passenger information');
        }

        if (!bookingData.selectedSeat) {
            throw new Error('Please select a seat first');
        }
        const user = await getCurrentUser();
        let user_id;
        if (!user) {
            user_id = -1
        } else {
            user_id = user.id
        }

        const bookingDataToSend = {
            flight_number: bookingData.selectedFlight,
            seat: bookingData.selectedSeat,
            serve_class: getSeatClass(bookingData.selectedSeat),
            pax_service: bookingData.selectedServices.map(s => s.name).join(', '),
            user_id: user_id,
            boarding_pass: bookingData.boardingPassStyle,
            note: specialRequests,
            passenger_name: passengerName,
            social_id: discordId,
            virtual_id: userId
        };

        console.log('Sending booking data:', bookingDataToSend);
        console.log('Using boarding pass style:', bookingData.boardingPassStyle);

        const response = await fetch('/api/post/booking/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(bookingDataToSend)
        });

        console.log('Response status:', response.status);

        const responseText = await response.text();
        console.log('Response text:', responseText);

        let result;
        try {
            result = JSON.parse(responseText);
        } catch (e) {
            console.error('Failed to parse JSON response:', e);
            throw new Error('Invalid response from server');
        }

        if (response.ok) {
            console.log('Booking successful:', result);
            bookingData.bookingId = result.booking_id;

            showBoardingPassStep(result.booking_id);
        } else {
            console.error('Booking failed:', result);
            throw new Error(result.error || 'Booking failed');
        }

    } catch (error) {
        console.error('Booking error:', error);
        alert('Booking failed: ' + error.message);

        completeBtn.disabled = false;
        completeBtn.innerHTML = '<i class="fas fa-check"></i> Complete Booking';
    }
}

function showBoardingPassStep(bookingId) {
    const bookingIdDisplay = document.getElementById('bookingIdDisplay');
    if (bookingIdDisplay) {
        bookingIdDisplay.textContent = bookingId;
    }
    showStep(6);
    generatePreview();
}

async function generatePreview() {
    if (!bookingData.bookingId) {
        alert('No booking ID available');
        return;
    }

    const preview = document.getElementById('boardingPassPreview');
    if (!preview) return;

    preview.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Generating preview...</p></div>';

    try {
        const response = await fetch('/api/get/boarding_pass/' + bookingData.bookingId + '/' + bookingData.boardingPassStyle);

        if (response.ok) {
            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);

            preview.innerHTML = '<div style="text-align: center;"><img src="' + imageUrl + '" alt="Boarding Pass Preview" style="max-width: 100%; max-height: 350px;" /></div>';
        } else {
            const errorText = await response.text();
            console.error('Preview error:', errorText);
            preview.innerHTML = '<div class="error">Failed to generate preview: ' + response.status + '</div>';
        }
    } catch (error) {
        console.error('Error generating preview:', error);
        preview.innerHTML = '<div class="error">Failed to generate preview: ' + error.message + '</div>';
    }
}

async function downloadBoardingPass(format) {
    if (!bookingData.bookingId) {
        alert('No booking ID available');
        return;
    }

    try {
        let url, filename;

        if (format === 'png') {
            url = '/api/get/boarding_pass/' + bookingData.bookingId + '/' + bookingData.boardingPassStyle;
            filename = 'boarding-pass-' + bookingData.bookingId + '.png';
        } else if (format === 'pdf') {
            url = '/api/get/boarding_pass_pdf/' + bookingData.bookingId + '/' + bookingData.boardingPassStyle;
            filename = 'boarding-pass-' + bookingData.bookingId + '.pdf';
        } else {
            throw new Error('Invalid format');
        }

        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

    } catch (error) {
        console.error('Error downloading boarding pass:', error);
        alert('Failed to download boarding pass');
    }
}

function goToHome() {
    window.location.href = '/';
}

function viewMyBookings() {
    window.location.href = '/profile';
}

document.addEventListener('DOMContentLoaded', function () {
    loadFlights();
    checkAuthStatus();

    document.querySelectorAll('.step').forEach(step => {
        step.addEventListener('click', function () {
            const stepNumber = parseInt(this.getAttribute('data-step'));
            const currentStep = getCurrentStep();

            if (stepNumber <= currentStep + 1) {
                showStep(stepNumber);

                if (stepNumber === 3 && bookingData.selectedFlight) {
                    loadServices();
                } else if (stepNumber === 4 && bookingData.selectedFlight) {
                    loadSeatmap();
                } else if (stepNumber === 5) {
                    updateConfirmationSummary();
                }
            }
        });
    });
});

function getCurrentStep() {
    const activeStep = document.querySelector('.booking-step.active');
    if (activeStep) {
        return parseInt(activeStep.id.replace('step', ''));
    }
    return 1;
}
