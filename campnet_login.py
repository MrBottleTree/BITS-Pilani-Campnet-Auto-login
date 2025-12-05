from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import requests
import urllib3
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CREDENTIALS_FILE = "credentials.json"
LOGIN_TIMEOUT_SECONDS = 10

load_dotenv(BASE_DIR / ".env", override=False)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGIN_URL = "https://campnet.bits-goa.ac.in:8090/login.xml"
@dataclass(frozen=True)
class Credential:
    username: str
    password: str


def _read_credentials_file(path: Path) -> list[Credential]:
    with path.open("r", encoding="utf-8") as file:
        raw = json.load(file)

    entries = raw.get("credentials") if isinstance(raw, dict) else raw
    if not isinstance(entries, list):
        raise ValueError(f"Expected a list of credentials in {path}")

    credentials: list[Credential] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Credential #{index + 1} is not a mapping in {path}")

        username = entry.get("username") or entry.get("uname")
        password = entry.get("password") or entry.get("pwd")
        if not username or not password:
            raise ValueError(f"Credential #{index + 1} missing username/password in {path}")

        credentials.append(Credential(str(username), str(password)))

    return credentials


def load_credentials() -> list[Credential]:
    env_credentials_file = os.getenv("CREDENTIALS_FILE") or os.getenv(
        "CAMPUS_CREDENTIALS_FILE"
    )

    candidate_paths = []
    if env_credentials_file:
        candidate_paths.append(Path(env_credentials_file))
    candidate_paths.append(BASE_DIR / DEFAULT_CREDENTIALS_FILE)

    seen: set[Path] = set()
    for candidate in candidate_paths:
        resolved = candidate if candidate.is_absolute() else BASE_DIR / candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        if not resolved.exists():
            continue
        try:
            credentials = _read_credentials_file(resolved)
            if credentials:
                return credentials
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Failed to read credentials from {resolved}: {exc}")

    username = os.getenv("UNAME")
    password = os.getenv("PWD")
    if username and password:
        return [Credential(username=username, password=password)]

    raise RuntimeError(
        "No credentials found. Create credentials.json (see credentials.json.example) "
        "or set UNAME/PWD in a .env file."
    )


def login_with_credential(credential: Credential) -> Tuple[bool, str]:
    ts = int(time.time() * 1000)
    payload = {
        "mode": "191",
        "username": credential.username,
        "password": credential.password,
        "a": ts,
        "producttype": "0",
    }
    try:
        resp = requests.post(LOGIN_URL, data=payload, verify=False, timeout=LOGIN_TIMEOUT_SECONDS)
        text = resp.text.lower()
    except Exception as exc:  # pylint: disable=broad-except
        return False, f"network error: {exc}"

    if "successfully" in text or "logged in" in text:
        return True, "login successful"

    if "already" in text and ("login" in text or "logged" in text):
        return True, "already logged in"

    if "password" in text and "invalid" in text:
        return False, "invalid username/password"

    return False, f"unexpected response: {resp.text[:200]}"


def login(credentials: Iterable[Credential] | None = None) -> tuple[bool, Credential | None, str]:
    credentials_to_try = list(credentials) if credentials is not None else load_credentials()
    if not credentials_to_try:
        return False, None, "no credentials supplied"

    last_reason = "no attempts made"
    for credential in credentials_to_try:
        success, reason = login_with_credential(credential)
        last_reason = reason
        if success:
            return True, credential, reason

    return False, None, last_reason


if __name__ == "__main__":
    ok, used_credential, message = login()
    if ok:
        print(f"Login OK for {used_credential.username if used_credential else 'unknown user'} ({message})")
    else:
        print(f"Login failed: {message}")
