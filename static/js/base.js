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
            
            // Проверяем статус уведомлений после загрузки кнопки
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

// Функции для уведомлений
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
    try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        
        if (subscription) {
            // Отписываемся
            await unsubscribeFromPush();
        } else {
            // Подписываемся
            await subscribeToPush();
        }
    } catch (error) {
        console.error('Error toggling notifications:', error);
        showNotificationMessage('❌ Ошибка при переключении уведомлений', 'error');
    }
}

async function subscribeToPush() {
    try {
        // Проверяем поддержку уведомлений
        if (!('Notification' in window)) {
            showNotificationMessage('Этот браузер не поддерживает уведомления', 'error');
            return;
        }

        // Запрашиваем разрешение
        const permission = await Notification.requestPermission();

        if (permission !== 'granted') {
            showNotificationMessage('Разрешение на уведомления не получено!', 'error');
            return;
        }

        // Регистрируем Service Worker
        const registration = await navigator.serviceWorker.ready;

        // Подписываемся на push-уведомления
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array('ТВОЙ_PUBLIC_VAPID_KEY') // замени на свой ключ
        });

        // Отправляем подписку на сервер
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
            // Отправляем на сервер запрос на удаление
            await fetch('/api/push/unsubscribe', {  // Путь теперь /api/push/unsubscribe
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    endpoint: subscription.endpoint
                })
            });
            
            // Отписываемся локально
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
    // Получаем ID пользователя если он авторизован
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

    const response = await fetch('/api/push/subscribe', {  // Путь теперь /api/push/subscribe
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
    // Создаем временное уведомление
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

async function logout() {
    try {
        // Отписываемся от уведомлений при выходе
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
});