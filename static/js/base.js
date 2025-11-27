// Firebase конфигурация
const firebaseConfig = {
  apiKey: "AIzaSyAhLzb1UdObqvZoQixxxKBD6n6TXmf502I",
  authDomain: "aurus-pwa.firebaseapp.com",
  projectId: "aurus-pwa",
  storageBucket: "aurus-pwa.firebasestorage.app",
  messagingSenderId: "550033719644",
  appId: "1:550033719644:web:43ede90b5c87dbbcd40199",
  measurementId: "G-8ELDJ6532Y"
};

// Инициализируем Firebase
let messaging = null;
try {
    const app = firebase.initializeApp(firebaseConfig);
    messaging = firebase.messaging();
    console.log('Firebase initialized successfully');
} catch (error) {
    console.error('Firebase initialization error:', error);
}

// Service Worker Registration
if ('serviceWorker' in navigator) {
    console.log('Registering Service Worker...');
    navigator.serviceWorker.register('/service-worker.js', { scope: '/' })
        .then((registration) => {
            console.log('Service Worker зарегистрирован успешно:', registration);

            // Инициализируем Firebase Messaging после регистрации SW
            if (messaging) {
                initFirebaseMessaging(registration);
            }
        })
        .catch((error) => {
            console.log('Ошибка регистрации Service Worker:', error);
        });
} else {
    console.log('Service Worker не поддерживается');
}

// Firebase Messaging инициализация
function initFirebaseMessaging(registration) {
    // Используем существующий Service Worker для Firebase
    messaging.useServiceWorker(registration);

    // Обработка уведомлений когда приложение активно
    messaging.onMessage((payload) => {
        console.log('Received foreground message:', payload);

        // Показываем уведомление даже когда приложение открыто
        if (payload.notification) {
            showLocalNotification(
                payload.notification.title,
                payload.notification.body,
                payload.data?.url
            );
        }
    });

    // Проверяем статус уведомлений при инициализации
    setTimeout(checkNotificationStatus, 1000);
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

// Notifications
async function checkNotificationStatus() {
    try {
        // Проверяем есть ли сохраненный токен
        const hasToken = await checkStoredToken();
        updateNotificationButton(hasToken);
    } catch (error) {
        console.error('Error checking notification status:', error);
        updateNotificationButton(false);
    }
}

async function checkStoredToken() {
    // Можно проверить в localStorage или сделать запрос к серверу
    return localStorage.getItem('fcm_token') !== null;
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
        const hasToken = await checkStoredToken();

        if (hasToken) {
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
        if (!messaging) {
            showNotificationMessage('Firebase не инициализирован', 'error');
            return;
        }

        if (!('Notification' in window)) {
            showNotificationMessage('Этот браузер не поддерживает уведомления', 'error');
            return;
        }

        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            showNotificationMessage('Разрешение на уведомления не получено!', 'error');
            return;
        }

        // Получаем FCM токен
        const token = await messaging.getToken({
            vapidKey: 'BLk5vQJ4y7Q3a9zT8wX2R1cL0pM3nBv6qZ8dF9gH2jK5tY7wX' // Замените на ваш VAPID key если есть
        });

        if (token) {
            // Сохраняем токен на сервер и локально
            await sendTokenToServer(token);
            localStorage.setItem('fcm_token', token);

            updateNotificationButton(true);
            showNotificationMessage('🔔 Уведомления включены!', 'success');
        } else {
            showNotificationMessage('❌ Не удалось получить токен', 'error');
        }

    } catch (error) {
        console.error('Ошибка подписки:', error);
        showNotificationMessage('❌ Ошибка при включении уведомлений: ' + error.message, 'error');
    }
}

async function unsubscribeFromPush() {
    try {
        const token = localStorage.getItem('fcm_token');

        if (token) {
            // Удаляем токен с сервера
            await fetch('/api/push/unsubscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token: token
                })
            });

            // Удаляем токен локально и отзываем его в FCM
            localStorage.removeItem('fcm_token');
            if (messaging) {
                await messaging.deleteToken();
            }

            updateNotificationButton(false);
            showNotificationMessage('🔕 Уведомления отключены', 'success');
        }
    } catch (error) {
        console.error('Ошибка отписки:', error);
        showNotificationMessage('❌ Ошибка при отключении уведомлений: ' + error.message, 'error');
    }
}

async function sendTokenToServer(token) {
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
            token: token,
            user_id: user_id
        })
    });

    if (!response.ok) {
        throw new Error('Ошибка сохранения токена на сервере');
    }
}

function showLocalNotification(title, body, url = '/') {
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification(title, {
            body: body,
            icon: '/static/images/icon-192x192.png',
            data: { url: url }
        });

        notification.onclick = function() {
            window.focus();
            if (url) {
                window.location.href = url;
            }
            notification.close();
        };
    }
}

function showNotificationMessage(message, type) {
    // Удаляем существующие уведомления
    const existingAlerts = document.querySelectorAll('.alert-notification');
    existingAlerts.forEach(alert => alert.remove());

    const alert = document.createElement('div');
    alert.className = `alert-notification alert-${type}`;
    alert.textContent = message;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        min-width: 250px;
        padding: 12px 16px;
        border-radius: 4px;
        color: white;
        font-weight: bold;
        background: ${type === 'success' ? '#4CAF50' : '#f44336'};
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    `;

    document.body.appendChild(alert);

    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 3000);
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
        // Отписываемся от уведомлений при выходе
        try {
            await unsubscribeFromPush();
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