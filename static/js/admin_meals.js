
let currentMeals = [];
let mealToDelete = null;

document.addEventListener('DOMContentLoaded', function () {
    loadAllMeals();
    setupSearch();
    setupMealForm();
});

async function loadAllMeals() {
    const mealsGrid = document.getElementById('mealsGrid');
    mealsGrid.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Loading meals...</p></div>';

    try {
        const response = await fetch('/api/get/all_meals');
        if (response.ok) {
            currentMeals = await response.json();
            displayMeals(currentMeals);
            updateFilters();
        } else {
            throw new Error('Failed to load meals');
        }

    } catch (error) {
        console.error('Error loading meals:', error);
        mealsGrid.innerHTML = '<div class="error">Failed to load meals. Please try again.</div>';
    }
}

function displayMeals(meals) {
    const mealsGrid = document.getElementById('mealsGrid');

    if (meals.length === 0) {
        mealsGrid.innerHTML = '<div class="no-meals"><i class="fas fa-utensils"></i><h3>No meals found</h3><p>Create your first meal to get started</p></div>';
        return;
    }

    let html = '';
    meals.forEach(meal => {
        const imageHtml = meal.image ? '<img src="' + meal.image + '" alt="' + meal.name + '" onerror="this.style.display=\'none\'">' : '<div class="meal-image-placeholder"><i class="fas fa-utensils"></i></div>';

        html += '<div class="meal-card" data-class="' + meal.serve_class + '" data-time="' + meal.serve_time + '">';
        html += '<div class="meal-header">';
        html += '<h3 class="meal-name">' + meal.name + '</h3>';
        html += '<span class="meal-class">' + meal.serve_class + '</span>';
        html += '</div>';
        html += '<div class="meal-time">' + meal.serve_time + '</div>';
        if (meal.description) {
            html += '<div class="meal-description">' + meal.description + '</div>';
        }
        html += '<div class="meal-image">' + imageHtml + '</div>';
        html += '<div class="meal-actions">';
        html += '<button class="btn-edit" onclick="editMeal(' + meal.id + ')"><i class="fas fa-edit"></i> Edit</button>';
        html += '<button class="btn-delete" onclick="showDeleteModal(' + meal.id + ', \'' + escapeString(meal.name) + '\')"><i class="fas fa-trash"></i> Delete</button>';
        html += '</div>';
        html += '</div>';
    });

    mealsGrid.innerHTML = html;
}

function updateFilters() {
    const classFilter = document.getElementById('classFilter');
    const timeFilter = document.getElementById('timeFilter');

    const classes = [...new Set(currentMeals.map(meal => meal.serve_class))];
    const times = [...new Set(currentMeals.map(meal => meal.serve_time))];

    classFilter.innerHTML = '<option value="">All Classes</option>';
    classes.forEach(className => {
        classFilter.innerHTML += '<option value="' + className + '">' + className + '</option>';
    });

    timeFilter.innerHTML = '<option value="">All Times</option>';
    times.forEach(time => {
        timeFilter.innerHTML += '<option value="' + time + '">' + time + '</option>';
    });
}

function escapeString(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '\\"');
}

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', function () {
        filterMeals();
    });
}

function filterMeals() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const classFilter = document.getElementById('classFilter').value;
    const timeFilter = document.getElementById('timeFilter').value;

    let filteredMeals = currentMeals;

    if (classFilter) {
        filteredMeals = filteredMeals.filter(meal => meal.serve_class === classFilter);
    }

    if (timeFilter) {
        filteredMeals = filteredMeals.filter(meal => meal.serve_time === timeFilter);
    }

    if (searchTerm) {
        filteredMeals = filteredMeals.filter(meal =>
            meal.name.toLowerCase().includes(searchTerm) ||
            (meal.description && meal.description.toLowerCase().includes(searchTerm)) ||
            meal.serve_class.toLowerCase().includes(searchTerm) ||
            meal.serve_time.toLowerCase().includes(searchTerm)
        );
    }

    displayMeals(filteredMeals);
}

function setupMealForm() {
    const form = document.getElementById('mealFormElement');
    form.addEventListener('submit', saveMeal);
}

function showAddMealForm() {
    document.getElementById('formTitle').textContent = 'Add New Meal';
    document.getElementById('mealFormElement').reset();
    document.getElementById('mealId').value = '';
    document.getElementById('mealForm').style.display = 'block';
    document.getElementById('mealForm').scrollIntoView({ behavior: 'smooth' });
}

function hideMealForm() {
    document.getElementById('mealForm').style.display = 'none';
}

async function editMeal(mealId) {
    const meal = currentMeals.find(m => m.id === mealId);
    if (!meal) return;

    document.getElementById('formTitle').textContent = 'Edit Meal';
    document.getElementById('mealId').value = meal.id;
    document.getElementById('serve_class').value = meal.serve_class;
    document.getElementById('serve_time').value = meal.serve_time;
    document.getElementById('name').value = meal.name;
    document.getElementById('description').value = meal.description || '';
    document.getElementById('image').value = meal.image || '';
    document.getElementById('mealForm').style.display = 'block';
    document.getElementById('mealForm').scrollIntoView({ behavior: 'smooth' });
}

async function saveMeal(event) {
    event.preventDefault();

    const mealId = document.getElementById('mealId').value;
    const isEdit = !!mealId;

    const mealData = {
        serve_class: document.getElementById('serve_class').value.trim(),
        serve_time: document.getElementById('serve_time').value.trim(),
        name: document.getElementById('name').value.trim(),
        description: document.getElementById('description').value.trim(),
        image: document.getElementById('image').value.trim() || null
    };

    if (!mealData.serve_class || !mealData.serve_time || !mealData.name) {
        alert('Please fill in all required fields');
        return;
    }

    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    submitBtn.disabled = true;

    try {
        const response = await fetch('/api/post/meal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(mealData)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to save meal');
        }

        hideMealForm();
        await loadAllMeals();
        showNotification('Meal ' + (isEdit ? 'updated' : 'created') + ' successfully!', 'success');

    } catch (error) {
        console.error('Error saving meal:', error);
        alert('Failed to save meal: ' + error.message);
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

function showDeleteModal(mealId, mealName) {
    mealToDelete = mealId;
    document.getElementById('deleteMealName').textContent = mealName;
    document.getElementById('deleteModal').style.display = 'block';
}

function closeDeleteModal() {
    mealToDelete = null;
    document.getElementById('deleteModal').style.display = 'none';
}

async function confirmDelete() {
    if (!mealToDelete) return;

    const deleteBtn = document.querySelector('#deleteModal .btn-danger');
    deleteBtn.disabled = true;
    deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

    try {
        const response = await fetch('/api/delete/meal/' + mealToDelete, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to delete meal');
        }

        closeDeleteModal();
        await loadAllMeals();
        showNotification('Meal deleted successfully!', 'success');

    } catch (error) {
        console.error('Error deleting meal:', error);
        alert('Failed to delete meal: ' + error.message);
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Delete';
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = 'notification notification-' + type;
    notification.innerHTML = '<div class="notification-content"><i class="fas fa-' + (type === 'success' ? 'check' : 'exclamation') + '-circle"></i><span>' + message + '</span></div>';

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
    const modal = document.getElementById('deleteModal');
    if (event.target === modal) {
        closeDeleteModal();
    }
}
