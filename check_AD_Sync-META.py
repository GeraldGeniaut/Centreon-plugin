#!/opt/centreon-python/bin/python3

import os
os.environ["OPENSSL_CONF"] = "/etc/centreon/openssl-ntlm.cnf"

import winrm
import argparse
import json
import sys
import warnings

warnings.filterwarnings(
    "ignore",
    message="There was a problem converting the Powershell error message*"
)


OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


def parse_args():
    parser = argparse.ArgumentParser(
        description="Centreon Plugin - PCNSSVC Monitoring via WinRM"
    )

    parser.add_argument(
        "-H", "--host",
        required=True,
        help="Nom ou IP du DC"
    )

    parser.add_argument(
        "-u", "--username",
        required=True,
        help="Compte DOMAIN\\user"
    )

    parser.add_argument(
        "-p", "--password",
        required=True,
        help="Mot de passe"
    )

    parser.add_argument(
        "--hours",
        type=int,
        default=48,
        help="Fenêtre d'analyse en heures (défaut : 48)"
    )

    parser.add_argument(
        "--ssl",
        action="store_true",
        help="Utiliser HTTPS (5986)"
    )

    return parser.parse_args()


def create_session(host, username, password, use_ssl=False):

    protocol = "https" if use_ssl else "http"
    port = 5986 if use_ssl else 5985

    return winrm.Session(
        f"{protocol}://{host}:{port}/wsman",
        auth=(username, password),
        transport="ntlm",
        server_cert_validation="ignore"
    )


def get_events(session, hours):

    ps_script = f"""
$since=(Get-Date).AddHours(-{hours})

Get-EventLog -LogName Application -Source PCNSSVC -Newest 1000 |
Where-Object {{ $_.TimeGenerated -gt $since }} |
Select @{{
           Name='TimeGenerated'
           Expression={{ $_.TimeGenerated.ToString("yyyy-MM-dd HH:mm:ss") }}
       }},
       EventID,
       EntryType,
       @{{
           Name='Message'
           Expression={{
               $_.Message `
                   -replace "`r"," " `
                   -replace "`n"," " `
                   -replace "\\s+"," "
           }}
       }} |
ConvertTo-Json -Depth 4 -Compress
"""

    result = session.run_ps(ps_script)

    stdout = result.std_out.decode("utf-8", errors="replace")
    stderr = result.std_err.decode("utf-8", errors="replace")

    return result.status_code, stdout, stderr


def main():

    args = parse_args()

    username = args.username.replace("\\\\", "\\")

    try:

        session = create_session(
            args.host,
            username,
            args.password,
            args.ssl
        )

        rc, stdout, stderr = get_events(session, args.hours)

        if rc != 0:
            print(f"UNKNOWN - PowerShell returned {rc}: {stderr}")
            sys.exit(UNKNOWN)

        if not stdout.strip():
            print(
                f"WARNING - Aucun événement PCNSSVC trouvé "
                f"depuis {args.hours} heures"
            )
            sys.exit(WARNING)

        events = json.loads(stdout)

        if isinstance(events, dict):
            events = [events]

        errors = []

        for event in events:

            entry_type = str(event.get("EntryType", "")).lower()

            if entry_type == "error":

                msg = event.get("Message", "")

                msg = msg.replace("\r", " ")
                msg = msg.replace("\n", " ")

                if len(msg) > 250:
                    msg = msg[:250] + "..."

                errors.append(
                    f"EventID={event.get('EventID')} : {msg}"
                )

        if errors:

            print(
                "CRITICAL - PCNSSVC Error(s) detected : "
                + " | ".join(errors[:3])
            )

            sys.exit(CRITICAL)

        latest = max(events, key=lambda e: e["TimeGenerated"])

        print(
            f"OK - PCNSSVC OK "
            f"({len(events)} événements sur {args.hours}h, "
            f"dernière activité={latest['TimeGenerated']})"
        )

        sys.exit(OK)

    except Exception as e:

        print(f"UNKNOWN - {e}")
        sys.exit(UNKNOWN)


if __name__ == "__main__":
    main()
