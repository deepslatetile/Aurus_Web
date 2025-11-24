document.addEventListener('DOMContentLoaded', function() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const authForms = document.querySelectorAll('.auth-form');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');

            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            authForms.forEach(form => {
                form.classList.remove('active');
                if (form.id === targetTab + 'Form') {
                    form.classList.add('active');
                }
            });
        });
    });

    document.getElementById('loginForm').addEventListener('submit', function(e) {
        e.preventDefault();
        handleLogin();
    });

    document.getElementById('registerForm').addEventListener('submit', function(e) {
        e.preventDefault();
        handleRegister();
    });
});

async function handleLogin() {
    const formData = {
        username: document.getElementById('loginUsername').value,
        password: document.getElementById('loginPassword').value
    };

    const submitBtn = document.querySelector('#loginForm .auth-btn');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
    submitBtn.disabled = true;

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
            credentials: 'include'  // Важно для работы с сессиями!
        });

        const result = await response.json();

        if (response.ok) {
            // Успешный логин
            showMessage('Login successful! Redirecting...', 'success');
            
            // Проверяем параметр redirect в URL
            const urlParams = new URLSearchParams(window.location.search);
            const redirectUrl = urlParams.get('redirect');

            setTimeout(() => {
                if (redirectUrl) {
                    window.location.href = redirectUrl;
                } else {
                    window.location.href = '/';
                }
            }, 1000);
        } else {
            // Ошибка логина
            showMessage('Login failed: ' + (result.error || 'Invalid credentials'), 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('Login failed. Please try again.', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

async function handleRegister() {
    const formData = {
        nickname: document.getElementById('regNickname').value,
        password: document.getElementById('regPassword').value,
        user_group: 'PAX',
        subgroup: ''
    };

    // Валидация пароля
    if (formData.password !== document.getElementById('regConfirmPassword').value) {
        showMessage('Passwords do not match!', 'error');
        return;
    }

    if (formData.password.length < 6) {
        showMessage('Password must be at least 6 characters long!', 'error');
        return;
    }

    const submitBtn = document.querySelector('#registerForm .auth-btn');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
    submitBtn.disabled = true;

    try {
        const response = await fetch('/api/auth/post/user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            // Успешная регистрация
            showMessage('Registration successful! Please login with your new account.', 'success');
            
            // Переключаем на вкладку логина
            setTimeout(() => {
                document.querySelector('[data-tab="login"]').click();
                // Auto-fill username with nickname
                document.getElementById('loginUsername').value = formData.nickname;
                // Clear registration form
                document.getElementById('regNickname').value = '';
                document.getElementById('regPassword').value = '';
                document.getElementById('regConfirmPassword').value = '';
            }, 1500);
        } else {
            // Ошибка регистрации
            showMessage('Registration failed: ' + (result.error || 'Please try again'), 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showMessage('Registration failed. Please try again.', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Функция для показа сообщений
function showMessage(message, type) {
    // Удаляем существующие сообщения
    const existingMessage = document.querySelector('.auth-message');
    if (existingMessage) {
        existingMessage.remove();
    }

    // Создаем новое сообщение
    const messageDiv = document.createElement('div');
    messageDiv.className = `auth-message ${type}`;
    messageDiv.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        ${message}
    `;

    // Вставляем после auth-card
    const authCard = document.querySelector('.auth-card');
    authCard.parentNode.insertBefore(messageDiv, authCard);

    // Автоматически удаляем через 5 секунд
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

// Добавляем CSS для сообщений
const style = document.createElement('style');
style.textContent = `
    .auth-message {
        padding: 12px 16px;
        margin: 16px 0;
        border-radius: 8px;
        font-weight: 500;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        animation: slideDown 0.3s ease;
    }
    .auth-message.success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .auth-message.error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    .auth-message i {
        font-size: 16px;
    }
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .auth-btn:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }
    .fa-spin {
        animation: fa-spin 1s infinite linear;
    }
    @keyframes fa-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);