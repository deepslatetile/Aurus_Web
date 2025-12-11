let teamData = [];
let currentMemberId = null;

const modal = document.getElementById('memberModal');
const modalTitle = document.getElementById('modalTitle');
const memberForm = document.getElementById('memberForm');
const closeBtn = document.querySelector('.close');
const cancelBtn = document.getElementById('cancelMemberBtn');

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

async function loadTeamData() {
    try {
        const response = await fetch('/api/get/about_us?group=team');
        if (!response.ok) throw new Error('Failed to load team data');

        teamData = await response.json();
        renderTeamTable();

    } catch (error) {
        console.error('Error loading team:', error);
        showAlert('Failed to load team data: ' + error.message, 'error');
    }
}

function renderTeamTable() {
    const tbody = document.getElementById('teamTableBody');

    if (teamData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="loading-cell">
                    <i class="fas fa-user-slash"></i>
                    <p>No team members found. Add your first team member!</p>
                </td>
            </tr>
        `;
        return;
    }

    teamData.sort((a, b) => (a.display_order || 0) - (b.display_order || 0));

    tbody.innerHTML = teamData.map(member => `
        <tr>
            <td>
                <div style="display: flex; align-items: center; gap: 10px;">
                    ${member.image ?
            `<img src="${member.image}" alt="${member.name}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;">` :
            `<div style="width: 40px; height: 40px; border-radius: 50%; background: #2d5cc4; display: flex; align-items: center; justify-content: center;">
                            <i class="fas fa-user" style="color: #8fa3d8;"></i>
                        </div>`
        }
                    <span>${member.name}</span>
                </div>
            </td>
            <td>${member.position || 'N/A'}</td>
            <td>${getDepartmentLabel(member.subgroup)}</td>
            <td>${member.years_experience ? member.years_experience + ' years' : 'N/A'}</td>
            <td>
                <span class="status-badge ${member.is_active ? 'badge-active' : 'badge-inactive'}">
                    ${member.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <div class="action-buttons">
                    <button onclick="editMember(${member.id})" class="btn-small btn-edit">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button onclick="toggleMemberStatus(${member.id}, ${member.is_active})" 
                            class="btn-small btn-toggle ${member.is_active ? '' : 'inactive'}">
                        <i class="fas fa-power-off"></i> ${member.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button onclick="deleteMember(${member.id})" class="btn-small btn-delete">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function getDepartmentLabel(department) {
    const departments = {
        'pilots': 'Flight Crew',
        'cabin': 'Cabin Crew',
        'operations': 'Operations',
        'maintenance': 'Maintenance',
        'management': 'Management',
        'support': 'Support Staff'
    };
    return departments[department] || department;
}

function openModal(isEdit = false) {
    modal.style.display = 'flex';
    modalTitle.textContent = isEdit ? 'Edit Team Member' : 'Add New Team Member';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    modal.style.display = 'none';
    currentMemberId = null;
    memberForm.reset();
    document.body.style.overflow = 'auto';
}

function editMember(id) {
    const member = teamData.find(m => m.id === id);
    if (!member) return;

    currentMemberId = id;

    document.getElementById('memberId').value = member.id;
    document.getElementById('memberName').value = member.name || '';
    document.getElementById('memberPosition').value = member.position || '';
    document.getElementById('memberRole').value = member.role || '';
    document.getElementById('memberDepartment').value = member.subgroup || '';
    document.getElementById('memberExperience').value = member.years_experience || '';
    document.getElementById('memberOrder').value = member.display_order || 0;
    document.getElementById('memberDescription').value = member.description || '';
    document.getElementById('memberImage').value = member.image || '';
    document.getElementById('memberLink').value = member.link || '';
    document.getElementById('memberStatus').value = member.is_active ? 'true' : 'false';

    openModal(true);
}

async function toggleMemberStatus(id, currentStatus) {
    if (!confirm(`Are you sure you want to ${currentStatus ? 'deactivate' : 'activate'} this team member?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/put/about_us/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: !currentStatus })
        });

        if (response.ok) {
            showAlert(`Team member ${currentStatus ? 'deactivated' : 'activated'} successfully!`, 'success');
            loadTeamData();
        } else {
            const error = await response.json();
            showAlert('Failed to update team member: ' + (error.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error updating team member:', error);
        showAlert('Error updating team member: ' + error.message, 'error');
    }
}

async function deleteMember(id) {
    if (!confirm('Are you sure you want to delete this team member? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/delete/about_us/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('Team member deleted successfully!', 'success');
            loadTeamData();
        } else {
            const error = await response.json();
            showAlert('Failed to delete team member: ' + (error.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error deleting team member:', error);
        showAlert('Error deleting team member: ' + error.message, 'error');
    }
}

memberForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = Object.fromEntries(formData);

    if (data.years_experience) data.years_experience = parseInt(data.years_experience);
    if (data.display_order) data.display_order = parseInt(data.display_order);
    data.is_active = data.is_active === 'true';

    const submitBtn = this.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        let response;
        if (currentMemberId) {
            response = await fetch(`/api/put/about_us/${currentMemberId}`, {
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
            showAlert(`Team member ${currentMemberId ? 'updated' : 'created'} successfully!`, 'success');
            closeModal();
            loadTeamData();
        } else {
            const error = await response.json();
            showAlert('Failed to save team member: ' + (error.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error saving team member:', error);
        showAlert('Error saving team member: ' + error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Save Member';
    }
});

document.addEventListener('DOMContentLoaded', function () {
    loadTeamData();

    document.getElementById('addMemberBtn').addEventListener('click', () => openModal(false));
    document.getElementById('refreshBtn').addEventListener('click', loadTeamData);

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    window.addEventListener('click', function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });
});
