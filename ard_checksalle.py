#!/usr/bin/env python3

# Monitoring badges ARD v2.2 - 2026/03/19 - Géniaut Gérald pour le Crous de Paris
# https://github.com/GeraldGeniaut
# ------------------------------------------------
# Usage : ard_checksalle.py [-h] --url URL --user USER --password PASSWORD --door DOOR [--warning WARNING] [--critical CRITICAL]
#-------------------------------------------------


import requests
import hashlib
import sys
import time
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
parser.add_argument("--door", required=True)

parser.add_argument("--warning", type=int, default=None)
parser.add_argument("--critical", type=int, default=1)

args = parser.parse_args()

base = args.url
user = args.user
password = args.password
door_filter = args.door
warn_threshold = args.warning
crit_threshold = args.critical

# -------------------------
# SESSION
# -------------------------
session = requests.Session()
session.verify = False

# -------------------------
# 1. CHALLENGE
# -------------------------
r = session.post(f"{base}/index.php?i=1", data={
    "eID": "tx_ardviewhelpers_challenge",
    "t": int(time.time() * 1000)
})

data = r.json()

if "challenge" not in data:
    print("UNKNOWN - Challenge KO")
    sys.exit(3)

challenge = data["challenge"]

# -------------------------
# 2. LOGIN
# -------------------------
hash_val = hashlib.md5(f"{user}:{hashlib.md5(password.encode()).hexdigest()}:{challenge}".encode()).hexdigest()

r = session.post(f"{base}/index.php?i=1", data={
    "eID": "tx_ardviewhelpers_login",
    "user": user,
    "password": hash_val,
    "challenge": challenge,
    "pid": 5
})

if '"success":true' not in r.text:
    print("CRITICAL - Authentification échouée")
    sys.exit(2)

# -------------------------
# 3. EVENTS
# -------------------------
params = {
    "pagesize": 20,
    "orderby": "crdate desc",
    "tca": 1,
    "nostripslashes": 1,
    "page": 1,
    "start": 0,
    "limit": 20,
    "jf": '{"bf":[{"f":"eventtype","o":"=","v":40}]}'
}

r = session.get(f"{base}/relational/tx_ardaccess_domain_model_events", params=params)
data = r.json()

if "data" not in data:
    print("UNKNOWN - Réponse invalide")
    sys.exit(3)

# -------------------------
# 4. FILTRAGE
# -------------------------
count = 0
last_msg = ""

for event in data["data"]:
    door = event.get("EVAL_deviceid", "")

    if door_filter.lower() in door.lower():
        count += 1

        user_evt = event.get("EVAL_userid", "Inconnu")
        date_evt = event.get("EVAL_tstamp", "Date inconnue")
        desc = event.get("description", "").strip()

        last_msg = f"{desc} : {user_evt} sur {door} à {date_evt}"

# -------------------------
# 5. SEUILS
# -------------------------
if count == 0:
    print(f"OK - Aucun badge sur {door_filter}")
    sys.exit(0)

if warn_threshold is not None and count >= warn_threshold and count < crit_threshold:
    print(f"WARNING - {count} badge(s) sur {door_filter} - {last_msg}")
    sys.exit(1)

if count >= crit_threshold:
    print(f"CRITICAL - {count} badge(s) sur {door_filter} - {last_msg}")
    sys.exit(2)

print(f"OK - {count} badge(s) sur {door_filter}")
sys.exit(0)
