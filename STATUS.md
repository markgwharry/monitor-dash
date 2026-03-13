# Pi Dashboard — Project Status

## What We've Built

An always-on dashboard for a 1080×1920 portrait display (Raspberry Pi 5), with two modes:

- **Operational mode** — dense, information-rich display for work hours
- **Ambient mode** — generative art with data-driven colour shifts for after hours

### Tech Stack

- **Backend:** FastAPI + Uvicorn + Jinja2 templates
- **Frontend:** Vanilla HTML/CSS/JS (no build step)
- **Data:** Pluggable provider pattern — `DataProvider` base class, `DataAggregator` merges all providers
- **Fonts:** Barlow + Barlow Condensed (body/labels), JetBrains Mono (data) via Google Fonts
- **Theme:** "Night Ops" — dark blue-black backgrounds, purposeful accent colours (green/blue/amber/red/cyan)

---

## Current State (Feb 2026)

**Dashboard is fully operational with live data.**

### Live Data Sources

| Provider | Data | Source |
|----------|------|--------|
| `PiHealthProvider` | CPU, memory, temp, disk, uptime | `/proc/stat`, `/proc/meminfo`, `/sys/class/thermal`, `shutil` |
| `AirQualityProvider` | PM2.5, PM10, VOC, indoor temp/humidity | Sensor at `192.168.1.65` |
| `DockerProvider` | 24 containers, status | Portainer API at `192.168.1.125:9000` |
| `WeatherProvider` | Current + forecast | OpenWeatherMap API (key pending activation) |
| `CalendarProvider` | Today/tomorrow events, day summary | MS365 ICS + iCloud (Personal + Family) |
| `CameraProvider` | Driveway camera snapshot | Home Assistant at `192.168.1.125:8123` |

### Removed (no accessible API)

- NAS storage stats — UGOS doesn't expose a usable API
- Network stats — low priority, left on mock

---

## Architecture

### Provider Pattern

Each data source is a `DataProvider` subclass in `app/services/providers/`. The `DataAggregator` merges them in order — later providers override earlier ones for the same keys.

```python
# app/main.py
data_aggregator = DataAggregator(providers=[
    MockDataProvider(),          # fallback base layer
    PiHealthProvider(),
    AirQualityProvider(endpoint=settings.air_sensor_url),
    DockerProvider(portainer_url=..., api_key=..., endpoint_id=...),
    WeatherProvider(api_key=..., location=...),
    CalendarProvider(ics_urls=[...]),
    CameraProvider(ha_url=..., token=..., entity_id=...),
])
```

### File Map

```
app/
  main.py                 — FastAPI app, routes, provider wiring
  config.py               — Pydantic settings (DASHBOARD_ env prefix)
  templates/
    base.html             — Base template (fonts, config injection)
    operational.html      — Operational mode layout
    ambient.html          — Ambient mode (generative art)
  routers/
    api.py                — GET /api/data (JSON)
    mode.py               — GET/POST /api/mode
  services/
    mode_manager.py       — Time-based + manual override mode switching
    data_aggregator.py    — Merges data from all providers
    providers/
      base.py             — Abstract DataProvider base class
      mock.py             — Mock data fallback (~50 fields)
      pi_health.py        — CPU, memory, temp, disk, uptime
      air_quality.py      — PM2.5, PM10, VOC, indoor temp/humidity
      docker.py           — Container list via Portainer API
      weather.py          — OpenWeatherMap current + forecast
      calendar.py         — ICS feed parser (icalendar library)
      camera.py           — Home Assistant camera snapshot URL

static/
  css/
    main.css              — Variables, reset, shared styles
    operational.css       — Operational mode layout + components
    ambient.css           — Ambient mode animations
  js/
    clock.js              — Live clock, day progress, camera refresh, data polling
    ambient-art.js        — Data-driven colour adjustments

scripts/
  dashboard-server.service — systemd unit for uvicorn backend
  dashboard.service         — systemd unit for kiosk browser
  kiosk-start.sh           — Browser launch script
```

---

## Configuration

All settings in `app/config.py`, overridable with `DASHBOARD_` env vars:

| Setting | Default | Notes |
|---------|---------|-------|
| `work_start_hour` | 9 | Operational mode starts |
| `work_end_hour` | 18 | Ambient mode starts |
| `air_sensor_url` | `http://192.168.1.65` | Air quality sensor |
| `homeassistant_url` | `http://192.168.1.125:8123` | HA instance |
| `homeassistant_token` | *(set)* | Long-lived access token |
| `camera_entity_id` | `camera.driveway_live_view_2` | HA camera entity |
| `portainer_url` | `http://192.168.1.125:9000` | Portainer instance |
| `portainer_api_key` | *(set)* | Portainer access token |
| `portainer_endpoint_id` | 3 | Docker environment ID |
| `weather_api_key` | *(set)* | OpenWeatherMap API key |
| `calendar_ics_urls` | *(list)* | MS365 + iCloud ICS URLs |

---

## Running

### Development

```bash
cd /home/pi/apps/dashboard/repo
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Production (systemd)

```bash
# Backend service
sudo systemctl start dashboard-server
sudo systemctl status dashboard-server

# View logs
journalctl -u dashboard-server -f
```

The service is installed at `/etc/systemd/system/dashboard-server.service` and enabled to start on boot.

### URLs

- `/` — Auto-selects mode based on time
- `/operational` — Force operational view
- `/ambient` — Force ambient view
- `/api/data` — JSON data endpoint
- `/api/mode` — Current mode status

---

## Network Map

| Device | IP | Services |
|--------|-----|----------|
| Pi (this device) | 192.168.1.x | Dashboard on :8080 |
| NAS (Ugreen) | 192.168.1.125 | Portainer :9000, Home Assistant :8123, Homepage :3000 |
| Air sensor | 192.168.1.65 | JSON endpoint on :80 |

---

## Future Work

- **Weather** — Will go live once OpenWeatherMap key activates (usually 2-3 hours)
- **Caching** — Add TTL caching for calendar/weather to reduce API calls
- **Error resilience** — Show stale data + indicator when a provider fails
- **WebSocket** — Replace polling with push for instant updates
- **Self-hosted fonts** — Remove Google Fonts dependency for offline reliability
- **Kiosk setup** — Configure browser to auto-launch on boot

---

## Credentials & Secrets

All sensitive values are in `app/config.py`. For production, consider moving to environment variables or a `.env` file (already supported via pydantic-settings).

Current secrets:
- Portainer API key
- Home Assistant long-lived token
- OpenWeatherMap API key
- Calendar ICS URLs (contain auth tokens)
