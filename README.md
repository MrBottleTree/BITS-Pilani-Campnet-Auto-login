# Campnet Auto Login

This project keeps Campnet sessions alive by retrying the captive-portal login whenever connectivity drops. You can store multiple credentials in `credentials.json` and the scripts will try each until one succeeds, falling back to `.env` for single-credential setups.

## Files
- `campnet_login.py` – Single login call against the Campnet portal.
- `campnet_autologin.py` – Background watcher that probes the network and re-logs when needed.
- `credentials.json.example` – Template for one or more username/password pairs.
- `.env.example` – Legacy single-credential template (`UNAME`/`PWD`).
- `setup_autologin.bat` – Windows helper that starts the watcher immediately and registers it in the Run key.
- `setup_autologin.sh` – Linux helper that installs a systemd user service for the watcher.

## Getting Started (Windows)
1. Install Python 3 and make sure `python`/`pythonw` are on your `PATH`.
2. Copy `credentials.json.example` to `credentials.json` and fill in your username/password pairs (first entry is tried first). If you prefer the old single-credential flow, copy `.env.example` to `.env` instead.
3. Double-click `setup_autologin.bat` (or run it from a shell). It will
   - locate `pythonw.exe` (falls back to `python.exe`),
   - add `CampnetAutoLogin` to `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, and
   - launch the watcher immediately.

Windows will now launch the watcher at every sign-in, and it will retry the Campnet login whenever the portal drops your session. The process sleeps between checks, so it stays lightweight (roughly a single HTTP probe every 10 seconds).

## Getting Started (Ubuntu/Linux)
1. Ensure Python 3 is available on `PATH`.
2. Copy `credentials.json.example` to `credentials.json` and fill in your credentials. You can list multiple entries for automatic failover; `.env` with `UNAME`/`PWD` still works if you only need one login.
3. Run `bash setup_autologin.sh`. It will
   - (optionally) install/upgrade `requests` and `python-dotenv` with pip,
   - write `~/.config/systemd/user/campnet_autologin.service`,
   - request lingering via `loginctl enable-linger $USER` when available so it also runs after reboot, and
   - `systemctl --user enable --now campnet_autologin.service`.

## Credentials
- Preferred: create `credentials.json` (see `credentials.json.example`) with one or more objects that have `username` and `password` keys. The script tries them in order until a login succeeds.
- Optional: set `CREDENTIALS_FILE=/path/to/other.json` in your environment or `.env` to point at a different file.
- Legacy: `.env` with `UNAME` and `PWD` still works for a single credential if no JSON file is found.

The setup script requests lingering automatically; if user services still stop on logout, rerun `loginctl enable-linger $USER`.

## Removing Autostart
- **Windows:** `setup_autologin.bat --remove`
- **Linux:** `bash setup_autologin.sh --remove`

## Notes
- Keep `.env` out of version control; commit a `.env.example` file with placeholder values instead.
- The scripts disable SSL verification because the captive portal uses a self-signed certificate. Use the code only on networks you trust.
- Logs live at `campnet_autologin.log` next to the scripts if you need to troubleshoot.
