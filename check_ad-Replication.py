#!/opt/centreon-python/bin/python3
# -*- coding: utf-8 -*-

import os
os.environ["OPENSSL_CONF"] = "/etc/centreon/openssl-ntlm.cnf"

import winrm
import argparse
import sys
import re
import time

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


def parse_args():
    parser = argparse.ArgumentParser(
        description="Centreon - Active Directory Replication Check"
    )

    parser.add_argument(
        "-H", "--host",
        required=True,
        help="Contrôleur de domaine"
    )

    parser.add_argument(
        "-u", "--username",
        required=True,
        help="Utilisateur"
    )

    parser.add_argument(
        "-p", "--password",
        required=True,
        help="Mot de passe"
    )

    parser.add_argument(
        "--ssl",
        action="store_true"
    )

    return parser.parse_args()


def run_repadmin(host, username, password, use_ssl=False):

    protocol = "https" if use_ssl else "http"
    port = 5986 if use_ssl else 5985

    session = winrm.Session(
        f"{protocol}://{host}:{port}/wsman",
        auth=(username, password),
        transport="ntlm",
        server_cert_validation="ignore"
    )

    start = time.time()

    result = session.run_cmd(
        "repadmin /replsummary"
    )

    runtime = round(time.time() - start, 1)

    stdout = result.std_out.decode(
        "cp850",
        errors="replace"
    )

    stderr = result.std_err.decode(
        "cp850",
        errors="replace"
    )

    return (
        result.status_code,
        stdout,
        stderr,
        runtime
    )


def parse_repadmin(output):

    critical_dcs = []
    warning_dcs = []

    total_failures = 0
    total_links = 0

    for line in output.splitlines():

        line = line.strip()

        if not line:
            continue

        m = re.search(
            r"([A-Za-z0-9_-]+)\s+"
            r"[\dsmh:]+\s+"
            r"(\d+)\s*/\s*(\d+)\s+"
            r"(\d+)",
            line
        )

        if not m:
            continue

        dc_name = m.group(1)
        failures = int(m.group(2))
        links = int(m.group(3))
        percent = int(m.group(4))

        total_failures += failures
        total_links += links

        if failures > 0:
            critical_dcs.append(
                f"{dc_name}={failures}/{links}"
            )

        elif percent > 0:
            warning_dcs.append(
                f"{dc_name}={percent}%"
            )

    return (
        total_failures,
        total_links,
        critical_dcs,
        warning_dcs
    )


def main():

    args = parse_args()

    try:

        status, stdout, stderr, runtime = run_repadmin(
            args.host,
            args.username,
            args.password,
            args.ssl
        )

    except Exception as e:

        print(
            f"UNKNOWN - WinRM error : {e}"
        )

        sys.exit(UNKNOWN)

    if status != 0:

        print(
            f"UNKNOWN - repadmin exit code {status}"
        )

        sys.exit(UNKNOWN)

    output = stdout + stderr

    (
        total_failures,
        total_links,
        critical_dcs,
        warning_dcs
    ) = parse_repadmin(output)

    if critical_dcs:

        print(
            f"CRITICAL - AD Replication FAILED : "
            f"{', '.join(critical_dcs)}"
        )

        sys.exit(CRITICAL)

    if warning_dcs:

        print(
            f"WARNING - AD Replication warning : "
            f"{', '.join(warning_dcs)}"
        )

        sys.exit(WARNING)

    print(
        f"OK - AD Replication OK "
        f"(0 failure(s) on {total_links} replication link(s), "
        f"runtime={runtime}s)"
    )

    sys.exit(OK)


if __name__ == "__main__":
    main()
