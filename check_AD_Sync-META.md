Centreon Plugin - PCNSSVC (Microsoft Identity Manager Password Synchronization)
Description

Ce plugin Centreon/Nagios permet de superviser le bon fonctionnement du service Password Change Notification Service (PCNS) utilisé par Microsoft Identity Manager (MIM).

Le contrôle est effectué à distance via WinRM sur un contrôleur de domaine Windows et analyse les événements générés par la source PCNSSVC dans le journal Application.

Le plugin permet de détecter :

Les erreurs de synchronisation des changements de mot de passe vers MIM.
Les erreurs RPC empêchant la communication avec le serveur MIM.
Une absence prolongée d'activité PCNSSVC pouvant indiquer un dysfonctionnement.
Fonctionnement

Le plugin interroge les événements PCNSSVC des dernières X heures (48 heures par défaut).

État OK

Le statut est OK si :

Aucun événement d'erreur PCNSSVC n'est détecté.
Au moins un événement PCNSSVC est présent dans la période analysée.

Exemple :

OK - PCNSSVC OK (686 événements sur 48h, dernière activité=2026-06-19 11:02:05)
État WARNING

Le statut est WARNING si :

Aucun événement PCNSSVC n'a été enregistré durant la période analysée.

Exemple :

WARNING - Aucun événement PCNSSVC détecté depuis 48h
État CRITICAL

Le statut est CRITICAL dès qu'un événement d'erreur PCNSSVC est détecté.

Exemple :

CRITICAL - PCNSSVC Error 6025 : Le serveur RPC n'est pas disponible
Prérequis Centreon
Python

Le plugin a été développé et testé avec :

Python 3.11
Bibliothèques Python

Installation dans l'environnement Python Centreon :

source /opt/centreon-python/bin/activate

pip install pywinrm requests requests-ntlm

Vérification :

python3 -c "import winrm"
Configuration OpenSSL

Créer le fichier :

/etc/centreon/openssl-ntlm.cnf

Contenu :

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

Cette configuration est nécessaire sur certaines distributions Linux utilisant OpenSSL 3 afin d'autoriser l'authentification NTLM.

Prérequis Active Directory
Activation WinRM

Sur chaque contrôleur de domaine :

Enable-PSRemoting -Force

Vérification :

Test-WsMan localhost
Authentification WinRM

Vérifier :

winrm get winrm/config/service/auth

Les paramètres suivants doivent être activés :

Basic = true
Kerberos = true
Negotiate = true
Compte de supervision

Créer un compte dédié, par exemple :

SC\centreon

Le compte doit :

Pouvoir ouvrir une session PowerShell distante.
Avoir accès au journal Application.
Être autorisé à exécuter les commandes PowerShell utilisées par le plugin.

Selon la configuration de sécurité de l'environnement, il peut être nécessaire d'ajouter temporairement le compte au groupe :

Administrateurs

ou

Utilisateurs de gestion à distance
Utilisation

Exemple :

./check_AD_Sync-META.py \
    -H 10.249.192.9 \
    -u "SC\\centreon" \
    -p "MotDePasse"
Exemple de commande Centreon
$USER1$/check_AD_Sync-META.py \
    -H '$HOSTADDRESS$' \
    -u '$ARG1$' \
    -p '$ARG2$'

Exemple :

check_AD_Sync-META!SC\centreon!MotDePasse
Déploiement recommandé

Créer un service Centreon sur chaque contrôleur de domaine :

DC4
DC5
DC6
DC7
DC8

Cela permet d'identifier immédiatement quel contrôleur de domaine rencontre un problème de synchronisation avec MIM.

Technologies concernées
Centreon
Nagios
Microsoft Active Directory
Microsoft Identity Manager (MIM)
Password Change Notification Service (PCNS)
WinRM
PowerShell Remoting
Auteur

Gérald Géniaut
