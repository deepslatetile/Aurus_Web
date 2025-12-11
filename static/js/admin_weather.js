
const WEATHER_API_BASE = '/admin/api/get/weather';

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('icaoCode').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            fetchWeather();
        }
    });

    document.getElementById('multiStationsInput').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            fetchMultipleStationsData();
        }
    });
});

function setICAO(code) {
    document.getElementById('icaoCode').value = code.toUpperCase();
    fetchWeather();
}

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
        const response = await fetch(`${WEATHER_API_BASE}/${icaoCode}`);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.results === 0) {
            showAlert(`No weather data found for ${icaoCode}`, 'warning');
            displayEmptyState();
            return;
        }

        displayWeatherData(data.data, data.cache_info);
        showAlert(`Weather data loaded for ${icaoCode}${data.cache_info.from_cache ? ' (from cache)' : ''}`, 'success');

    } catch (error) {
        console.error('Error fetching weather:', error);
        showAlert(`Error loading weather data: ${error.message}`, 'error');
        displayEmptyState();
    } finally {
        showLoading(false);
    }
}

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
        const response = await fetch(`${WEATHER_API_BASE}/multiple?stations=${stationsParam}`);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.results === 0) {
            showAlert('No weather data found for the specified stations', 'warning');
            return;
        }

        displayWeatherData(data.data, data.cache_info);

        const cacheInfo = data.cache_info;
        const cacheMessage = cacheInfo ?
            ` (${cacheInfo.from_cache} from cache, ${cacheInfo.from_api} from API)` : '';

        showAlert(`Loaded data for ${data.results} station(s)${cacheMessage}`, 'success');

    } catch (error) {
        console.error('Error fetching multiple stations:', error);
        showAlert(`Error loading weather data: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

function displayWeatherData(weatherData, cacheInfo = null) {
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
        const stationCacheInfo = station.cache_info || cacheInfo;
        const card = createWeatherCard(station, stationCacheInfo);
        weatherCards.appendChild(card);
    });
}

function createWeatherCard(station, cacheInfo = null) {
    const card = document.createElement('div');
    card.className = 'weather-card';

    const observationTime = new Date(station.observed).toLocaleString();
    const temperature = station.temperature ? `${station.temperature.celsius}°C` : 'N/A';
    const dewPoint = station.dewpoint ? `${station.dewpoint.celsius}°C` : 'N/A';
    const wind = station.wind ? `${station.wind.degrees}° at ${station.wind.speed_kts} kt` : 'N/A';
    const visibility = station.visibility ? `${station.visibility.meters_text} m` : 'N/A';
    const altimeter = station.barometer ? `${station.barometer.hpa} hPa` : 'N/A';
    const humidity = station.humidity ? `${station.humidity.percent}%` : 'N/A';

    card.innerHTML = `
        <div class="weather-header">
            <div class="station-info">
                <h3>${station.icao}</h3>
                <p class="station-location">${station.station?.name || 'Unknown Location'}</p>
                <p class="station-location">Observed: ${observationTime}</p>
                ${cacheInfo && cacheInfo.from_cache ? `
                    <div class="cache-indicator">
                        <i class="fas fa-database"></i>
                        Cached (${Math.round(cacheInfo.cache_duration / 60)} min)
                    </div>
                ` : ''}
            </div>
            <div class="flight-category ${station.flight_category ? station.flight_category.toLowerCase() : 'unknown'}">
                ${station.flight_category || 'UNKN'}
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
                <span class="weather-label">Humidity</span>
                <span class="weather-value">${humidity}</span>
            </div>
        </div>
        
        ${station.conditions && station.conditions.length > 0 ? `
        <div class="weather-item">
            <span class="weather-label">Conditions</span>
            <span class="weather-value">
                ${station.conditions.map(cond => cond.text).join(', ')}
            </span>
        </div>
        ` : ''}
        
        ${station.clouds && station.clouds.length > 0 ? `
        <div class="weather-item">
            <span class="weather-label">Clouds</span>
            <span class="weather-value">
                ${station.clouds.map(cloud => `${cloud.text} at ${cloud.feet} ft`).join(', ')}
            </span>
        </div>
        ` : ''}
        
        ${station.raw_text ? `
        <div class="weather-raw">
            <p class="raw-metar">${station.raw_text}</p>
        </div>
        ` : ''}
    `;

    return card;
}

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

function displayEmptyState() {
    const emptyState = document.getElementById('emptyState');
    const weatherCards = document.getElementById('weatherCards');

    emptyState.style.display = 'block';
    weatherCards.style.display = 'none';
}

function showAlert(message, type) {
    const alert = document.getElementById('alertMessage');
    alert.textContent = message;
    alert.className = `alert-message alert-${type}`;
    alert.style.display = 'block';

    setTimeout(() => {
        alert.style.display = 'none';
    }, 5000);
}

function fetchMultipleStations() {
    document.getElementById('multiStationModal').style.display = 'flex';
}

function closeMultiStationModal() {
    document.getElementById('multiStationModal').style.display = 'none';
}

function showCacheManagement() {
    document.getElementById('cacheModal').style.display = 'flex';
}

function closeCacheModal() {
    document.getElementById('cacheModal').style.display = 'none';
}

async function getCacheStatus() {
    try {
        const response = await fetch('/admin/api/weather/cache/status');

        if (!response.ok) {
            if (response.status === 403) {
                throw new Error('Access denied. Please check your admin permissions.');
            }
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayCacheStatus(data.cache_status);

    } catch (error) {
        console.error('Error getting cache status:', error);
        showAlert(`Error getting cache status: ${error.message}`, 'error');

        const cacheStatusElement = document.getElementById('cacheStatus');
        cacheStatusElement.innerHTML = `
            <div class="cache-error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${error.message}</p>
                <p class="error-detail">Status: ${error.message.includes('Access denied') ? 'Unauthorized' : 'API Error'}</p>
            </div>
        `;
    }
}

async function clearWeatherCache() {
    if (!confirm('Are you sure you want to clear the weather cache? This will remove all cached weather data.')) {
        return;
    }

    try {
        const response = await fetch('/admin/api/weather/cache/clear', {
            method: 'POST'
        });

        if (!response.ok) {
            if (response.status === 403) {
                throw new Error('Access denied. Please check your admin permissions.');
            }
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        showAlert(data.message, 'success');

        getCacheStatus();

    } catch (error) {
        console.error('Error clearing cache:', error);
        showAlert(`Error clearing cache: ${error.message}`, 'error');
    }
}

function displayCacheStatus(cacheStatus) {
    const cacheStatusElement = document.getElementById('cacheStatus');

    if (!cacheStatus) {
        cacheStatusElement.innerHTML = `
            <div class="cache-error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Unable to load cache status</p>
            </div>
        `;
        return;
    }

    const utilizationPercent = Math.round((cacheStatus.total_entries / cacheStatus.max_entries) * 100);
    const activePercent = Math.round((cacheStatus.active_entries / cacheStatus.max_entries) * 100);

    cacheStatusElement.innerHTML = `
        <div class="cache-stats">
            <div class="cache-stat-row">
                <div class="cache-stat">
                    <span class="stat-label">Total Entries</span>
                    <span class="stat-value">${cacheStatus.total_entries}</span>
                </div>
                <div class="cache-stat">
                    <span class="stat-label">Active Entries</span>
                    <span class="stat-value">${cacheStatus.active_entries}</span>
                </div>
                <div class="cache-stat">
                    <span class="stat-label">Expired Entries</span>
                    <span class="stat-value">${cacheStatus.expired_entries}</span>
                </div>
            </div>
            
            <div class="cache-stat-row">
                <div class="cache-stat">
                    <span class="stat-label">Max Capacity</span>
                    <span class="stat-value">${cacheStatus.max_entries}</span>
                </div>
                <div class="cache-stat">
                    <span class="stat-label">Utilization</span>
                    <span class="stat-value ${utilizationPercent > 80 ? 'stat-warning' : ''}">
                        ${utilizationPercent}%
                    </span>
                </div>
                <div class="cache-stat">
                    <span class="stat-label">Cache Duration</span>
                    <span class="stat-value">${cacheStatus.cache_duration_minutes} min</span>
                </div>
            </div>
        </div>
        
        ${cacheStatus.oldest_entries.length > 0 ? `
        <div class="cache-entries-section">
            <h4>Oldest Entries</h4>
            <div class="cache-entries-list">
                ${cacheStatus.oldest_entries.map(entry => `
                    <div class="cache-entry">
                        <span class="entry-icao">${entry.icao}</span>
                        <span class="entry-time">${new Date(entry.created_at * 1000).toLocaleString()}</span>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}
        
        ${cacheStatus.newest_entries.length > 0 ? `
        <div class="cache-entries-section">
            <h4>Newest Entries</h4>
            <div class="cache-entries-list">
                ${cacheStatus.newest_entries.map(entry => `
                    <div class="cache-entry">
                        <span class="entry-icao">${entry.icao}</span>
                        <span class="entry-time">${new Date(entry.created_at * 1000).toLocaleString()}</span>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}
        
        <div class="cache-actions">
            <button class="btn btn-small btn-secondary" onclick="getCacheStatus()">
                <i class="fas fa-sync-alt"></i> Refresh
            </button>
            <button class="btn btn-small btn-danger" onclick="clearWeatherCache()">
                <i class="fas fa-trash"></i> Clear Cache
            </button>
        </div>
    `;
}

document.addEventListener('click', function (event) {
    const multiModal = document.getElementById('multiStationModal');
    const cacheModal = document.getElementById('cacheModal');

    if (event.target === multiModal) {
        closeMultiStationModal();
    }

    if (event.target === cacheModal) {
        closeCacheModal();
    }
});
