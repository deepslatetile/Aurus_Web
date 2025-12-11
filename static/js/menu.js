
let allMeals = [];

document.addEventListener('DOMContentLoaded', function () {
    loadMenu();
});

async function loadMenu() {
    try {
        const response = await fetch('/api/get/all_meals');

        if (response.ok) {
            allMeals = await response.json();
            displayMenu(allMeals);
            updateFilters();
        } else {
            throw new Error('Failed to load menu');
        }

    } catch (error) {
        console.error('Error loading menu:', error);
        document.getElementById('menuLoading').innerHTML = '<div class="error"><i class="fas fa-exclamation-triangle"></i><p>Failed to load menu. Please try again later.</p></div>';
    }
}

function displayMenu(meals) {
    const menuLoading = document.getElementById('menuLoading');
    const menuItems = document.getElementById('menuItems');
    const noMeals = document.getElementById('noMeals');

    menuLoading.style.display = 'none';

    if (meals.length === 0) {
        noMeals.style.display = 'block';
        menuItems.style.display = 'none';
        return;
    }

    const groupedMeals = {};
    meals.forEach(meal => {
        if (!groupedMeals[meal.serve_time]) {
            groupedMeals[meal.serve_time] = [];
        }
        groupedMeals[meal.serve_time].push(meal);
    });

    let html = '';
    Object.keys(groupedMeals).forEach(time => {
        const timeMeals = groupedMeals[time];
        const timeDisplay = time.charAt(0).toUpperCase() + time.slice(1);

        html += '<div class="menu-category">';
        html += '<div class="category-header">';
        html += '<h2 class="category-title">' + timeDisplay + '</h2>';
        html += '</div>';
        html += '<div class="menu-items">';

        timeMeals.forEach(meal => {
            const imageHtml = meal.image ? '<img src="' + meal.image + '" alt="' + meal.name + '" onerror="this.style.display=\'none\'">' : '<div class="meal-image-placeholder"><i class="fas fa-utensils"></i></div>';

            html += '<div class="meal-card">';
            html += '<div class="meal-image">' + imageHtml + '</div>';
            html += '<div class="meal-content">';
            html += '<h3 class="meal-name">' + meal.name + '</h3>';
            html += '<span class="meal-class">' + meal.serve_class + '</span>';
            if (meal.description) {
                html += '<div class="meal-description">' + meal.description + '</div>';
            }
            html += '<div class="meal-time">' + timeDisplay + '</div>';
            html += '</div>';
            html += '</div>';
        });

        html += '</div>';
        html += '</div>';
    });

    menuItems.innerHTML = html;
    menuItems.style.display = 'block';
    noMeals.style.display = 'none';
}

function updateFilters() {
    const classSelect = document.getElementById('classSelect');
    const timeSelect = document.getElementById('timeSelect');

    const classes = [...new Set(allMeals.map(meal => meal.serve_class))];
    const times = [...new Set(allMeals.map(meal => meal.serve_time))];

    const classHierarchy = ["First", "Business", "Economy"];
    const orderedClasses = classHierarchy.filter(cls => classes.includes(cls));

    classSelect.innerHTML = '<option value="all">All Classes</option>';
    orderedClasses.forEach(className => {
        classSelect.innerHTML += '<option value="' + className + '">' + className + '</option>';
    });

    timeSelect.innerHTML = '<option value="all">All Times</option>';
    times.forEach(time => {
        const timeDisplay = time.charAt(0).toUpperCase() + time.slice(1);
        timeSelect.innerHTML += '<option value="' + time + '">' + timeDisplay + '</option>';
    });
}

function filterMenu() {
    const selectedClass = document.getElementById('classSelect').value;
    const selectedTime = document.getElementById('timeSelect').value;

    let filteredMeals = allMeals;

    const classHierarchy = ["First", "Business", "Economy"];

    if (selectedClass !== 'all') {
        const selectedIndex = classHierarchy.indexOf(selectedClass);
        const allowedClasses = classHierarchy.slice(selectedIndex);

        filteredMeals = filteredMeals.filter(meal =>
            allowedClasses.includes(meal.serve_class)
        );
    }

    if (selectedTime !== 'all') {
        filteredMeals = filteredMeals.filter(meal => meal.serve_time === selectedTime);
    }

    displayMenu(filteredMeals);
}
