/**
 * Operational mode — live clock, day progress, and data refresh
 */
(function () {
    'use strict';

    const clockEl        = document.getElementById('clock');
    const clockSecEl     = document.getElementById('clock-seconds');
    const clockSepEl     = document.getElementById('clock-sep');
    const dayProgressEl  = document.getElementById('day-progress');
    const lastRefreshEl  = document.getElementById('last-refresh');
    const cameraFeedEl   = document.getElementById('camera-feed');
    const cameraTimeEl   = document.getElementById('camera-time');
    const cameraStatusEl = document.getElementById('camera-status');
    const refreshInterval = window.DASHBOARD_CONFIG?.refreshInterval || 60000;
    const cameraRefreshInterval = 5000; // 5 seconds

    // Work day bounds (minutes from midnight)
    const WORK_START = 9 * 60;
    const WORK_END   = 18 * 60;

    /**
     * Update clock display (called every second)
     */
    function updateClock() {
        const now = new Date();
        const hh  = String(now.getHours()).padStart(2, '0');
        const mm  = String(now.getMinutes()).padStart(2, '0');
        const ss  = String(now.getSeconds()).padStart(2, '0');

        if (clockEl)    clockEl.textContent    = `${hh}:${mm}`;
        if (clockSecEl) clockSecEl.textContent = ss;
    }

    /**
     * Update day progress bar
     */
    function updateDayProgress() {
        if (!dayProgressEl) return;

        const now  = new Date();
        const mins = now.getHours() * 60 + now.getMinutes();
        let pct;

        if (mins <= WORK_START) pct = 0;
        else if (mins >= WORK_END) pct = 100;
        else pct = Math.round((mins - WORK_START) / (WORK_END - WORK_START) * 100);

        dayProgressEl.style.width = pct + '%';
    }

    /**
     * Refresh camera snapshot
     */
    function refreshCamera() {
        if (!cameraFeedEl) return;

        const newUrl = '/api/camera?_t=' + Date.now();

        // Preload the image to avoid flicker
        const img = new Image();
        img.onload = function () {
            cameraFeedEl.src = newUrl;
            if (cameraTimeEl) {
                const now = new Date();
                cameraTimeEl.textContent = now.toLocaleTimeString('en-GB', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
            }
            if (cameraStatusEl) {
                cameraStatusEl.classList.remove('dot-red');
                cameraStatusEl.classList.add('dot-green');
            }
        };
        img.onerror = function () {
            if (cameraStatusEl) {
                cameraStatusEl.classList.remove('dot-green');
                cameraStatusEl.classList.add('dot-red');
            }
        };
        img.src = newUrl;
    }

    /**
     * Check if mode should change and reload
     */
    async function checkModeChange() {
        try {
            const res  = await fetch('/api/mode');
            const data = await res.json();

            if (data.mode !== window.DASHBOARD_CONFIG?.mode) {
                window.location.reload();
            }
        } catch (e) {
            console.error('Mode check error:', e);
        }
    }

    /**
     * Refresh dashboard data from API
     */
    async function refreshData() {
        try {
            const res  = await fetch('/api/data');
            const data = await res.json();

            // Update meeting countdown in priority panel
            const countdownEl = document.getElementById('next-countdown');
            if (countdownEl && data.calendar?.next_meeting) {
                const mtg = data.calendar.next_meeting;
                if (mtg.active) {
                    countdownEl.textContent = `${mtg.minutes_remaining}m`;
                } else if (mtg.minutes_until !== undefined) {
                    countdownEl.textContent = `${mtg.minutes_until}m`;
                }
            }

            // Update last-refresh timestamp
            if (lastRefreshEl && data.time?.current) {
                lastRefreshEl.textContent = data.time.current;
            }

            // Check for mode change
            await checkModeChange();
        } catch (e) {
            console.error('Data refresh error:', e);
        }
    }

    /**
     * Initialise timers
     */
    function init() {
        updateClock();
        updateDayProgress();

        // Clock: every second
        setInterval(updateClock, 1000);

        // Day progress: every minute
        setInterval(updateDayProgress, 60000);

        // Data refresh
        setInterval(refreshData, refreshInterval);

        // Mode check: every 30 seconds
        setInterval(checkModeChange, 30000);

        // Camera refresh: every 5 seconds
        if (cameraFeedEl) {
            setInterval(refreshCamera, cameraRefreshInterval);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
