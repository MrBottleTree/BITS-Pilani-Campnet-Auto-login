import time
import datetime
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import requests
from requests import RequestException

from campnet_login import login

BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "campnet_autologin.log"

CHECK_URLS = (
    "http://clients3.google.com/generate_204",
    "http://connectivitycheck.gstatic.com/generate_204",
)
CHECK_INTERVAL_SECONDS = 10
RETRY_INTERVAL_SECONDS = 10
POST_LOGIN_VERIFY_DELAY_SECONDS = 5
FORCE_LOGIN_INTERVAL_SECONDS = 300
PROBE_HEADERS = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

logger = logging.getLogger("campnet-autologin")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = RotatingFileHandler(LOG_PATH, maxBytes=512 * 1024, backupCount=1)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False


def is_logged_in() -> tuple[bool, str]:
    for url in CHECK_URLS:
        try:
            response = requests.get(
                url,
                timeout=5,
                allow_redirects=True,
                headers=PROBE_HEADERS,
            )
        except RequestException as exc:
            logger.debug("Probe %s raised %s", url, exc)
            continue

        final_url = response.url
        text = response.text.strip()
        text_lower = text.lower()

        if response.status_code == 204 and final_url == url:
            return True, "204 with no redirect"

        if response.status_code == 200 and final_url == url and not text:
            return True, "200 with empty body"

        if response.status_code == 200 and final_url == url and text_lower == "success":
            return True, "200 success marker"

        if final_url != url:
            return False, f"redirected to {final_url} ({response.status_code})"

        if "<html" in text_lower or "<!doctype" in text_lower:
            return False, "html portal content"

        if "campnet" in text_lower or "login" in text_lower:
            return False, "portal text detected"

        logger.debug(
            "Probe %s unexpected response %s len=%s", url, response.status_code, len(text)
        )

    return False, "all probes inconclusive"


def attempt_login() -> bool:
    success = login()
    if success:
        logger.info("Login attempt reported success")
    else:
        logger.warning("Login attempt did not confirm success")
    return success


def main() -> None:
    logger.info("Watcher started at %s", datetime.datetime.now().isoformat())
    last_success = 0.0

    while True:
        logged_in, reason = is_logged_in()
        if logged_in:
            if last_success and time.time() - last_success >= FORCE_LOGIN_INTERVAL_SECONDS:
                logger.info("Force refreshing session after %ss", FORCE_LOGIN_INTERVAL_SECONDS)
                if attempt_login():
                    last_success = time.time()
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        logger.warning("Connectivity probe indicates logout (%s); attempting login", reason)
        if attempt_login():
            last_success = time.time()
            time.sleep(POST_LOGIN_VERIFY_DELAY_SECONDS)
            continue

        logger.warning("Login attempt failed; retrying in %ss", RETRY_INTERVAL_SECONDS)
        time.sleep(RETRY_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()

