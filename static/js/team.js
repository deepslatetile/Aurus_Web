
let teamMembers = [];

async function loadTeamData() {
    try {
        const container = document.getElementById('teamContainer');
        container.innerHTML = `
            <div class="loading-container">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading team information...</p>
            </div>
        `;

        const response = await fetch('/api/get/about_us?group=team&active=true');
        if (!response.ok) {
            throw new Error('Failed to load team data');
        }

        teamMembers = await response.json();
        renderTeam();

    } catch (error) {
        console.error('Error loading team:', error);
        const container = document.getElementById('teamContainer');
        container.innerHTML = `
            <div class="no-results">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Unable to load team information. Please try again later.</p>
            </div>
        `;
    }
}

function renderTeam() {
    const container = document.getElementById('teamContainer');

    if (teamMembers.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <i class="fas fa-user-slash"></i>
                <p>No team members found.</p>
            </div>
        `;
        return;
    }

    const departmentFilter = document.getElementById('departmentFilter').value;
    const sortFilter = document.getElementById('sortFilter').value;

    let filteredMembers = [...teamMembers];

    if (departmentFilter !== 'all') {
        filteredMembers = filteredMembers.filter(member =>
            member.subgroup === departmentFilter
        );
    }

    filteredMembers.sort((a, b) => {
        if (sortFilter === 'name') {
            return a.name.localeCompare(b.name);
        } else if (sortFilter === 'experience') {
            return (b.years_experience || 0) - (a.years_experience || 0);
        } else if (sortFilter === 'position') {
            return (a.display_order || 0) - (b.display_order || 0);
        }
        return 0;
    });

    if (filteredMembers.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <p>No team members found matching your filters.</p>
                <button onclick="resetFilters()" class="btn-secondary" style="margin-top: 1rem;">
                    <i class="fas fa-redo"></i> Reset Filters
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = filteredMembers.map(member => `
        <div class="team-card">
            <div class="team-image">
                ${member.image ?
            `<img src="${member.image}" alt="${member.name}" loading="lazy">` :
            `<div class="placeholder"><i class="fas fa-user"></i></div>`
        }
            </div>
            <div class="team-content">
                <h3 class="team-title">${member.name}</h3>
                <div class="team-position">
                    <i class="fas fa-briefcase"></i>
                    <span>${member.position || 'Team Member'}</span>
                </div>
                ${member.role ? `
                    <div class="team-position" style="margin-top: 0.5rem;">
                        <i class="fas fa-star"></i>
                        <span>${member.role}</span>
                    </div>
                ` : ''}
                <div class="team-details">
                    <div class="detail-item">
                        <span class="label">Department:</span>
                        <span>${getDepartmentLabel(member.subgroup)}</span>
                    </div>
                    ${member.years_experience ? `
                        <div class="detail-item">
                            <span class="label">Experience:</span>
                            <span>${member.years_experience} years</span>
                        </div>
                    ` : ''}
                </div>
                ${member.description ? `
                    <div class="team-description">
                        ${member.description}
                    </div>
                ` : ''}
                ${member.link ? `
                    <a href="${member.link}" target="_blank" class="btn-secondary" style="margin-top: 1rem; width: 100%; text-align: center;">
                        <i class="fas fa-external-link-alt"></i> View Profile
                    </a>
                ` : ''}
            </div>
        </div>
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

function resetFilters() {
    document.getElementById('departmentFilter').value = 'all';
    document.getElementById('sortFilter').value = 'name';
    renderTeam();
}

document.addEventListener('DOMContentLoaded', function () {
    loadTeamData();
    document.getElementById('departmentFilter').addEventListener('change', renderTeam);
    document.getElementById('sortFilter').addEventListener('change', renderTeam);
    document.getElementById('resetFilters').addEventListener('click', resetFilters);
});
