
let currentBooking = null;
let currentUser = null;

async function loadBookingInfo() {
    const bookingId = document.getElementById('bookingId').value;
    if (!bookingId) {
        alert('Please enter booking ID');
        return;
    }

    try {
        const response = await fetch(`/admin/api/bookings/${bookingId}`);
        if (!response.ok) {
            throw new Error('Booking not found');
        }

        currentBooking = await response.json();
        displayBookingInfo(currentBooking);

        const servicesTotal = currentBooking.pax_services.reduce((total, service) => total + (parseFloat(service.price) || 0), 0);
        document.getElementById('paymentAmount').value = servicesTotal.toFixed(2);
        document.getElementById('paymentDescription').value = `Payment for booking ${bookingId} - Services`;

    } catch (error) {
        alert('Error loading booking: ' + error.message);
    }
}

function displayBookingInfo(booking) {
    document.getElementById('bookingInfo').style.display = 'block';
    document.getElementById('infoFlight').textContent = booking.flight_number;
    document.getElementById('infoPassenger').textContent = booking.passenger_name || booking.user_nickname;
    document.getElementById('infoSeat').textContent = `${booking.seat} (${booking.serve_class})`;

    const servicesTotal = booking.pax_services.reduce((total, service) => total + (parseFloat(service.price) || 0), 0);
    document.getElementById('infoServicesTotal').textContent = `$${servicesTotal.toFixed(2)}`;
}

async function loadUserInfo() {
    const identifier = document.getElementById('userIdentifier').value;
    if (!identifier) {
        alert('Please enter user identifier');
        return;
    }

    try {
        let response = await fetch(`/api/get/users/virtual/${identifier}`);
        if (!response.ok) {
            response = await fetch(`/api/get/user/${identifier}`);
            if (!response.ok) {
                throw new Error('User not found');
            }
        }

        currentUser = await response.json();
        displayUserInfo(currentUser);

    } catch (error) {
        alert('Error loading user: ' + error.message);
    }
}

function displayUserInfo(user) {
    document.getElementById('userInfo').style.display = 'block';
    document.getElementById('infoNickname').textContent = user.nickname;
    document.getElementById('infoMiles').textContent = user.miles || 0;
}

async function processBookingPayment() {
    if (!currentBooking) {
        alert('Please load booking first');
        return;
    }

    const amount = parseFloat(document.getElementById('paymentAmount').value);
    const description = document.getElementById('paymentDescription').value;

    if (isNaN(amount) || amount <= 0) {
        alert('Please enter valid positive amount');
        return;
    }

    if (!description) {
        alert('Please enter description');
        return;
    }

    try {
        const response = await fetch('/api/post/transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentBooking.user_id,
                booking_id: currentBooking.id,
                amount: -amount,
                description: description,
                type: 'booking_payment'
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to process payment');
        }

        alert('Booking payment processed successfully!');
        resetForms();

    } catch (error) {
        console.error('Payment error:', error);
        alert('Error processing payment: ' + error.message);
    }
}

async function processUserPayment() {
    if (!currentUser) {
        alert('Please load user first');
        return;
    }

    const amount = parseFloat(document.getElementById('userAmount').value);
    const description = document.getElementById('userDescription').value;

    if (isNaN(amount) || amount === 0) {
        alert('Please enter valid non-zero amount');
        return;
    }

    if (!description) {
        alert('Please enter description');
        return;
    }

    try {
        const transactionType = amount > 0 ? 'payment' : 'withdrawal';

        const response = await fetch('/api/post/transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUser.id,
                amount: amount,
                description: description,
                type: transactionType
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to process transaction');
        }

        alert('Transaction processed successfully!');
        resetForms();

    } catch (error) {
        console.error('Transaction error:', error);
        alert('Error processing transaction: ' + error.message);
    }
}

async function processMassPayment() {
    const flightNumber = document.getElementById('flightNumber').value.trim();
    const amount = parseFloat(document.getElementById('massAmount').value);
    const description = document.getElementById('massDescription').value.trim();

    if (!flightNumber) {
        alert('Please enter flight number');
        return;
    }

    if (isNaN(amount) || amount === 0) {
        alert('Please enter valid non-zero amount');
        return;
    }

    if (!description) {
        alert('Please enter description');
        return;
    }

    const transactionType = amount > 0 ? 'mass_payment' : 'mass_withdrawal';
    const actionType = amount > 0 ? 'payment' : 'withdrawal';

    if (!confirm(`Process $${Math.abs(amount).toFixed(2)} ${actionType} for all valid bookings on flight ${flightNumber}?\nThis action cannot be undone.`)) {
        return;
    }

    try {
        const processBtn = document.querySelector('.mass-btn');
        const originalText = processBtn.innerHTML;
        processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        processBtn.disabled = true;

        const response = await fetch(`/admin/api/bookings?flight_number=${flightNumber}`);
        if (!response.ok) {
            throw new Error('Failed to load bookings');
        }

        const bookings = await response.json();

        const validBookings = bookings.filter(booking =>
            booking.valid === true || booking.valid === 1
        );

        console.log(`Found ${validBookings.length} valid bookings for flight ${flightNumber}`);

        if (validBookings.length === 0) {
            alert('No valid bookings found for this flight');
            processBtn.innerHTML = originalText;
            processBtn.disabled = false;
            return;
        }

        let processed = 0;
        let errors = 0;
        const errorDetails = [];

        for (const booking of validBookings) {
            try {
                console.log('Processing booking:', booking.id);

                const bookingDetailResponse = await fetch(`/admin/api/bookings/${booking.id}`);
                if (!bookingDetailResponse.ok) {
                    throw new Error(`Failed to get booking details for ${booking.id}`);
                }

                const bookingDetail = await bookingDetailResponse.json();
                const userId = bookingDetail.user_id;

                if (!userId) {
                    console.warn(`No user_id found for booking ${booking.id}`);
                    errors++;
                    errorDetails.push(`Booking ${booking.id}: No user ID`);
                    continue;
                }

                const transactionResponse = await fetch('/api/post/transaction', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        booking_id: booking.id,
                        amount: amount,
                        description: `${description} - Flight ${flightNumber}`,
                        type: transactionType
                    })
                });

                const transactionResult = await transactionResponse.json();

                if (transactionResponse.ok) {
                    processed++;
                    console.log(`✅ Processed ${actionType} for user ${userId}, booking ${booking.id}`);
                } else {
                    errors++;
                    errorDetails.push(`Booking ${booking.id}: ${transactionResult.error || 'Transaction failed'}`);
                    console.warn(`❌ Failed ${actionType} for booking ${booking.id}:`, transactionResult.error);
                }

            } catch (error) {
                errors++;
                errorDetails.push(`Booking ${booking.id}: ${error.message}`);
                console.error(`❌ Error processing booking ${booking.id}:`, error);
            }
        }

        let resultMessage = `Mass ${actionType} completed!\nProcessed: ${processed}\nErrors: ${errors}`;

        if (errors > 0) {
            resultMessage += `\n\nError details:\n${errorDetails.slice(0, 5).join('\n')}`;
            if (errorDetails.length > 5) {
                resultMessage += `\n... and ${errorDetails.length - 5} more errors`;
            }
            console.error('Mass payment errors:', errorDetails);
        }

        alert(resultMessage);

        if (processed > 0) {
            resetForms();
        }

    } catch (error) {
        console.error('Mass payment error:', error);
        alert('Error processing mass payment: ' + error.message);
    } finally {
        const processBtn = document.querySelector('.mass-btn');
        processBtn.innerHTML = '<i class="fas fa-users"></i> Process Mass Payment';
        processBtn.disabled = false;
    }
}

async function loadUserTransactions() {
    const userId = document.getElementById('searchUserId').value.trim();
    if (!userId) {
        alert('Please enter user ID');
        return;
    }

    try {
        const container = document.getElementById('transactionsList');
        container.innerHTML = '<div class="loading">Loading transactions...</div>';

        const response = await fetch(`/api/get/transactions/user/${userId}`);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to load transactions');
        }

        const transactions = await response.json();
        displayTransactions(transactions);

    } catch (error) {
        console.error('Load transactions error:', error);
        const container = document.getElementById('transactionsList');
        container.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

function displayTransactions(transactions) {
    const container = document.getElementById('transactionsList');

    if (transactions.length === 0) {
        container.innerHTML = '<div class="loading">No transactions found</div>';
        return;
    }

    container.innerHTML = transactions.map(transaction => {
        const amount = parseFloat(transaction.amount);

        return `
        <div class="transaction-item">
            <div class="transaction-header">
                <div class="transaction-amount ${amount >= 0 ? 'amount-positive' : 'amount-negative'}">
                    ${amount >= 0 ? '+' : ''}$${amount.toFixed(2)}
                </div>
                <div class="transaction-date">${transaction.created_at_formatted}</div>
            </div>
            <div class="transaction-details">
                <div class="transaction-detail">
                    <span class="detail-label">Description:</span>
                    <span>${transaction.description}</span>
                </div>
                <div class="transaction-detail">
                    <span class="detail-label">Type:</span>
                    <span>${transaction.type}</span>
                </div>
                <div class="transaction-detail">
                    <span class="detail-label">Booking ID:</span>
                    <span>${transaction.booking_id || 'N/A'}</span>
                </div>
                <div class="transaction-detail">
                    <span class="detail-label">Admin:</span>
                    <span>${transaction.admin_nickname}</span>
                </div>
            </div>
        </div>
        `;
    }).join('');
}

function resetForms() {
    document.getElementById('bookingInfo').style.display = 'none';
    document.getElementById('userInfo').style.display = 'none';
    currentBooking = null;
    currentUser = null;
    document.querySelectorAll('input').forEach(input => {
        if (input.type !== 'button') input.value = '';
    });
}
