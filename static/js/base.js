// static/js/base.js
async function loadNavigation() {
    try {
        const response = await fetch('/api/get/web_config/state/1');
        const pages = await response.json();

        const navMenu = document.getElementById('navMenu');
        const mobileDropdownMenu = document.getElementById('mobileDropdownMenu');
        
        // Очищаем меню
        navMenu.innerHTML = '';
        mobileDropdownMenu.innerHTML = '';

        // Создаем пункты для десктопного меню
        pages.forEach(page => {
            // Десктопное меню
            const desktopItem = document.createElement('li');
            desktopItem.className = 'nav-item';
            const desktopLink = document.createElement('a');
            desktopLink.href = `/${page.page_name}`;
            desktopLink.textContent = page.page_display;
            desktopItem.appendChild(desktopLink);
            navMenu.appendChild(desktopItem);

            // Мобильное меню
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
        // Fallback навигация
        const fallbackPages = [
            { page_name: '', page_display: 'Home' },
            { page_name: 'schedule', page_display: 'Schedule' }
        ];

        const navMenu = document.getElementById('navMenu');
        const mobileDropdownMenu = document.getElementById('mobileDropdownMenu');
        
        navMenu.innerHTML = '';
        mobileDropdownMenu.innerHTML = '';

        fallbackPages.forEach(page => {
            // Десктоп
            const desktopItem = document.createElement('li');
            desktopItem.className = 'nav-item';
            const desktopLink = document.createElement('a');
            desktopLink.href = `/${page.page_name}`;
            desktopLink.textContent = page.page_display;
            desktopItem.appendChild(desktopLink);
            navMenu.appendChild(desktopItem);

            // Мобильное
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
            // User is logged in
            const displayName = window.innerWidth < 480 ? 
                user.nickname.substring(0, 10) + (user.nickname.length > 10 ? '...' : '') : 
                user.nickname;

            document.getElementById('authButtons').innerHTML = `
                    <div class="user-info">
                        <div class="user-avatar">${user.nickname.charAt(0).toUpperCase()}</div>
                        <span>${displayName}</span>
                    </div>
                    <button class="logout-btn" onclick="logout()">
                        <i class="fas fa-sign-out-alt"></i> ${window.innerWidth < 480 ? '' : 'Logout'}
                    </button>
                `;
        } else {
            // User is not logged in
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

function toggleMobileMenu() {
    const mobileDropdown = document.getElementById('mobileDropdown');
    const toggleButton = document.querySelector('.mobile-menu-toggle');
    
    mobileDropdown.classList.toggle('active');
    
    // Меняем иконку
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

// Закрытие мобильного меню при клике вне его
document.addEventListener('click', function(event) {
    const mobileDropdown = document.getElementById('mobileDropdown');
    const toggleButton = document.querySelector('.mobile-menu-toggle');
    
    if (!mobileDropdown.contains(event.target) && !toggleButton.contains(event.target)) {
        closeMobileMenu();
    }
});

// Закрытие мобильного меню при ресайзе
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