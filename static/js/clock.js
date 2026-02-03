/**
 * Live clock and data refresh for operational mode
 */

(function() {
    'use strict';

    const clockElement = document.getElementById('clock');
    const refreshInterval = window.DASHBOARD_CONFIG?.refreshInterval || 60000;

    /**
     * Update the clock display
     */
    function updateClock() {
        if (!clockElement) return;

        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');

        clockElement.textContent = `${hours}:${minutes}`;
    }

    /**
     * Check if mode should change and reload if needed
     */
    async function checkModeChange() {
        try {
            const response = await fetch('/api/mode');
            const data = await response.json();

            if (data.mode !== window.DASHBOARD_CONFIG?.mode) {
                // Mode changed, reload the page
                window.location.reload();
            }
        } catch (error) {
            console.error('Error checking mode:', error);
        }
    }

    /**
     * Refresh dashboard data
     */
    async function refreshData() {
        try {
            const response = await fetch('/api/data');
            const data = await response.json();

            // Update countdown if present
            const countdown = document.getElementById('meeting-countdown');
            if (countdown && data.calendar?.next_meeting?.minutes_until !== undefined) {
                countdown.textContent = `in ${data.calendar.next_meeting.minutes_until}m`;
            }

            // Check for mode change
            await checkModeChange();
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    }

    // Initialize
    function init() {
        // Update clock immediately and then every second
        updateClock();
        setInterval(updateClock, 1000);

        // Refresh data periodically
        setInterval(refreshData, refreshInterval);

        // Also check mode more frequently (every 30 seconds)
        setInterval(checkModeChange, 30000);
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
