#!/usr/bin/env python3
import subprocess
import argparse
import sys

def run_ssh_command(host, command, ssh_user="root", ssh_key="/var/lib/centreon-engine/.ssh/centreon"):
    """
    Exécute une commande SSH sur un hôte distant avec un timeout et une clé privée.
    """
    ssh_cmd = [
        "ssh",
        "-i", ssh_key,
        "-o", "HostKeyAlgorithms=ssh-ed25519",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=5",
        f"{ssh_user}@{host}",
        command
    ]
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        return (result.returncode, result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        return (3, "", "Timeout lors de la connexion SSH.")

def check_remote_nfs_mount(host, mount_point, server, ssh_user="root", ssh_key="/root/.ssh/centreon"):
    """
    Vérifie à distance si un montage NFS est fonctionnel, avec détection des blocages.
    """
    # 1. Vérifier que le montage est de type NFS et actif
    return_code, stdout, stderr = run_ssh_command(host, f"mount | grep '{mount_point}' | grep -c 'type nfs'")
    if return_code != 0:
        return (3, f"UNKNOWN: Impossible de vérifier les montages sur {host} ({stderr}).")
    if "1" not in stdout.strip():
        return (2, f"CRITICAL: {mount_point} n'est pas monté ou n'est pas de type NFS sur {host}.")

    # 2. Tester la connectivité NFS (rpcinfo)
    return_code, stdout, stderr = run_ssh_command(host, f"rpcinfo -t {server} nfs 2>&1")
    if return_code != 0:
        return (2, f"CRITICAL: Service NFS non disponible sur {server} ({stderr}).")

    # 3. Tester ls -l avec un timeout court pour détecter les blocages
    return_code, stdout, stderr = run_ssh_command(host, f"timeout 5 ls -l {mount_point} >/dev/null 2>&1")
    if return_code != 0:
        return (2, f"CRITICAL: Impossible de lister {mount_point} (blocage ou timeout).")

    # 4. Tester l'écriture/suppression
    return_code, stdout, stderr = run_ssh_command(
        host,
        f"touch {mount_point}/.nfs_check_tmp 2>/dev/null && rm -f {mount_point}/.nfs_check_tmp 2>/dev/null"
    )
    if return_code == 0:
        return (0, f"OK: {mount_point} est accessible et fonctionnel sur {host}.")
    else:
        return (2, f"CRITICAL: Impossible d'écrire/supprimer dans {mount_point} sur {host} ({stderr}).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vérifie l'état d'un montage NFS à distance pour Centreon/Nagios.")
    parser.add_argument("--host", required=True, help="Adresse IP ou nom d'hôte du serveur cible.")
    parser.add_argument("--mount-point", required=True, help="Chemin du point de montage NFS.")
    parser.add_argument("--server", required=True, help="Adresse ou nom du serveur NFS.")
    parser.add_argument("--ssh-user", default="root", help="Utilisateur SSH (par défaut: root).")
    parser.add_argument("--ssh-key", default="/root/.ssh/centreon", help="Chemin vers la clé SSH privée.")
    args = parser.parse_args()

    code, message = check_remote_nfs_mount(
        args.host,
        args.mount_point,
        args.server,
        args.ssh_user,
        args.ssh_key
    )
    print(message)
    sys.exit(code)
