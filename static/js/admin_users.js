
let currentPage = 1;
const perPage = 20;
let currentUserId = null;

document.addEventListener('DOMContentLoaded', function () {
    loadStats();
    loadUsers();
});

async function loadStats() {
    try {
        const response = await fetch('/admin/api/users/stats');
        if (!response.ok) {
            throw new Error('Failed to load statistics');
        }

        const stats = await response.json();
        displayStats(stats);

    } catch (error) {
        console.error('Error loading statistics:', error);
        document.getElementById('statsGrid').innerHTML = '<div class="alert alert-error">Error loading statistics</div>';
    }
}

function displayStats(stats) {
    const statsGrid = document.getElementById('statsGrid');

    statsGrid.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${stats.total_users}</div>
            <div class="stat-label">Total Users</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.active_users}</div>
            <div class="stat-label">Active Users</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.hq_users}</div>
            <div class="stat-label">HQ Users</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.staff_users}</div>
            <div class="stat-label">Staff Users</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.passenger_users}</div>
            <div class="stat-label">Passenger Users</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.total_miles}</div>
            <div class="stat-label">Total Miles</div>
        </div>
    `;
}

async function loadUsers(page = 1) {
    currentPage = page;
    const container = document.getElementById('usersContainer');
    container.innerHTML = '<div class="loading">Loading users...</div>';

    const search = document.getElementById('searchFilter').value;
    const group = document.getElementById('groupFilter').value;
    const status = document.getElementById('statusFilter').value;

    try {
        const params = new URLSearchParams({
            page: page,
            per_page: perPage,
            ...(search && { search: search }),
            ...(group && { group: group }),
            ...(status && { status: status })
        });

        const response = await fetch(`/admin/api/users?${params}`);
        if (!response.ok) {
            throw new Error('Failed to load users');
        }

        const data = await response.json();
        displayUsers(data);

    } catch (error) {
        console.error('Error loading users:', error);
        container.innerHTML = '<div class="alert alert-error">Error loading users: ' + error.message + '</div>';
    }
}

function displayUsers(data) {
    const container = document.getElementById('usersContainer');
    const pagination = document.getElementById('pagination');

    if (data.users.length === 0) {
        container.innerHTML = '<div class="loading">No users found</div>';
        pagination.innerHTML = '';
        return;
    }

    container.innerHTML = data.users.map(user => `
        <div class="user-item" onclick="openUserModal(${user.id})">
            <div class="user-header">
                <div class="user-name">${user.nickname}</div>
                <div class="user-id">ID: ${user.id}</div>
            </div>
            <div class="user-details">
                <div class="user-detail">
                    <span class="detail-label">Virtual ID:</span>
                    <span>${user.virtual_id || 'N/A'}</span>
                </div>
                <div class="user-detail">
                    <span class="detail-label">Group:</span>
                    <span class="user-group-${user.user_group.toLowerCase()}">${user.user_group}</span>
                </div>
                <div class="user-detail">
                    <span class="detail-label">Miles:</span>
                    <span>${user.miles}</span>
                </div>
                <div class="user-detail">
                    <span class="detail-label">Status:</span>
                    <span class="status-${user.status || 'active'}">${user.status || 'active'}</span>
                </div>
                <div class="user-detail">
                    <span class="detail-label">Created:</span>
                    <span>${new Date(user.created_at * 1000).toLocaleDateString()}</span>
                </div>
            </div>
        </div>
    `).join('');

    pagination.innerHTML = `
        <button onclick="loadUsers(${currentPage - 1})" ${currentPage <= 1 ? 'disabled' : ''}>
            <i class="fas fa-chevron-left"></i> Previous
        </button>
        <span class="pagination-info">
            Page ${currentPage} of ${data.total_pages}
        </span>
        <button onclick="loadUsers(${currentPage + 1})" ${currentPage >= data.total_pages ? 'disabled' : ''}>
            Next <i class="fas fa-chevron-right"></i>
        </button>
    `;
}

function clearFilters() {
    document.getElementById('searchFilter').value = '';
    document.getElementById('groupFilter').value = '';
    document.getElementById('statusFilter').value = '';
    loadUsers(1);
}

async function openUserModal(userId) {
    currentUserId = userId;
    const modal = document.getElementById('userModal');
    const modalBody = document.getElementById('modalBody');

    try {
        const response = await fetch(`/admin/api/users/${userId}`);
        if (!response.ok) {
            throw new Error('Failed to load user details');
        }

        const user = await response.json();
        displayUserModal(user);

    } catch (error) {
        console.error('Error loading user details:', error);
        alert('Error loading user details: ' + error.message);
    }
}

function displayUserModal(user) {
    const modalBody = document.getElementById('modalBody');

    modalBody.innerHTML = `
        <form id="userForm">
            <div class="form-group">
                <label for="userId">User ID:</label>
                <input type="text" id="userId" value="${user.id}" readonly>
            </div>

            <div class="form-group">
                <label for="nickname">Nickname:</label>
                <input type="text" id="nickname" name="nickname" value="${user.nickname}" required>
            </div>

            <div class="form-group">
                <label for="virtualId">Virtual ID:</label>
                <input type="number" id="virtualId" name="virtual_id" value="${user.virtual_id || ''}">
            </div>

            <div class="form-group">
                <label for="socialId">Social ID:</label>
                <input type="number" id="socialId" name="social_id" value="${user.social_id || ''}">
            </div>

            <div class="form-group">
                <label for="miles">Miles:</label>
                <input type="number" id="miles" name="miles" value="${user.miles}" required>
            </div>

            <div class="form-group">
                <label for="userGroup">User Group:</label>
                <select id="userGroup" name="user_group" required>
                    <option value="PAX" ${user.user_group === 'PAX' ? 'selected' : ''}>Passenger</option>
                    <option value="STF" ${user.user_group === 'STF' ? 'selected' : ''}>Staff</option>
                    <option value="HQ" ${user.user_group === 'HQ' ? 'selected' : ''}>HQ</option>
                </select>
            </div>

            <div class="form-group">
                <label for="subgroup">Subgroup:</label>
                <input type="text" id="subgroup" name="subgroup" value="${user.subgroup}" required>
            </div>

            <div class="form-group">
                <label for="link">Link:</label>
                <input type="text" id="link" name="link" value="${user.link || ''}">
            </div>

            <div class="form-group">
                <label for="status">Status:</label>
                <select id="status" name="status">
                    <option value="active" ${(user.status || 'active') === 'active' ? 'selected' : ''}>Active</option>
                    <option value="inactive" ${user.status === 'inactive' ? 'selected' : ''}>Inactive</option>
                </select>
            </div>

            <div class="form-group">
                <label for="metadata">Metadata:</label>
                <textarea id="metadata" name="metadata">${user.metadata || ''}</textarea>
            </div>

            <div class="form-group">
                <label for="pending">Pending:</label>
                <input type="text" id="pending" name="pending" value="${user.pending || ''}">
            </div>

            <div class="form-group">
                <label>Created:</label>
                <input type="text" value="${new Date(user.created_at * 1000).toLocaleString()}" readonly>
            </div>

            <div class="user-actions">
                <button type="button" class="delete-btn" onclick="deleteUser(${user.id})">
                    <i class="fas fa-trash"></i> Delete User
                </button>
                <button type="button" class="cancel-btn" onclick="closeModal()">Cancel</button>
                <button type="submit" class="save-btn">Save Changes</button>
            </div>
        </form>
    `;

    document.getElementById('userForm').addEventListener('submit', saveUserChanges);
    document.getElementById('userModal').style.display = 'block';
}

async function saveUserChanges(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        nickname: formData.get('nickname'),
        virtual_id: formData.get('virtual_id') ? parseInt(formData.get('virtual_id')) : null,
        social_id: formData.get('social_id') ? parseInt(formData.get('social_id')) : null,
        miles: parseInt(formData.get('miles')),
        user_group: formData.get('user_group'),
        subgroup: formData.get('subgroup'),
        link: formData.get('link'),
        status: formData.get('status'),
        metadata: formData.get('metadata'),
        pending: formData.get('pending')
    };

    try {
        const response = await fetch(`/admin/api/users/${currentUserId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error('Failed to update user');
        }

        closeModal();
        loadUsers(currentPage);
        loadStats();
        alert('User updated successfully!');

    } catch (error) {
        console.error('Error updating user:', error);
        alert('Error updating user: ' + error.message);
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/admin/api/users/${userId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete user');
        }

        closeModal();
        loadUsers(currentPage);
        loadStats();
        alert('User deleted successfully!');

    } catch (error) {
        console.error('Error deleting user:', error);
        alert('Error deleting user: ' + error.message);
    }
}

function showCreateUserModal() {
    document.getElementById('createUserModal').style.display = 'block';
}

function closeCreateUserModal() {
    document.getElementById('createUserModal').style.display = 'none';
    document.getElementById('createUserForm').reset();
}

async function createUser(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        nickname: formData.get('nickname'),
        password: formData.get('password'),
        user_group: formData.get('user_group'),
        subgroup: formData.get('subgroup'),
        virtual_id: formData.get('virtual_id') ? parseInt(formData.get('virtual_id')) : null,
        social_id: formData.get('social_id') ? parseInt(formData.get('social_id')) : null,
        status: formData.get('status')
    };

    try {
        const response = await fetch('/api/post/user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create user');
        }

        closeCreateUserModal();
        loadUsers(1);
        loadStats();
        alert('User created successfully!');

    } catch (error) {
        console.error('Error creating user:', error);
        alert('Error creating user: ' + error.message);
    }
}

function closeModal() {
    document.getElementById('userModal').style.display = 'none';
    currentUserId = null;
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('createUserForm').addEventListener('submit', createUser);

    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.onclick = function () {
            document.getElementById('userModal').style.display = 'none';
            document.getElementById('createUserModal').style.display = 'none';
            currentUserId = null;
        }
    });

    window.onclick = function (event) {
        if (event.target === document.getElementById('userModal')) {
            closeModal();
        }
        if (event.target === document.getElementById('createUserModal')) {
            closeCreateUserModal();
        }
    }
});
