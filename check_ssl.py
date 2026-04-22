#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import socket
import ssl
import sys
import tempfile
from datetime import datetime, timezone

# ==========================================================
# check_ssl.py - Géniaut Gérald - 22/04/2026
#
# Plugin Centreon / Nagios
#
# Vérifie la date d'expiration d'un certificat SSL/TLS
#
# Modes :
#   strict    = validation complète de la chaîne SSL
#   insecure  = ignore les erreurs de chaîne / CA
#
# Usage Centreon :
#
# $USER1$/check_ssl.py \
#   --hostname=$_SERVICEURL$ \
#   --warning=$_SERVICEWARNING$ \
#   --critical=$_SERVICECRITICAL$ \
#   --mode $ARG3$
#
# Valeurs ARG3 :
#   strict
#   insecure
#
# Codes retour :
#   0 OK
#   1 WARNING
#   2 CRITICAL
#   3 UNKNOWN
# ==========================================================


def nagios_exit(state, message):
    codes = {
        "OK": 0,
        "WARNING": 1,
        "CRITICAL": 2,
        "UNKNOWN": 3
    }

    print(f"{state} - {message}")
    sys.exit(codes[state])


def get_certificate(hostname, insecure=False):
    """
    Récupère le certificat distant.
    """

    try:
        if insecure:
            context = ssl._create_unverified_context()
        else:
            context = ssl.create_default_context()

        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:

                # Mode strict : lecture normale
                if not insecure:
                    cert = ssock.getpeercert()

                    if not cert:
                        raise Exception("Aucun certificat recu")

                    return cert

                # Mode permissif :
                # getpeercert() retourne parfois {}
                # donc on lit le binaire DER
                der_cert = ssock.getpeercert(binary_form=True)

                if not der_cert:
                    raise Exception("Aucun certificat recu")

                pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)

                with tempfile.NamedTemporaryFile(mode="w", delete=True) as tmp:
                    tmp.write(pem_cert)
                    tmp.flush()

                    cert = ssl._ssl._test_decode_cert(tmp.name)

                return cert

    except socket.timeout:
        raise Exception("Connection timeout")

    except socket.gaierror:
        raise Exception("Erreur de resolution DNS")


def parse_expiry(cert):
    """
    Extrait la date d'expiration.
    """

    if "notAfter" not in cert:
        raise Exception("Impossible de lire la date d'expiration du certificat")

    return datetime.strptime(
        cert["notAfter"],
        "%b %d %H:%M:%S %Y %Z"
    ).replace(tzinfo=timezone.utc)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--hostname",
        required=True,
        help="Hostname to check"
    )

    parser.add_argument(
        "--warning",
        type=int,
        default=30,
        help="Warning threshold in days"
    )

    parser.add_argument(
        "--critical",
        type=int,
        default=10,
        help="Critical threshold in days"
    )

    parser.add_argument(
        "--mode",
        default="strict",
        help="strict or insecure"
    )

    args = parser.parse_args()

    hostname = args.hostname
    warning = args.warning
    critical = args.critical
    mode = args.mode.lower()

    insecure = (mode == "insecure")

    try:
        cert = get_certificate(hostname, insecure)

        expiry_date = parse_expiry(cert)

        now = datetime.now(timezone.utc)

        days_left = (expiry_date - now).days

        perfdata = (
            f"days_remaining={days_left};"
            f"{warning};"
            f"{critical};0;"
        )

        display_mode = "PERMISSIVE" if insecure else "STRICT"

        # Etat Nagios / Centreon
        if days_left < 0:
            nagios_exit(
                "CRITICAL",
                f"[{display_mode}] "
                f"Certificate expired {-days_left} days ago "
                f"| {perfdata}"
            )

        elif days_left <= critical:
            nagios_exit(
                "CRITICAL",
                f"[{display_mode}] "
                f"Certificate expires in {days_left} days "
                f"| {perfdata}"
            )

        elif days_left <= warning:
            nagios_exit(
                "WARNING",
                f"[{display_mode}] "
                f"Certificate expires in {days_left} days "
                f"| {perfdata}"
            )

        else:
            nagios_exit(
                "OK",
                f"[{display_mode}] "
                f"Certificate valid for {days_left} days "
                f"| {perfdata}"
            )

    except ssl.SSLError as err:
        nagios_exit("CRITICAL", f"SSL error: {err}")

    except Exception as err:
        nagios_exit("UNKNOWN", str(err))


if __name__ == "__main__":
    main()
