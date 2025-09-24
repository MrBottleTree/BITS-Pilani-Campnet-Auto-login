#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/campnet_autologin.py"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="campnet_autologin.service"
SERVICE_PATH="$SERVICE_DIR/$SERVICE_NAME"
PYTHON_BIN="${PYTHON_BIN:-"$(command -v python3 || true)"}"

log() { printf '[campnet-autologin] %s\n' "$*"; }

ensure_python() {
    if [[ -z "$PYTHON_BIN" ]]; then
        log "python3 not found on PATH. Set PYTHON_BIN=/path/to/python and rerun."
        exit 1
    fi
}

install_deps() {
    if [[ -n "$SKIP_PIP" ]]; then
        return
    fi
    log "Installing/upgrading required Python packages (requests, python-dotenv)"
    "$PYTHON_BIN" -m pip install --user --upgrade requests python-dotenv || log "pip install failed; continuing"
}

write_service() {
    mkdir -p "$SERVICE_DIR"
    cat >"$SERVICE_PATH" <<SERVICE
[Unit]
Description=Campnet Autologin
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR
ExecStart=$PYTHON_BIN $SCRIPT_PATH
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
SERVICE
    log "Systemd user service written to $SERVICE_PATH"
}

reload_and_enable() {
    systemctl --user daemon-reload
    systemctl --user enable --now "$SERVICE_NAME"
    log "Service enabled and started (systemd user)"
}

stop_and_remove() {
    if systemctl --user list-unit-files | grep -q "^$SERVICE_NAME"; then
        systemctl --user disable --now "$SERVICE_NAME" >/dev/null 2>&1 || true
        log "Service stopped and disabled"
    fi
    rm -f "$SERVICE_PATH"
    log "Removed $SERVICE_PATH"
}

if [[ ! -f "$SCRIPT_PATH" ]]; then
    log "campnet_autologin.py not found in $SCRIPT_DIR"
    exit 1
fi

if [[ "${1:-}" == "--remove" ]]; then
    stop_and_remove
    exit 0
fi

ensure_python
install_deps
write_service
reload_and_enable

log "campnet_autologin.py will now run in background and on login."
log "If you log out and systemd user services stop, enable lingering via: loginctl enable-linger $USER"