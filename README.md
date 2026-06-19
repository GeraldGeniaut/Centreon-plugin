Ensemble de plugins Centreon


-- ard_checksalle.py : Permet de relever les badges qui ont ouvert ou tenté d'ouvrir une porte (filtre par le nom de la porte). 

-- ard_checkalarms.py : Permet d'alerter sur les Alarmes déclanché dans ARD (defaut technique)

-- Active Directory Comptes Locked : fichier php à completer (lien sur fichier de connexion & base URL de recherche). Ce fichier est appelé par le script pyhton qui est à implémenter dans centreon. 

-- check_nfs.py : Check connexion NFS over ssh (Prérequis : une clef ssh pour un accès root à l'utilisateur centreon-engine). 

-- check_ssl.py : Permet de vérifier la validité d'un SSL (soit strict mode soit mode insecure pour palier les pbs de chaines mals formées)

-- etc... (voir les fichiers script.md )
