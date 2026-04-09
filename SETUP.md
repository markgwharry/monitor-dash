# Pi Dashboard — Pi Zero 2 W Setup

## Prerequisites

- Raspberry Pi Zero 2 W (or any Pi with 64-bit OS)
- 64-bit Raspberry Pi OS (Bookworm or later)
- SSH access configured
- Network connectivity

## 1. Install System Packages

```bash
sudo apt-get update
sudo apt-get install -y chromium python3-venv cage wlr-randr
```

## 2. Clone Repos

```bash
mkdir -p ~/apps
cd ~/apps

git clone https://github.com/markgwharry/monitor-dash.git dashboard/repo
git clone https://github.com/markgwharry/aineLetters.git aine-letters/repo
```

## 3. Set Up Python Environment

```bash
cd ~/apps/dashboard/repo
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and tokens
nano .env
```

## 5. Test the Dashboard

```bash
cd ~/apps/dashboard/repo
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
# Visit http://pizero.local:8080 from another device
```

## 6. Install Systemd Services

### Dashboard server (runs on boot)

```bash
sudo cp scripts/dashboard-server.service /etc/systemd/system/dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable --now dashboard.service
```

### Kiosk mode (Chromium in cage, auto-starts on boot)

Create `/etc/systemd/system/kiosk.service`:

```ini
[Unit]
Description=Dashboard Kiosk
After=dashboard.service
Wants=dashboard.service

[Service]
Type=simple
User=pi
Environment=WLR_LIBINPUT_NO_DEVICES=1
ExecStart=/usr/bin/cage -s -- /home/pi/apps/dashboard/repo/scripts/kiosk-cage.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now kiosk.service
```

## 7. Display Rotation

The kiosk script (`scripts/kiosk-cage.sh`) rotates HDMI-A-1 to portrait (90°).
Edit the `wlr-randr` line if your monitor needs a different transform (0, 90, 180, 270).

## 8. Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

## 9. Switching to the Game

The letter game is accessible at `http://localhost:8080/games/letters` — there is a
link in the dashboard footer. Press the back arrow in the game to return to the dashboard.

## File Structure

```
~/apps/
├── dashboard/repo/          # This repo
│   ├── app/                 # FastAPI application
│   ├── static/              # CSS, JS
│   ├── scripts/             # Service files and kiosk launcher
│   ├── .env                 # Your secrets (not in git)
│   └── requirements.txt
└── aine-letters/repo/       # Letter game (separate repo)
    ├── index.html
    ├── app.js
    └── style.css
```
