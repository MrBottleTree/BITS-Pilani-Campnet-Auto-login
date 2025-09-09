import requests
import time
import urllib3
import os
from dotenv import load_dotenv
load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGIN_URL = "https://campnet.bits-goa.ac.in:8090/login.xml"
username = os.getenv("UNAME")
pwd = os.getenv("PWD")

def login():
    ts = int(time.time() * 1000)
    payload = {"mode": "191", "username": username, "password": pwd, "a": ts, "producttype": "0"}
    try:
        resp = requests.post(LOGIN_URL, data=payload, verify=False, timeout=10)
        if "successfully" in resp.text.lower() or "logged in" in resp.text.lower():
            print("Login OK")
        else:
            print("Response:", resp.text[:200])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    login()