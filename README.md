# Campnet Auto Login

This project keeps Campnet sessions alive by retrying the captive-portal login whenever connectivity drops. Credentials live in a local `.env` file so the Python scripts can authenticate without manual input.

## Files
- `campnet_login.py` – Single login call against the Campnet portal.
- `campnet_autologin.py` – Background watcher that probes the network and re-logs when needed.
- `setup_autologin.bat` – Starts the watcher immediately and registers it in the Windows Run key for future sign-ins.

## Getting Started
1. Install Python 3 and make sure `python`/`pythonw` are on your `PATH`.
2. Copy `.env.example` to `.env` (or create `.env`) and fill in `UNAME` and `PWD`.
3. Double-click `setup_autologin.bat` (or run it from a shell). It will
   - locate `pythonw.exe` (falls back to `python.exe`),
   - add `CampnetAutoLogin` to `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, and
   - launch the watcher immediately.

Windows will now launch the watcher at every sign-in, and it will retry the Campnet login whenever the portal drops your session. The process sleeps between checks, so it stays lightweight (roughly a single HTTP probe every 10 seconds).

## Removing Autostart
Run `setup_autologin.bat --remove` to delete the Run-key entry. If you just want to stop the current watcher, end the Python process from Task Manager.

## Notes
- Keep `.env` out of version control; commit a `.env.example` file with placeholder values instead.
- The scripts disable SSL verification because the captive portal uses a self-signed certificate. Use the code only on networks you trust.
- Logs live at `campnet_autologin.log` next to the scripts if you need to troubleshoot.