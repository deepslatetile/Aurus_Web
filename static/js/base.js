// Service Worker Registration
if ('serviceWorker' in navigator) {
    console.log('Registering Service Worker...');
    navigator.serviceWorker.register('/service-worker.js', { scope: '/' })
        .then((registration) => {
            console.log('Service Worker зарегистрирован успешно:', registration);
            console.log('Scope:', registration.scope);
        })
        .catch((error) => {
            console.log('Ошибка регистрации Service Worker:', error);
        });
} else {
    console.log('Service Worker не поддерживается');
}

// Navigation
async function loadNavigation() {
    try {
        const response = await fetch('/api/get/web_config/state/1');
        const pages = await response.json();

        const navMenu = document.getElementById('navMenu');
        const mobileDropdownMenu = document.getElementById('mobileDropdownMenu');

        navMenu.innerHTML = '';
        mobileDropdownMenu.innerHTML = '';

        pages.forEach(page => {
            const desktopItem = document.createElement('li');
            desktopItem.className = 'nav-item';
            const desktopLink = document.createElement('a');
            desktopLink.href = `/${page.page_name}`;
            desktopLink.textContent = page.page_display;
            desktopItem.appendChild(desktopLink);
            navMenu.appendChild(desktopItem);

            const mobileItem = document.createElement('li');
            mobileItem.className = 'mobile-dropdown-item';
            const mobileLink = document.createElement('a');
            mobileLink.href = `/${page.page_name}`;
            mobileLink.textContent = page.page_display;
            mobileItem.appendChild(mobileLink);
            mobileDropdownMenu.appendChild(mobileItem);
        });

    } catch (error) {
        console.error('Error loading navigation:', error);
        const fallbackPages = [
            { page_name: '', page_display: 'Home' },
            { page_name: 'schedule', page_display: 'Schedule' }
        ];

        const navMenu = document.getElementById('navMenu');
        const mobileDropdownMenu = document.getElementById('mobileDropdownMenu');

        navMenu.innerHTML = '';
        mobileDropdownMenu.innerHTML = '';

        fallbackPages.forEach(page => {
            const desktopItem = document.createElement('li');
            desktopItem.className = 'nav-item';
            const desktopLink = document.createElement('a');
            desktopLink.href = `/${page.page_name}`;
            desktopLink.textContent = page.page_display;
            desktopItem.appendChild(desktopLink);
            navMenu.appendChild(desktopItem);

            const mobileItem = document.createElement('li');
            mobileItem.className = 'mobile-dropdown-item';
            const mobileLink = document.createElement('a');
            mobileLink.href = `/${page.page_name}`;
            mobileLink.textContent = page.page_display;
            mobileItem.appendChild(mobileLink);
            mobileDropdownMenu.appendChild(mobileItem);
        });
    }
}

// Auth
async function loadAuthButtons() {
    try {
        const response = await fetch('/api/auth/me');
        if (response.ok) {
            const user = await response.json();
            const displayName = window.innerWidth < 480 ?
                user.nickname.substring(0, 10) + (user.nickname.length > 10 ? '...' : '') :
                user.nickname;

            document.getElementById('authButtons').innerHTML = `
                <div class="auth-section">
                    <button class="notification-btn" id="notificationBtn" onclick="toggleNotifications()">
                        <i class="fas fa-bell bell-icon"></i>
                        <div class="status-dot"></div>
                    </button>
                    <div class="user-info">
                        <div class="user-avatar">${user.nickname.charAt(0).toUpperCase()}</div>
                        <span>${displayName}</span>
                    </div>
                    <button class="logout-btn" onclick="logout()">
                        <i class="fas fa-sign-out-alt"></i> ${window.innerWidth < 480 ? '' : 'Logout'}
                    </button>
                </div>
            `;

            setTimeout(checkNotificationStatus, 100);
        } else {
            document.getElementById('authButtons').innerHTML = `
                <a href="/login" class="login-btn">
                    <i class="fas fa-user"></i> ${window.innerWidth < 480 ? '' : 'Login'}
                </a>
            `;
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
        document.getElementById('authButtons').innerHTML = `
            <a href="/login" class="login-btn">
                <i class="fas fa-user"></i> ${window.innerWidth < 480 ? '' : 'Login'}
            </a>
        `;
    }
}

// Mobile Menu
function toggleMobileMenu() {
    const mobileDropdown = document.getElementById('mobileDropdown');
    const toggleButton = document.querySelector('.mobile-menu-toggle');

    mobileDropdown.classList.toggle('active');

    const icon = toggleButton.querySelector('i');
    if (mobileDropdown.classList.contains('active')) {
        icon.className = 'fas fa-times';
    } else {
        icon.className = 'fas fa-bars';
    }
}

function closeMobileMenu() {
    const mobileDropdown = document.getElementById('mobileDropdown');
    const toggleButton = document.querySelector('.mobile-menu-toggle');

    mobileDropdown.classList.remove('active');
    toggleButton.querySelector('i').className = 'fas fa-bars';
}

// Logout
async function logout() {
    try {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            if (subscription) {
                await unsubscribeFromPush();
            }
        } catch (e) {
            console.log('Error unsubscribing on logout:', e);
        }

        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Notifications
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

async function checkNotificationStatus() {
    try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        updateNotificationButton(!!subscription);
    } catch (error) {
        console.error('Error checking notification status:', error);
        updateNotificationButton(false);
    }
}

function updateNotificationButton(isSubscribed) {
    const btn = document.getElementById('notificationBtn');
    if (btn) {
        if (isSubscribed) {
            btn.classList.add('subscribed', 'active');
            btn.title = 'Уведомления включены (нажмите чтобы отключить)';
        } else {
            btn.classList.remove('subscribed', 'active');
            btn.title = 'Уведомления выключены (нажмите чтобы включить)';
        }
    }
}

async function toggleNotifications() {
    console.log('Toggle notifications clicked');

    try {
        if (!('serviceWorker' in navigator)) {
            showNotificationMessage('❌ Ваш браузер не поддерживает уведомления', 'error');
            return;
        }

        if (!('PushManager' in window)) {
            showNotificationMessage('❌ Ваш браузер не поддерживает push-уведомления', 'error');
            return;
        }

        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();

        if (subscription) {
            await unsubscribeFromPush();
        } else {
            await subscribeToPush();
        }
    } catch (error) {
        console.error('Error toggling notifications:', error);
        showNotificationMessage('❌ Ошибка при переключении уведомлений: ' + error.message, 'error');
    }
}

async function subscribeToPush() {
    try {
        if (!('Notification' in window)) {
            showNotificationMessage('Этот браузер не поддерживает уведомления', 'error');
            return;
        }

        const permission = await Notification.requestPermission();

        if (permission !== 'granted') {
            showNotificationMessage('Разрешение на уведомления не получено!', 'error');
            return;
        }

        const registration = await navigator.serviceWorker.ready;

        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array('BM7DyIdnHT3n9NMl0RyvIBidOPtntzo8pI9OuhpTPEXthjcx4MziDCR2NHEfxVUhvzwqUdM77IKMhx3ftXM_svo')
        });

        await sendSubscriptionToServer(subscription);

        updateNotificationButton(true);
        showNotificationMessage('🔔 Уведомления включены!', 'success');

    } catch (error) {
        console.error('Ошибка подписки:', error);
        showNotificationMessage('❌ Ошибка при включении уведомлений', 'error');
    }
}

async function unsubscribeFromPush() {
    try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();

        if (subscription) {
            await fetch('/api/push/unsubscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    endpoint: subscription.endpoint
                })
            });

            await subscription.unsubscribe();

            updateNotificationButton(false);
            showNotificationMessage('🔕 Уведомления отключены', 'success');
        }
    } catch (error) {
        console.error('Ошибка отписки:', error);
        showNotificationMessage('❌ Ошибка при отключении уведомлений', 'error');
    }
}

async function sendSubscriptionToServer(subscription) {
    let user_id = null;
    try {
        const userResponse = await fetch('/api/auth/me');
        if (userResponse.ok) {
            const user = await userResponse.json();
            user_id = user.id;
        }
    } catch (e) {
        console.log('User not authenticated for notifications');
    }

    const response = await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            subscription: subscription,
            user_id: user_id
        })
    });

    if (!response.ok) {
        throw new Error('Ошибка сохранения подписки');
    }
}

function showNotificationMessage(message, type) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alert.style.position = 'fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = '10000';
    alert.style.minWidth = '250px';

    document.body.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 3000);
}

// Event Listeners
document.addEventListener('click', function(event) {
    const mobileDropdown = document.getElementById('mobileDropdown');
    const toggleButton = document.querySelector('.mobile-menu-toggle');

    if (!mobileDropdown.contains(event.target) && !toggleButton.contains(event.target)) {
        closeMobileMenu();
    }
});

window.addEventListener('resize', function() {
    if (window.innerWidth > 768) {
        closeMobileMenu();
    }
    loadAuthButtons();
});

document.addEventListener('DOMContentLoaded', function() {
    loadNavigation();
    loadAuthButtons();

    // Add mobile menu toggle event
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', toggleMobileMenu);
    }
});