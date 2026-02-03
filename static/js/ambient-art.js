/**
 * Ambient mode - subtle data-driven color adjustments
 */

(function() {
    'use strict';

    const container = document.querySelector('.dashboard-ambient');
    const dataElement = document.querySelector('.ambient-data');

    /**
     * Apply data-driven color adjustments
     */
    function applyDataColors() {
        if (!container || !dataElement) return;

        const temp = parseFloat(dataElement.dataset.temp) || 15;
        const humidity = parseFloat(dataElement.dataset.humidity) || 50;
        const airQuality = dataElement.dataset.airQuality || 'good';

        // Temperature affects warm/cool tones
        if (temp < 10) {
            container.setAttribute('data-temp-cold', 'true');
            container.removeAttribute('data-temp-warm');
        } else if (temp > 25) {
            container.setAttribute('data-temp-warm', 'true');
            container.removeAttribute('data-temp-cold');
        } else {
            container.removeAttribute('data-temp-cold');
            container.removeAttribute('data-temp-warm');
        }

        // Air quality affects saturation
        if (airQuality === 'poor') {
            container.setAttribute('data-air-poor', 'true');
        } else {
            container.removeAttribute('data-air-poor');
        }
    }

    /**
     * Check if should switch to operational mode
     */
    async function checkModeChange() {
        try {
            const response = await fetch('/api/mode');
            const data = await response.json();

            if (data.mode !== 'ambient') {
                window.location.reload();
            }
        } catch (error) {
            console.error('Error checking mode:', error);
        }
    }

    /**
     * Refresh ambient data
     */
    async function refreshData() {
        try {
            const response = await fetch('/api/data');
            const data = await response.json();

            if (dataElement) {
                dataElement.dataset.temp = data.weather?.temp || 15;
                dataElement.dataset.humidity = data.systems?.indoor?.humidity || 50;
                dataElement.dataset.airQuality = data.systems?.air_quality?.voc || 'good';
            }

            applyDataColors();
            await checkModeChange();
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    }

    // Initialize
    function init() {
        applyDataColors();

        // Refresh data every minute
        setInterval(refreshData, 60000);

        // Check mode every 30 seconds
        setInterval(checkModeChange, 30000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
