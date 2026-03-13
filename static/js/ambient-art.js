/**
 * Ambient Mode - Data as Art
 * Visual atmosphere driven by weather, temperature, and home data
 */

(function() {
    'use strict';

    const canvas = document.getElementById('ambient-canvas');
    const ctx = canvas?.getContext('2d');
    const dataEl = document.querySelector('.ambient-data');

    if (!canvas || !ctx) return;

    // Set canvas size
    function resize() {
        canvas.width = 1080;
        canvas.height = 1920;
    }
    resize();

    // Data state
    let state = {
        temp: 15,
        tempOutside: 10,
        humidity: 50,
        condition: 'cloudy',
        airQuality: 'good',
        heatingOn: false,
        nextEventMins: null,
        time: new Date()
    };

    // Color palettes based on conditions
    const palettes = {
        cold: ['#1e3a5f', '#2d5a87', '#3d7ab0', '#4d9ad9', '#5dbaff'],
        mild: ['#1a1a2e', '#2d2d5a', '#4a4a8a', '#6a6aba', '#8a8aea'],
        warm: ['#2d1b1b', '#5a2d2d', '#8a4a4a', '#ba6a6a', '#ea8a8a'],
        hot: ['#3d1a1a', '#6a2a1a', '#9a4a2a', '#ca6a3a', '#fa8a4a'],
        night: ['#0a0f1a', '#101828', '#182438', '#203048', '#284058']
    };

    // Particle system
    class Particle {
        constructor(type = 'ambient') {
            this.type = type;
            this.reset();
        }

        reset() {
            if (this.type === 'rain') {
                this.x = Math.random() * canvas.width;
                this.y = -10;
                this.speed = 8 + Math.random() * 12;
                this.length = 10 + Math.random() * 20;
                this.opacity = 0.1 + Math.random() * 0.3;
            } else if (this.type === 'snow') {
                this.x = Math.random() * canvas.width;
                this.y = -10;
                this.speed = 1 + Math.random() * 2;
                this.size = 2 + Math.random() * 4;
                this.opacity = 0.3 + Math.random() * 0.4;
                this.drift = Math.random() * 2 - 1;
            } else if (this.type === 'star') {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height * 0.7;
                this.size = 1.5 + Math.random() * 3;
                this.twinkleSpeed = 0.015 + Math.random() * 0.025;
                this.twinklePhase = Math.random() * Math.PI * 2;
                this.opacity = 0.5 + Math.random() * 0.5;
            } else if (this.type === 'dust') {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = 1 + Math.random() * 2;
                this.speedX = (Math.random() - 0.5) * 0.3;
                this.speedY = (Math.random() - 0.5) * 0.2;
                this.opacity = 0.05 + Math.random() * 0.1;
            } else {
                // Ambient floating orb
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = 80 + Math.random() * 200;
                this.speedX = (Math.random() - 0.5) * 0.3;
                this.speedY = (Math.random() - 0.5) * 0.2;
                this.hue = Math.random() * 60 - 30; // Variation from base
                this.opacity = 0.08 + Math.random() * 0.12;
            }
        }

        update() {
            if (this.type === 'rain') {
                this.y += this.speed;
                this.x += 1; // Slight wind
                if (this.y > canvas.height) this.reset();
            } else if (this.type === 'snow') {
                this.y += this.speed;
                this.x += this.drift + Math.sin(this.y * 0.01) * 0.5;
                if (this.y > canvas.height) this.reset();
            } else if (this.type === 'star') {
                this.twinklePhase += this.twinkleSpeed;
            } else if (this.type === 'dust') {
                this.x += this.speedX;
                this.y += this.speedY;
                if (this.x < 0) this.x = canvas.width;
                if (this.x > canvas.width) this.x = 0;
                if (this.y < 0) this.y = canvas.height;
                if (this.y > canvas.height) this.y = 0;
            } else {
                this.x += this.speedX;
                this.y += this.speedY;
                // Bounce at edges
                if (this.x < -this.size || this.x > canvas.width + this.size) this.speedX *= -1;
                if (this.y < -this.size || this.y > canvas.height + this.size) this.speedY *= -1;
            }
        }

        draw(baseColor) {
            if (this.type === 'rain') {
                ctx.beginPath();
                ctx.moveTo(this.x, this.y);
                ctx.lineTo(this.x + 2, this.y + this.length);
                ctx.strokeStyle = `rgba(150, 180, 220, ${this.opacity})`;
                ctx.lineWidth = 1;
                ctx.stroke();
            } else if (this.type === 'snow') {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255, 255, 255, ${this.opacity})`;
                ctx.fill();
            } else if (this.type === 'star') {
                const twinkle = (Math.sin(this.twinklePhase) + 1) / 2;
                const opacity = this.opacity * (0.5 + twinkle * 0.5);
                const size = this.size * (0.8 + twinkle * 0.4);
                // Glow
                ctx.beginPath();
                ctx.arc(this.x, this.y, size * 3, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(200, 220, 255, ${opacity * 0.1})`;
                ctx.fill();
                // Core
                ctx.beginPath();
                ctx.arc(this.x, this.y, size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255, 255, 250, ${opacity})`;
                ctx.fill();
            } else if (this.type === 'dust') {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(200, 180, 150, ${this.opacity})`;
                ctx.fill();
            } else {
                // Gradient orb
                const gradient = ctx.createRadialGradient(
                    this.x, this.y, 0,
                    this.x, this.y, this.size
                );
                gradient.addColorStop(0, `rgba(${baseColor.r}, ${baseColor.g}, ${baseColor.b}, ${this.opacity})`);
                gradient.addColorStop(1, 'transparent');
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = gradient;
                ctx.fill();
            }
        }
    }

    // Particle collections
    let orbs = [];
    let weatherParticles = [];
    let stars = [];
    let dust = [];

    // Initialize particles
    function initParticles() {
        orbs = Array.from({ length: 6 }, () => new Particle('ambient'));
        stars = Array.from({ length: 50 }, () => new Particle('star'));
        dust = Array.from({ length: 30 }, () => new Particle('dust'));
    }

    // Update weather particles based on condition
    function updateWeatherParticles() {
        const condition = state.condition.toLowerCase();

        if (condition.includes('rain') || condition.includes('drizzle') || condition.includes('shower')) {
            if (weatherParticles.length < 100 || weatherParticles[0]?.type !== 'rain') {
                weatherParticles = Array.from({ length: 100 }, () => new Particle('rain'));
            }
        } else if (condition.includes('snow') || condition.includes('sleet')) {
            if (weatherParticles.length < 60 || weatherParticles[0]?.type !== 'snow') {
                weatherParticles = Array.from({ length: 60 }, () => new Particle('snow'));
            }
        } else {
            weatherParticles = [];
        }
    }

    // Get base color from temperature
    function getBaseColor() {
        const temp = state.tempOutside;
        let r, g, b;

        if (temp < 5) {
            // Cold - blue
            r = 30 + Math.sin(Date.now() * 0.0001) * 10;
            g = 80 + Math.sin(Date.now() * 0.00012) * 20;
            b = 180 + Math.sin(Date.now() * 0.00015) * 30;
        } else if (temp < 15) {
            // Mild - purple/blue
            r = 80 + Math.sin(Date.now() * 0.0001) * 20;
            g = 60 + Math.sin(Date.now() * 0.00012) * 15;
            b = 160 + Math.sin(Date.now() * 0.00015) * 25;
        } else if (temp < 22) {
            // Warm - purple/pink
            r = 140 + Math.sin(Date.now() * 0.0001) * 30;
            g = 80 + Math.sin(Date.now() * 0.00012) * 20;
            b = 140 + Math.sin(Date.now() * 0.00015) * 25;
        } else {
            // Hot - orange/red
            r = 200 + Math.sin(Date.now() * 0.0001) * 30;
            g = 100 + Math.sin(Date.now() * 0.00012) * 30;
            b = 60 + Math.sin(Date.now() * 0.00015) * 20;
        }

        // Heating on adds warmth
        if (state.heatingOn) {
            r = Math.min(255, r + 40);
            g = Math.min(255, g + 10);
        }

        return { r: Math.round(r), g: Math.round(g), b: Math.round(b) };
    }

    // Get background gradient
    function getBackgroundGradient() {
        const temp = state.tempOutside;
        const hour = state.time.getHours();
        const isNight = hour < 6 || hour > 20;

        let colors;
        if (isNight) {
            colors = palettes.night;
        } else if (temp < 5) {
            colors = palettes.cold;
        } else if (temp < 15) {
            colors = palettes.mild;
        } else if (temp < 22) {
            colors = palettes.warm;
        } else {
            colors = palettes.hot;
        }

        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, colors[0]);
        gradient.addColorStop(0.4, colors[1]);
        gradient.addColorStop(0.7, colors[2]);
        gradient.addColorStop(1, colors[3]);

        return gradient;
    }

    // Draw heating glow
    function drawHeatingGlow() {
        if (!state.heatingOn) return;

        const gradient = ctx.createRadialGradient(
            canvas.width / 2, canvas.height, 0,
            canvas.width / 2, canvas.height, canvas.height * 0.6
        );
        gradient.addColorStop(0, 'rgba(255, 120, 50, 0.15)');
        gradient.addColorStop(0.5, 'rgba(255, 80, 30, 0.05)');
        gradient.addColorStop(1, 'transparent');

        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // Draw event pulse
    let eventPulsePhase = 0;
    function drawEventPulse() {
        if (state.nextEventMins === null || state.nextEventMins > 30) return;

        eventPulsePhase += 0.02;
        const intensity = Math.max(0, 1 - state.nextEventMins / 30);
        const pulse = (Math.sin(eventPulsePhase * 2) + 1) / 2;

        const gradient = ctx.createRadialGradient(
            canvas.width / 2, canvas.height * 0.3, 0,
            canvas.width / 2, canvas.height * 0.3, 200 + pulse * 100
        );
        gradient.addColorStop(0, `rgba(100, 150, 255, ${0.1 * intensity * pulse})`);
        gradient.addColorStop(1, 'transparent');

        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // Draw air quality haze
    function drawAirQualityHaze() {
        if (state.airQuality === 'good') return;

        const haziness = state.airQuality === 'poor' ? 0.15 : 0.08;
        ctx.fillStyle = `rgba(150, 140, 130, ${haziness})`;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // Main render loop
    function render() {
        // Background
        ctx.fillStyle = getBackgroundGradient();
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Stars (always at night, daytime only if clear)
        const hour = state.time.getHours();
        const isNight = hour < 6 || hour > 20;
        const isClear = state.condition.toLowerCase().includes('clear') ||
                        state.condition.toLowerCase().includes('sunny');
        const isCloudy = state.condition.toLowerCase().includes('cloud') ||
                         state.condition.toLowerCase().includes('overcast');

        // Always show stars at night (dimmer if cloudy), or daytime if clear
        if (isNight || isClear) {
            const cloudDim = (isNight && isCloudy) ? 0.4 : 1;
            ctx.globalAlpha = cloudDim;
            stars.forEach(s => {
                s.update();
                s.draw();
            });
            ctx.globalAlpha = 1;
        }

        // Ambient orbs
        const baseColor = getBaseColor();
        orbs.forEach(orb => {
            orb.update();
            orb.draw(baseColor);
        });

        // Dust particles (for poor air quality)
        if (state.airQuality !== 'good') {
            dust.forEach(d => {
                d.update();
                d.draw();
            });
        }

        // Weather particles
        weatherParticles.forEach(p => {
            p.update();
            p.draw();
        });

        // Heating glow
        drawHeatingGlow();

        // Event pulse
        drawEventPulse();

        // Air quality haze
        drawAirQualityHaze();

        requestAnimationFrame(render);
    }

    // Update clock display
    function updateClock() {
        const clockEl = document.getElementById('ambient-clock');
        const tempEl = document.getElementById('ambient-temp');

        if (clockEl) {
            const now = new Date();
            state.time = now;
            const hours = now.getHours().toString().padStart(2, '0');
            const mins = now.getMinutes().toString().padStart(2, '0');
            clockEl.textContent = `${hours}:${mins}`;
        }

        if (tempEl) {
            tempEl.textContent = `${Math.round(state.tempOutside)}°`;
        }
    }

    // Load data from element
    function loadData() {
        if (!dataEl) return;

        state.temp = parseFloat(dataEl.dataset.temp) || 15;
        state.tempOutside = parseFloat(dataEl.dataset.tempOutside) || 10;
        state.humidity = parseFloat(dataEl.dataset.humidity) || 50;
        state.condition = dataEl.dataset.condition || 'cloudy';
        state.airQuality = dataEl.dataset.airQuality || 'good';
        state.heatingOn = dataEl.dataset.heatingOn === 'true';
        state.nextEventMins = dataEl.dataset.nextEventMins ?
            parseInt(dataEl.dataset.nextEventMins) : null;

        updateWeatherParticles();
    }

    // Refresh data from API
    async function refreshData() {
        try {
            const response = await fetch('/api/data');
            const data = await response.json();

            if (dataEl) {
                dataEl.dataset.temp = data.systems?.indoor?.temp || 15;
                dataEl.dataset.tempOutside = data.weather?.temp || 10;
                dataEl.dataset.humidity = data.systems?.indoor?.humidity || 50;
                dataEl.dataset.condition = data.weather?.condition || 'cloudy';
                dataEl.dataset.airQuality = data.systems?.air_quality?.pm25_label?.toLowerCase() || 'good';
                dataEl.dataset.heatingOn = data.systems?.heating?.status === 'heating';
                dataEl.dataset.nextEventMins = data.calendar?.next_meeting?.minutes_until || '';
            }

            loadData();
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    }

    // Check mode change
    async function checkMode() {
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

    // Initialize
    function init() {
        initParticles();
        loadData();
        updateClock();
        render();

        // Update clock every second
        setInterval(updateClock, 1000);

        // Refresh data every minute
        setInterval(refreshData, 60000);

        // Check mode every 30 seconds
        setInterval(checkMode, 30000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
