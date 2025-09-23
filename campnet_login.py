import requests
import time
import urllib3
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGIN_URL = "https://campnet.bits-goa.ac.in:8090/login.xml"
username = os.getenv("UNAME")
pwd = os.getenv("PWD")


def login() -> bool:
    ts = int(time.time() * 1000)
    payload = {"mode": "191", "username": username, "password": pwd, "a": ts, "producttype": "0"}
    try:
        resp = requests.post(LOGIN_URL, data=payload, verify=False, timeout=10)
        text = resp.text.lower()
    except Exception as exc:
        print("Error:", exc)
        return False

    if "successfully" in text or "logged in" in text:
        print("Login OK")
        return True

    if "already" in text and ("login" in text or "logged" in text):
        print("Already logged in")
        return True

    print("Response:", resp.text[:200])
    return False


if __name__ == "__main__":
    login()

