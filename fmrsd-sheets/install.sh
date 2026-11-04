#!/usr/bin/env bash
# Run on meercat from inside the fmrsd-sheets folder:  bash install.sh
# Installs the sheets server as a user service that starts at boot, then publishes
# it to your Tailscale network with `tailscale serve`.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8077
UNIT="$HOME/.config/systemd/user/fmrsd-sheets.service"

command -v python3 >/dev/null || { echo "python3 is not installed"; exit 1; }
mkdir -p "$DIR/data" "$(dirname "$UNIT")"

cat > "$UNIT" <<EOF
[Unit]
Description=FMRSD timesheets, trip sheets and fuel sheets

[Service]
ExecStart=$(command -v python3) $DIR/server.py --host 127.0.0.1 --port $PORT
Restart=on-failure

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now fmrsd-sheets.service

# Without lingering, user services stop when you log out of a headless machine.
if [ "$(loginctl show-user "$USER" -p Linger --value 2>/dev/null)" != yes ]; then
  echo "Allowing the service to run while you're logged out (may ask for your password)…"
  loginctl enable-linger "$USER" 2>/dev/null || sudo loginctl enable-linger "$USER"
fi

sleep 1
curl -fsS "http://127.0.0.1:$PORT/api/store" >/dev/null && echo "Server is running on port $PORT."

echo "Publishing to your tailnet…"
if tailscale serve --bg "$PORT" 2>/dev/null || sudo tailscale serve --bg "$PORT"; then
  tailscale serve status
else
  echo "tailscale serve failed. See the README for the fallback."
fi
