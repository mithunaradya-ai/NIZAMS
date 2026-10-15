#!/bin/sh
set -eu

URL="${KIOSK_URL:-http://127.0.0.1:8080}"
while ! curl --silent --fail "$URL/health" >/dev/null; do
    sleep 2
done

exec chromium \
    --kiosk \
    --noerrdialogs \
    --disable-session-crashed-bubble \
    --disable-infobars \
    --disable-translate \
    --check-for-update-interval=31536000 \
    --autoplay-policy=no-user-gesture-required \
    "$URL"
