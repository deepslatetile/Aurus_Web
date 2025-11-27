// Aviation Weather API base URL
const WEATHER_API_URL = 'https://aviationweather.gov/api/data/metar';

// Загрузка при старте
document.addEventListener('DOMContentLoaded', function() {
    // Обработчик Enter в поле ICAO
    document.getElementById('icaoCode').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            fetchWeather();
        }
    });

    // Обработчик Enter в поле множественных станций
    document.getElementById('multiStationsInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            fetchMultipleStationsData();
        }
    });
});

// Установка ICAO кода
function setICAO(code) {
    document.getElementById('icaoCode').value = code.toUpperCase();
    fetchWeather();
}

// Получение погоды для одной станции
async function fetchWeather() {
    const icaoCode = document.getElementById('icaoCode').value.trim().toUpperCase();

    if (!icaoCode) {
        showAlert('Please enter an ICAO code', 'error');
        return;
    }

    if (icaoCode.length !== 4) {
        showAlert('ICAO code must be 4 characters', 'error');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${WEATHER_API_URL}?ids=${icaoCode}&format=json`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (!data || data.length === 0) {
            showAlert(`No weather data found for ${icaoCode}`, 'warning');
            displayEmptyState();
            return;
        }

        displayWeatherData(data);
        showAlert(`Weather data loaded for ${icaoCode}`, 'success');

    } catch (error) {
        console.error('Error fetching weather:', error);
        showAlert(`Error loading weather data: ${error.message}`, 'error');
        displayEmptyState();
    } finally {
        showLoading(false);
    }
}

// Получение погоды для множественных станций
async function fetchMultipleStationsData() {
    const stationsInput = document.getElementById('multiStationsInput').value.trim().toUpperCase();

    if (!stationsInput) {
        showAlert('Please enter ICAO codes', 'error');
        return;
    }

    const stations = stationsInput.split(',').map(s => s.trim()).filter(s => s.length === 4);

    if (stations.length === 0) {
        showAlert('No valid ICAO codes found', 'error');
        return;
    }

    if (stations.length > 10) {
        showAlert('Maximum 10 stations allowed', 'warning');
        stations.splice(10);
    }

    showLoading(true);

    try {
        const stationsParam = stations.join(',');
        const response = await fetch(`${WEATHER_API_URL}?ids=${stationsParam}&format=json`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (!data || data.length === 0) {
            showAlert('No weather data found for the specified stations', 'warning');
            return;
        }

        displayWeatherData(data);
        showAlert(`Loaded data for ${data.length} station(s)`, 'success');

    } catch (error) {
        console.error('Error fetching multiple stations:', error);
        showAlert(`Error loading weather data: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Отображение данных о погоде
function displayWeatherData(weatherData) {
    const weatherCards = document.getElementById('weatherCards');
    const emptyState = document.getElementById('emptyState');

    if (!weatherData || weatherData.length === 0) {
        displayEmptyState();
        return;
    }

    weatherCards.innerHTML = '';
    emptyState.style.display = 'none';
    weatherCards.style.display = 'grid';

    weatherData.forEach(station => {
        const card = createWeatherCard(station);
        weatherCards.appendChild(card);
    });
}

// Создание карточки погоды
function createWeatherCard(station) {
    const card = document.createElement('div');
    card.className = 'weather-card';

    const observationTime = new Date(station.obsTime * 1000).toLocaleString();
    const temperature = station.temp !== undefined ? `${station.temp}°C` : 'N/A';
    const dewPoint = station.dewp !== undefined ? `${station.dewp}°C` : 'N/A';
    const wind = station.wdir !== undefined && station.wspd !== undefined
        ? `${station.wdir}° at ${station.wspd} kt`
        : 'N/A';
    const visibility = station.visib !== undefined ? `${station.visib} km` : 'N/A';
    const altimeter = station.altim !== undefined ? `${station.altim} hPa` : 'N/A';

    card.innerHTML = `
        <div class="weather-header">
            <div class="station-info">
                <h3>${station.icaoId}</h3>
                <p class="station-location">${station.name || 'Unknown Location'}</p>
                <p class="station-location">Observed: ${observationTime}</p>
            </div>
            <div class="flight-category ${station.fltCat ? station.fltCat.toLowerCase() : 'unknown'}">
                ${station.fltCat || 'UNKN'}
            </div>
        </div>
        
        <div class="weather-details">
            <div class="weather-item">
                <span class="weather-label">Temperature</span>
                <span class="weather-value">${temperature}</span>
            </div>
            <div class="weather-item">
                <span class="weather-label">Dew Point</span>
                <span class="weather-value">${dewPoint}</span>
            </div>
            <div class="weather-item">
                <span class="weather-label">Wind</span>
                <span class="weather-value">${wind}</span>
            </div>
            <div class="weather-item">
                <span class="weather-label">Visibility</span>
                <span class="weather-value">${visibility}</span>
            </div>
            <div class="weather-item">
                <span class="weather-label">Altimeter</span>
                <span class="weather-value">${altimeter}</span>
            </div>
            <div class="weather-item">
                <span class="weather-label">Weather</span>
                <span class="weather-value">${station.wxString || 'N/A'}</span>
            </div>
        </div>
        
        ${station.rawOb ? `
        <div class="weather-raw">
            <p class="raw-metar">${station.rawOb}</p>
        </div>
        ` : ''}
        
        ${station.clouds && station.clouds.length > 0 ? `
        <div class="weather-item">
            <span class="weather-label">Clouds</span>
            <span class="weather-value">
                ${station.clouds.map(cloud => `${cloud.cover} at ${cloud.base} ft`).join(', ')}
            </span>
        </div>
        ` : ''}
    `;

    return card;
}

// Показать/скрыть загрузку
function showLoading(show) {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const weatherCards = document.getElementById('weatherCards');

    if (show) {
        loadingSpinner.style.display = 'block';
        weatherCards.style.display = 'none';
    } else {
        loadingSpinner.style.display = 'none';
        weatherCards.style.display = 'grid';
    }
}

// Показать пустое состояние
function displayEmptyState() {
    const emptyState = document.getElementById('emptyState');
    const weatherCards = document.getElementById('weatherCards');

    emptyState.style.display = 'block';
    weatherCards.style.display = 'none';
}

// Показать уведомление
function showAlert(message, type) {
    const alert = document.getElementById('alertMessage');
    alert.textContent = message;
    alert.className = `alert-message alert-${type}`;
    alert.style.display = 'block';

    setTimeout(() => {
        alert.style.display = 'none';
    }, 5000);
}

// Модальное окно для множественных станций
function fetchMultipleStations() {
    document.getElementById('multiStationModal').style.display = 'flex';
}

function closeMultiStationModal() {
    document.getElementById('multiStationModal').style.display = 'none';
}

// Закрытие модального окна при клике вне его
document.addEventListener('click', function(event) {
    const modal = document.getElementById('multiStationModal');
    if (event.target === modal) {
        closeMultiStationModal();
    }
});

// Автозагрузка погоды для UNKL при загрузке страницы (опционально)
// setTimeout(() => fetchWeather(), 1000);