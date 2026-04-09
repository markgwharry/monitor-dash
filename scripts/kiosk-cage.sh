#!/bin/bash
# Dashboard kiosk launcher
# Rotates display and opens chromium in kiosk mode

DASHBOARD_URL="${1:-http://localhost:8080/}"

# Rotate display after cage starts (background, wait for wayland)
(
    sleep 3
    wlr-randr --output HDMI-A-1 --transform 90 2>/dev/null
) &

exec chromium \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --no-first-run \
    --enable-features=OverlayScrollbar \
    --disable-translate \
    --disable-features=TranslateUI \
    http://localhost:8080/
