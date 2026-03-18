#!/usr/bin/env python3
import requests
import sys
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument("--url", required=True)
parser.add_argument("--warning", type=int, default=60)   # en secondes
parser.add_argument("--critical", type=int, default=300) # en secondes

args = parser.parse_args()

now = int(time.time())

try:
    r = requests.get(args.url, timeout=10, verify=False)
    data = r.json()

    users = data.get("users", [])

except Exception as e:
    print(f"CRITICAL - Erreur récupération: {e}")
    sys.exit(2)

if not users:
    print("OK - Aucun compte verrouillé")
    sys.exit(0)

status = "OK"
exit_code = 0
messages = []

for u in users:
    username = u.get("user")
    lock_time = int(u.get("lock_time", 0))

    if lock_time == 0:
        continue

    duration = now - lock_time

    # 👉 logique temporelle
    if duration >= args.critical:
        status = "CRITICAL"
        exit_code = 2
    elif duration >= args.warning and status != "CRITICAL":
        status = "WARNING"
        exit_code = 1

    minutes = duration // 60
    seconds = duration % 60
    messages.append(f"{username} ({minutes}m {seconds}s)")

# -------------------------
# SORTIE
# -------------------------
print(f"{status} - {len(users)} compte(s) verrouillé(s) : " + ", ".join(messages[:5]))

sys.exit(exit_code)
