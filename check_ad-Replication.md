# Centreon Plugin - Active Directory Replication Health

## Description

Ce plugin Centreon/Nagios supervise l'état de la réplication Active Directory en interrogeant directement l'outil Microsoft **repadmin** via **WinRM**.

Contrairement à certaines vérifications basées sur `dcdiag`, cette méthode s'appuie sur :

```text
repadmin /replsummary
```

qui fournit une vision globale de la santé de la réplication de l'ensemble de la forêt Active Directory.

Le plugin détecte :

* Les erreurs de réplication entre contrôleurs de domaine.
* Les liens de réplication en échec.
* Les retards de réplication anormaux.
* Les contrôleurs de domaine injoignables.

---

## Pourquoi utiliser repadmin ?

Les tests :

```text
dcdiag /test:Replications
```

ou

```text
dcdiag /test:KnowsOfRoleHolders
```

peuvent produire des faux positifs lorsqu'ils sont exécutés avec un compte de supervision ne disposant pas de tous les privilèges AD.

À l'inverse :

```text
repadmin /replsummary
```

s'appuie directement sur les mécanismes de réplication Active Directory et fournit un résultat beaucoup plus fiable pour la supervision.

---

## Fonctionnement

Le plugin exécute :

```text
repadmin /replsummary
```

sur un contrôleur de domaine.

Le résultat contient la synthèse de réplication de l'ensemble des DC de la forêt.

Exemple :

```text
DSA source             différence max    nb échecs %% erreur

DC1                       20m:25s    0 / 10    0
DC2                       19m:51s    0 / 10    0
DC3                       20m:24s    0 / 10    0
DC4                       20m:25s    0 / 10    0
DC5                       20m:24s    0 / 10    0
```

---

## États retournés

### OK

Aucune erreur de réplication détectée.

Exemple :

```text
OK - AD Replication OK (0 failure(s) on 20 replication link(s))
```

---

### WARNING

Le nombre d'échecs est faible mais non nul.

Exemple :

```text
WARNING - AD Replication Warning (1 failure on 20 replication links)
```

---

### CRITICAL

Un ou plusieurs liens de réplication sont en échec.

Exemple :

```text
CRITICAL - AD Replication FAILED (5 failures on 20 replication links)
```

---

### UNKNOWN

Le contrôleur de domaine ne répond pas via WinRM ou la commande ne peut être exécutée.

Exemple :

```text
UNKNOWN - WinRM connection failed
```

---

## Prérequis Centreon

### Python

Testé avec :

```text
Python 3.11
```

### Bibliothèques Python

Installation dans l'environnement Centreon :

```bash
source /opt/centreon-python/bin/activate

pip install pywinrm requests requests-ntlm
```

---

## Configuration OpenSSL

Créer :

```bash
/etc/centreon/openssl-ntlm.cnf
```

Contenu :

```ini
openssl_conf = openssl_init

[openssl_init]
providers = provider_sect

[provider_sect]
default = default_sect
legacy = legacy_sect

[default_sect]
activate = 1

[legacy_sect]
activate = 1
```

Cette configuration est nécessaire sur certaines distributions Linux utilisant OpenSSL 3 avec l'authentification NTLM.

---

## Prérequis Active Directory

### Activation WinRM

Sur chaque contrôleur de domaine :

```powershell
Enable-PSRemoting -Force
```

Vérification :

```powershell
Test-WsMan localhost
```

---

### Authentification WinRM

Vérifier :

```powershell
winrm get winrm/config/service/auth
```

Les paramètres suivants doivent être activés :

```text
Basic = true
Kerberos = true
Negotiate = true
```

---

### Compte de supervision

Créer un compte dédié :

```text
SC\centreon
```

Le compte doit pouvoir :

* Ouvrir une session PowerShell distante.
* Exécuter repadmin.
* Lire les informations Active Directory.

Selon les délégations en place, il peut être nécessaire de l'ajouter :

```text
Administrateurs
```

ou

```text
Utilisateurs de gestion à distance
```

---

## Utilisation

Exemple :

```bash
./check_ad_replication.py \
    -H 10.73.24.1 \
    -u "centreon@geniaut.fr" \
    -p "MotDePasse"
```

---

## Exemple de commande Centreon

```bash
$USER1$/check_ad_replication.py \
    -H '$HOSTADDRESS$' \
    -u '$ARG1$' \
    -p '$ARG2$'
```

Exemple :

```text
check_AD-Replication!SC\centreon!MotDePasse
```

---

## Déploiement recommandé

Un seul service Centreon est généralement suffisant.

En effet :

```text
repadmin /replsummary
```

retourne déjà l'état de réplication de l'ensemble des contrôleurs de domaine de la forêt.

Exemple :

```text
DC4
DC5
DC6
DC7
DC8
```

Il n'est donc pas nécessaire de créer un contrôle sur chaque DC.

Un seul contrôle exécuté sur un contrôleur de domaine sain permet de superviser toute la réplication Active Directory.

---

## Technologies concernées

* Microsoft Active Directory
* WinRM
* PowerShell Remoting
* Repadmin
* Centreon
* Nagios

---

## Auteur

Gérald Géniaut

RSSI – Crous de Paris
