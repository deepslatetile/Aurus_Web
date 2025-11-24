let currentPages = [];
let pageToDelete = null;

// Load pages based on filter
async function loadPages(state = '-1') {
    try {
        const container = document.getElementById('pagesList');
        container.innerHTML = '<div class="loading-text"><i class="fas fa-spinner fa-spin"></i> Loading pages...</div>';

        const response = await fetch(`/api/get/web_config/state/${state}`);
        if (!response.ok) throw new Error('Failed to load pages');

        currentPages = await response.json();
        renderPages();
    } catch (error) {
        console.error('Error loading pages:', error);
        showAlert('Error loading pages: ' + error.message, 'error');
    }
}

// Render pages list
function renderPages() {
    const container = document.getElementById('pagesList');

    if (!currentPages || currentPages.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <h3>No Pages Found</h3>
                <p>Create your first page to get started!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = currentPages.map(page => `
        <div class="page-item">
            <div class="page-info">
                <div class="page-name">${page.page_display}</div>
                <div class="page-details">
                    <span class="page-state ${page.state === 1 ? 'state-active' : 'state-inactive'}">
                        <i class="fas ${page.state === 1 ? 'fa-eye' : 'fa-eye-slash'}"></i>
                        ${page.state === 1 ? 'Visible' : 'Hidden'}
                    </span>
                    <span class="page-url">/${page.page_name}</span>
                </div>
            </div>
            <div class="page-actions">
                <button class="btn-icon btn-toggle" onclick="togglePageState(${page.id}, ${page.state})"
                        title="${page.state === 1 ? 'Hide from navigation' : 'Show in navigation'}">
                    <i class="fas ${page.state === 1 ? 'fa-eye-slash' : 'fa-eye'}"></i>
                    ${page.state === 1 ? 'Hide' : 'Show'}
                </button>
                <button class="btn-icon btn-edit" onclick="editPage(${page.id})" title="Edit">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-icon btn-delete" onclick="confirmDelete(${page.id}, '${page.page_display}')" title="Delete">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
}

// Toggle page state
async function togglePageState(pageId, currentState) {
    const newState = currentState === 1 ? 0 : 1;
    const action = newState === 1 ? 'shown' : 'hidden';

    try {
        const response = await fetch(`/api/put/web_config/${pageId}/${newState}`, {
            method: 'PUT'
        });

        if (response.ok) {
            showAlert(`Page ${action} in navigation successfully`, 'success');
            loadPages(document.getElementById('stateFilter').value);
        } else {
            throw new Error('Failed to update page state');
        }
    } catch (error) {
        console.error('Error toggling page state:', error);
        showAlert('Error updating page: ' + error.message, 'error');
    }
}

// Create new page
function createPage() {
    document.getElementById('modalTitle').textContent = 'Add New Page';
    document.getElementById('pageForm').reset();
    document.getElementById('pageId').value = '';
    document.getElementById('pageState').value = '1';
    showModal('pageModal');
}

// Edit existing page
async function editPage(pageId) {
    try {
        const response = await fetch(`/api/get/web_config/id/${pageId}`);
        if (!response.ok) throw new Error('Failed to load page');

        const page = await response.json();

        document.getElementById('modalTitle').textContent = 'Edit Page';
        document.getElementById('pageId').value = page.id;
        document.getElementById('pageName').value = page.page_name;
        document.getElementById('pageDisplay').value = page.page_display;
        document.getElementById('pageState').value = page.state.toString();

        showModal('pageModal');
    } catch (error) {
        console.error('Error loading page:', error);
        showAlert('Error loading page: ' + error.message, 'error');
    }
}

// Save page (create or update)
async function savePage(formData) {
    const pageId = document.getElementById('pageId').value;
    const isEdit = !!pageId;

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        const url = isEdit
                ? `/api/put/page_content/${formData.page_name}`
                : '/api/post/web_config/';

        const method = isEdit ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            showAlert(`Page ${isEdit ? 'updated' : 'created'} successfully`, 'success');
            hideModal('pageModal');
            loadPages(document.getElementById('stateFilter').value);
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save page');
        }
    } catch (error) {
        console.error('Error saving page:', error);
        showAlert('Error saving page: ' + error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-save"></i> Save Page';
    }
}

// Confirm deletion
function confirmDelete(pageId, pageName) {
    pageToDelete = pageId;
    document.getElementById('deletePageName').textContent = pageName;
    showModal('deleteModal');
}

// Delete page
async function deletePage() {
    if (!pageToDelete) return;

    const deleteBtn = document.getElementById('confirmDeleteBtn');
    deleteBtn.disabled = true;
    deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

    try {
        const response = await fetch(`/api/delete/web_config/${pageToDelete}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showAlert('Page deleted successfully', 'success');
            hideModal('deleteModal');
            loadPages(document.getElementById('stateFilter').value);
        } else {
            throw new Error('Failed to delete page');
        }
    } catch (error) {
        console.error('Error deleting page:', error);
        showAlert('Error deleting page: ' + error.message, 'error');
    } finally {
        pageToDelete = null;
        deleteBtn.disabled = false;
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Delete Page';
    }
}

// Modal functions
function showModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}

function hideModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Alert function
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
    }, 4000);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function () {
    // Load initial pages
    loadPages();

    // Setup filter change listener
    document.getElementById('stateFilter').addEventListener('change', function () {
        loadPages(this.value);
    });

    // Setup create button
    document.getElementById('createPageBtn').addEventListener('click', createPage);

    // Setup form submission
    document.getElementById('pageForm').addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = {
            page_name: document.getElementById('pageName').value.trim(),
            page_display: document.getElementById('pageDisplay').value.trim(),
            state: parseInt(document.getElementById('pageState').value)
        };

        // Basic validation
        if (!formData.page_name) {
            showAlert('Please enter a page URL', 'error');
            return;
        }

        if (!formData.page_display) {
            showAlert('Please enter a display name', 'error');
            return;
        }

        savePage(formData);
    });

    // Setup modal close buttons
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', function () {
            const modal = this.closest('.modal');
            hideModal(modal.id);
        });
    });

    // Setup cancel buttons
    document.getElementById('cancelBtn').addEventListener('click', function () {
        hideModal('pageModal');
    });

    document.getElementById('cancelDeleteBtn').addEventListener('click', function () {
        hideModal('deleteModal');
    });

    // Setup delete confirmation
    document.getElementById('confirmDeleteBtn').addEventListener('click', deletePage);

    // Close modal when clicking outside
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function (e) {
            if (e.target === this) {
                hideModal(this.id);
            }
        });
    });
});