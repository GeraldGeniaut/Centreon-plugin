#!/usr/bin/env python3
import requests
import hashlib
import time
import sys
import argparse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------------
# ARGUMENTS
# -------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--url", required=True)
parser.add_argument("--user", required=True)
parser.add_argument("--password", required=True)
parser.add_argument("--critical", type=int, default=1)
parser.add_argument("--warning", type=int, default=0)

args = parser.parse_args()

base = args.url.rstrip("/")
user = args.user
password = args.password

# -------------------------
# SESSION HTTP
# -------------------------
session = requests.Session()
session.verify = False  # SSL OFF

headers = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}

# -------------------------
# 1. CHALLENGE
# -------------------------
try:
    response = session.post(
        f"{base}/index.php?i=1",
        data={
            "eID": "tx_ardviewhelpers_challenge",
            "t": int(time.time() * 1000)
        },
        headers=headers
    )

    data = response.json()
    challenge = data.get("challenge")

    if not challenge:
        print("CRITICAL - Impossible de récupérer le challenge")
        sys.exit(2)

except Exception as e:
    print(f"CRITICAL - Erreur challenge: {e}")
    sys.exit(2)

# -------------------------
# 2. LOGIN
# -------------------------
try:
    hash_pass = hashlib.md5(
        f"{user}:{hashlib.md5(password.encode()).hexdigest()}:{challenge}".encode()
    ).hexdigest()

    response = session.post(
        f"{base}/index.php?i=1&t={int(time.time()*1000)}",
        data={
            "eID": "tx_ardviewhelpers_login",
            "user": user,
            "password": hash_pass,
            "challenge": challenge,
            "pid": 5
        },
        headers=headers
    )

    if '"success":true' not in response.text:
        print("CRITICAL - Authentification échouée")
        sys.exit(2)

except Exception as e:
    print(f"CRITICAL - Erreur login: {e}")
    sys.exit(2)

# -------------------------
# 3. RECUPERATION ALARMES
# -------------------------
try:
    params = {
        "pagesize": 50,
        "orderby": "lastdatetime desc",
        "tca": 1,
        "nostripslashes": 1,
        "page": 1,
        "start": 0,
        "limit": 25,
        "jf": '{"bf":[{"f":"deleted","o":"=","v":0},{"f":"alarmResolved","o":"=","v":0},{"f":"faultlog","o":"=","v":1}]}'
    }

    response = session.get(
        f"{base}/relational/tx_ardaccess_domain_model_alarms",
        params=params,
        headers=headers
    )

    data = response.json()

except Exception as e:
    print(f"CRITICAL - Erreur récupération alarmes: {e}")
    sys.exit(2)

# -------------------------
# 4. SORTIE CENTREON
# -------------------------
alarms = data.get("data", [])

if not alarms:
    print("OK - Aucune alarme")
    sys.exit(0)

count = len(alarms)

# Gestion des seuils
if count >= args.critical:
    status = "CRITICAL"
    exit_code = 2
elif count >= args.warning:
    status = "WARNING"
    exit_code = 1
else:
    status = "OK"
    exit_code = 0

print(f"{status} - {count} alarme(s) active(s)")

for alarm in alarms:
    desc = alarm.get("description", "").strip()
    door = alarm.get("EVAL_doors", "")
    date = alarm.get("EVAL_lastdatetime", "")

    print(f"{desc} - {door} - {date}")

sys.exit(exit_code)
