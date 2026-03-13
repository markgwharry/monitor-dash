/**
 * Screen care — pixel shift + late-night blanking
 * Loaded on all modes via base.html
 */
(function () {
    'use strict';

    // ---- Configuration ----
    const SHIFT_INTERVAL   = 5 * 60 * 1000; // 5 minutes
    const SHIFT_MAX        = 3;              // max px offset
    const SLEEP_START      = 0;              // midnight
    const SLEEP_END        = 6;              // 6am
    const SLEEP_CHECK      = 30 * 1000;      // check every 30s

    // ---- Pixel Shift ----
    // Cycle through small offsets to prevent static edges
    const shiftPattern = [
        [0, 0], [1, 1], [2, 0], [3, -1],
        [2, -2], [0, -1], [-1, 0], [-2, 1],
        [-3, 2], [-1, 1], [0, 0], [1, -1],
        [2, -2], [3, -1], [1, 1], [-1, 2],
    ];
    let shiftIndex = 0;

    function applyPixelShift() {
        const [dx, dy] = shiftPattern[shiftIndex % shiftPattern.length];
        document.body.style.transform = `translate(${dx}px, ${dy}px)`;
        shiftIndex++;
    }

    // ---- Sleep Blanking ----
    let overlay = null;
    let clockEl = null;
    let isSleeping = false;

    function createOverlay() {
        overlay = document.createElement('div');
        overlay.id = 'sleep-overlay';

        clockEl = document.createElement('div');
        clockEl.id = 'sleep-clock';
        clockEl.className = 'mono';
        overlay.appendChild(clockEl);

        document.body.appendChild(overlay);
    }

    function updateSleepClock() {
        if (!clockEl) return;
        const now = new Date();
        const hh = String(now.getHours()).padStart(2, '0');
        const mm = String(now.getMinutes()).padStart(2, '0');
        clockEl.textContent = `${hh}:${mm}`;
    }

    function checkSleep() {
        const hour = new Date().getHours();
        const shouldSleep = hour >= SLEEP_START && hour < SLEEP_END;

        if (shouldSleep && !isSleeping) {
            isSleeping = true;
            overlay.classList.add('active');
            updateSleepClock();
        } else if (!shouldSleep && isSleeping) {
            isSleeping = false;
            overlay.classList.remove('active');
        }

        if (isSleeping) {
            updateSleepClock();
        }
    }

    // ---- Init ----
    function init() {
        createOverlay();

        // Pixel shift: every 5 minutes
        applyPixelShift();
        setInterval(applyPixelShift, SHIFT_INTERVAL);

        // Sleep check: every 30 seconds
        checkSleep();
        setInterval(checkSleep, SLEEP_CHECK);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
