#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/campnet_autologin.py"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="campnet_autologin.service"
SERVICE_PATH="$SERVICE_DIR/$SERVICE_NAME"
PYTHON_BIN="${PYTHON_BIN:-"$(command -v python3 || true)"}"

log() { printf '[campnet-autologin] %s\n' "$*"; }

detect_missing_modules() {
    "$PYTHON_BIN" - <<'PY'
import importlib.util
mods = ["requests", "dotenv"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
print(" ".join(missing))
PY
}

ensure_python() {
    if [[ -z "$PYTHON_BIN" ]]; then
        log "python3 not found on PATH. Set PYTHON_BIN=/path/to/python and rerun."
        exit 1
    fi
}

install_deps() {
    if [[ -n "${SKIP_PIP:-}" ]]; then
        log "SKIP_PIP set; assuming dependencies are installed"
        return
    fi
    missing_modules="$(detect_missing_modules)"
    if [[ -z "$missing_modules" ]]; then
        log "Dependencies already present; skipping pip install"
        return
    fi

    log "Installing/upgrading required Python packages ($missing_modules)"
    err_log="$(mktemp)"
    if ! "$PYTHON_BIN" -m pip install --user --upgrade $missing_modules 2>"$err_log"; then
        if grep -q "externally-managed-environment" "$err_log"; then
            log "pip refused (externally managed env). Install via: sudo apt install python3-requests python3-dotenv"
        else
            log "pip install failed; see $err_log"
        fi
    fi
    rm -f "$err_log"
}

enable_linger() {
    if ! command -v loginctl >/dev/null 2>&1; then
        log "loginctl not found; skipping linger enablement (user services may stop on logout)"
        return
    fi

    if loginctl show-user "$USER" 2>/dev/null | grep -q "Linger=yes"; then
        log "User lingering already enabled for $USER"
        return
    fi

    if loginctl enable-linger "$USER"; then
        log "Enabled lingering for $USER (user services will start at boot and survive logout)"
    else
        log "Could not enable lingering for $USER; user services may stop on logout"
    fi
}

write_service() {
    mkdir -p "$SERVICE_DIR"
    cat >"$SERVICE_PATH" <<SERVICE
[Unit]
Description=Campnet Autologin
After=default.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR
ExecStart=$PYTHON_BIN $SCRIPT_PATH
Restart=always
RestartSec=3

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
enable_linger
write_service
reload_and_enable

log "campnet_autologin.py will now run in background and on login."
log "If user services still stop on logout, run: loginctl enable-linger $USER"
