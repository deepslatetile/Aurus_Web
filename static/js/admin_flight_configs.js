
let currentConfigs = [];
let configToDelete = null;
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', function () {
    loadAllConfigs();
    setupSearch();
    setupTypeFilter();
    setupConfigTypeHandler();
});

function setupConfigTypeHandler() {
    const configTypeSelect = document.getElementById('configType');
    configTypeSelect.addEventListener('change', function () {
        const boardingStyleFields = document.getElementById('boardingStyleFields');
        if (this.value === 'boarding_style') {
            boardingStyleFields.style.display = 'block';
            document.getElementById('configData').value = JSON.stringify({
                "draw_function": "default",
                "background_image": "",
                "background_url": "",
                "font_size": 32,
                "font_family": "kja.ttf"
            }, null, 2);
        } else {
            boardingStyleFields.style.display = 'none';
            document.getElementById('configData').value = '{}';
        }
    });

    const drawFunctionSelect = document.getElementById('drawFunction');
    drawFunctionSelect.addEventListener('change', function () {
        const customFunctionGroup = document.getElementById('customFunctionGroup');
        if (this.value === 'custom') {
            customFunctionGroup.style.display = 'block';
        } else {
            customFunctionGroup.style.display = 'none';
        }
    });
}

async function loadAllConfigs() {
    const configsGrid = document.getElementById('configsGrid');
    configsGrid.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Loading flight configs...</p></div>';

    try {
        const types = ['cabin_layout', 'service', 'boarding_style'];
        let allConfigs = [];

        for (const type of types) {
            const response = await fetch(`/api/get/flight_configs/${type}`);

            if (response.ok) {
                const result = await response.json();
                if (result.success && result.configs) {
                    allConfigs = allConfigs.concat(result.configs);
                }
            }
        }

        currentConfigs = allConfigs;
        displayConfigs(currentConfigs);

    } catch (error) {
        console.error('Error loading configs:', error);
        configsGrid.innerHTML = '<div class="error">Failed to load flight configs. Please try again.</div>';
    }
}

function displayConfigs(configs) {
    const configsGrid = document.getElementById('configsGrid');

    if (configs.length === 0) {
        configsGrid.innerHTML = `
        <div class="no-configs">
            <i class="fas fa-cogs" style="font-size: 3rem; margin-bottom: 1rem;"></i>
            <h3>No flight configs found</h3>
            <p>Create your first flight configuration to get started</p>
        </div>
    `;
        return;
    }

    let html = '';
    configs.forEach(config => {
        const description = config.description ? `<div class="config-description">${config.description}</div>` : '';

        let dataDisplay = JSON.stringify(config.data, null, 2);
        if (config.type === 'boarding_style') {
            const styleInfo = [];
            if (config.data.draw_function) styleInfo.push(`Function: ${config.data.draw_function}`);
            if (config.data.background_image) styleInfo.push(`BG Image: ${config.data.background_image}`);
            if (config.data.background_url) styleInfo.push(`BG URL: ${config.data.background_url}`);

            if (styleInfo.length > 0) {
                dataDisplay = styleInfo.join('\n') + '\n\n' + dataDisplay;
            }
        }

        html += `
    <div class="config-card">
        <div class="config-header">
            <h3 class="config-name">${config.name}</h3>
            <span class="config-type">${config.type}</span>
        </div>
        ${description}
        <div class="config-data">
            <pre>${dataDisplay}</pre>
        </div>
        <div class="config-footer">
            <div class="config-meta">
                Updated: ${formatTimestamp(config.updated_at)}
            </div>
            <div class="config-actions">
                <button class="btn-edit" onclick="editConfig(${config.id})">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-delete" onclick="showDeleteModal(${config.id}, '${escapeString(config.name)}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    </div>
    `;
    });

    configsGrid.innerHTML = html;
}

function escapeString(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '\\"');
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', function () {
        filterConfigs();
    });
}

function setupTypeFilter() {
    const typeButtons = document.querySelectorAll('.type-btn');
    typeButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            typeButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentFilter = this.dataset.type;
            filterConfigs();
        });
    });
}

function filterConfigs() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();

    let filteredConfigs = currentConfigs;

    if (currentFilter !== 'all') {
        filteredConfigs = filteredConfigs.filter(config => config.type === currentFilter);
    }

    if (searchTerm) {
        filteredConfigs = filteredConfigs.filter(config =>
            config.name.toLowerCase().includes(searchTerm) ||
            config.type.toLowerCase().includes(searchTerm) ||
            (config.description && config.description.toLowerCase().includes(searchTerm)) ||
            JSON.stringify(config.data).toLowerCase().includes(searchTerm)
        );
    }

    displayConfigs(filteredConfigs);
}

function showCreateModal() {
    document.getElementById('modalTitle').textContent = 'Create Flight Config';
    document.getElementById('configForm').reset();
    document.getElementById('configId').value = '';
    document.getElementById('configType').disabled = false;
    document.getElementById('boardingStyleFields').style.display = 'none';
    document.getElementById('customFunctionGroup').style.display = 'none';
    document.getElementById('configModal').style.display = 'block';
}

function editConfig(configId) {
    const config = currentConfigs.find(c => c.id === configId);
    if (!config) return;

    document.getElementById('modalTitle').textContent = 'Edit Flight Config';
    document.getElementById('configId').value = config.id;
    document.getElementById('configName').value = config.name;
    document.getElementById('configType').value = config.type;
    document.getElementById('configDescription').value = config.description || '';
    document.getElementById('configData').value = JSON.stringify(config.data, null, 2);
    document.getElementById('configType').disabled = true;

    const boardingStyleFields = document.getElementById('boardingStyleFields');
    const customFunctionGroup = document.getElementById('customFunctionGroup');
    if (config.type === 'boarding_style') {
        boardingStyleFields.style.display = 'block';

        const drawFunction = config.data.draw_function || 'default';
        if (drawFunction === 'default') {
            document.getElementById('drawFunction').value = 'default';
            customFunctionGroup.style.display = 'none';
        } else {
            const drawFunctionSelect = document.getElementById('drawFunction');
            let isKnownFunction = false;
            for (let option of drawFunctionSelect.options) {
                if (option.value === drawFunction) {
                    isKnownFunction = true;
                    break;
                }
            }

            if (isKnownFunction) {
                document.getElementById('drawFunction').value = drawFunction;
                customFunctionGroup.style.display = 'none';
            } else {
                document.getElementById('drawFunction').value = 'custom';
                document.getElementById('customFunction').value = drawFunction;
                customFunctionGroup.style.display = 'block';
            }
        }

        if (config.data.background_image) {
            document.getElementById('backgroundImage').value = config.data.background_image;
        }
        if (config.data.background_url) {
            document.getElementById('backgroundUrl').value = config.data.background_url;
        }
    } else {
        boardingStyleFields.style.display = 'none';
        customFunctionGroup.style.display = 'none';
    }

    document.getElementById('configModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('configModal').style.display = 'none';
}

function showDeleteModal(configId, configName) {
    configToDelete = configId;
    document.getElementById('deleteConfigName').textContent = configName;
    document.getElementById('deleteModal').style.display = 'block';
}

function closeDeleteModal() {
    configToDelete = null;
    document.getElementById('deleteModal').style.display = 'none';
}

async function saveConfig() {
    const saveBtn = document.getElementById('saveConfigBtn');
    const configId = document.getElementById('configId').value;
    const isEdit = !!configId;

    const name = document.getElementById('configName').value.trim();
    const type = document.getElementById('configType').value;
    const data = document.getElementById('configData').value.trim();
    const description = document.getElementById('configDescription').value.trim();

    if (!name || !type || !data) {
        alert('Please fill in all required fields');
        return;
    }

    let parsedData;
    try {
        parsedData = JSON.parse(data);
    } catch (e) {
        alert('Invalid JSON data. Please check your JSON syntax.');
        return;
    }

    if (type === 'boarding_style') {
        const drawFunction = document.getElementById('drawFunction').value;
        const backgroundImage = document.getElementById('backgroundImage').value.trim();
        const backgroundUrl = document.getElementById('backgroundUrl').value.trim();
        const customFunction = document.getElementById('customFunction').value.trim();

        if (!drawFunction) {
            alert('Please select a draw function for boarding style');
            return;
        }

        parsedData.draw_function = drawFunction === 'custom' ? customFunction : drawFunction;
        if (backgroundImage) parsedData.background_image = backgroundImage;
        if (backgroundUrl) parsedData.background_url = backgroundUrl;

        if (drawFunction === 'custom' && !customFunction) {
            alert('Please enter custom function name');
            return;
        }
    }

    const configData = {
        name: name,
        type: type,
        data: parsedData,
        description: description
    };

    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        let url, method;

        if (isEdit) {
            url = `/api/put/flight_config/${configId}`;
            method = 'PUT';
        } else {
            url = '/api/post/flight_config';
            method = 'POST';
        }

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(configData)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to save config');
        }

        closeModal();
        await loadAllConfigs();
        showNotification(`Config ${isEdit ? 'updated' : 'created'} successfully!`, 'success');

    } catch (error) {
        console.error('Error saving config:', error);
        alert('Failed to save config: ' + error.message);
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Config';
    }
}

async function confirmDelete() {
    if (!configToDelete) return;

    const deleteBtn = document.querySelector('#deleteModal .btn-danger');
    deleteBtn.disabled = true;
    deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

    try {
        const response = await fetch(`/api/delete/flight_config/${configToDelete}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to delete config');
        }

        closeDeleteModal();
        await loadAllConfigs();
        showNotification('Config deleted successfully!', 'success');

    } catch (error) {
        console.error('Error deleting config:', error);
        alert('Failed to delete config: ' + error.message);
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Delete';
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
    <div class="notification-content">
        <i class="fas fa-${type === 'success' ? 'check' : 'exclamation'}-circle"></i>
        <span>${message}</span>
    </div>
`;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

window.onclick = function (event) {
    const modal = document.getElementById('configModal');
    const deleteModal = document.getElementById('deleteModal');

    if (event.target === modal) {
        closeModal();
    }
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
}

document.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && document.getElementById('configModal').style.display === 'block') {
        event.preventDefault();
        saveConfig();
    }
});
