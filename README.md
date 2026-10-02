# Attaque Cryptographique par algorithme MCMC (Metropolis-Hastings)

Projet réalisé dans le cadre du module R5.12 (Modélisations Mathématiques) à l'IUT d'Amiens (BUT Informatique).
Ce programme implémente un algorithme de Monte-Carlo par chaînes de Markov (MCMC) pour décrypter deux chiffrements classiques sans connaître la clé :

1. La substitution mono-alphabétique
2. La permutation (transposition par blocs de 10)

Auteurs : Mathys & Ethan

## Fonctionnalités Avancées

- Analyse par N-grammes (Digrammes & Trigrammes) : Utilisation d'une matrice 3D pour éviter les optimums locaux (anagrammes), avec complexité optimisée via précalcul des log-vraisemblances.
- Modèles Multilingues : Apprentissage statistique dynamique en interrogeant directement l'API Wikipédia (FR, EN, ES, etc.).
- Sources Personnalisées : Ingestion de fichiers locaux .txt pour éprouver la dépendance de l'algorithme à son modèle d'entraînement.
- Interface Graphique (GUI) : Monitoring scientifique en temps réel avec Matplotlib, illustrant la phase de chauffe (Burn-in) et la stabilisation de la chaîne.

## Architecture

Le projet applique une séparation stricte entre la couche métier et les interfaces utilisateur :

    Projet-attaque-cryptographique-par-MCMC/
    ├── data/                  # Matrices de probabilités classées par langue
    ├── src/                   # Cœur algorithmique (Couche métier)
    │   ├── attaque_mcmc.py       # Algorithme Metropolis-Hastings et calcul des scores
    │   ├── permutation.py        # Logique de mutation et chiffrement par blocs
    │   ├── substitution.py       # Logique de mutation et chiffrement mono-alphabétique
    │   └── wiki_statistiques.py  # Aspirateur Wikipédia et génération des matrices
    ├── interface_complete.py  # Application graphique complète (GUI) avec traceur MCMC
    ├── main.py                # Interface en ligne de commande (CLI) alternative
    ├── requirements.txt       # Liste des dépendances externes
    └── README.md              # Documentation

## Installation et Utilisation

### 1. Prérequis

Python 3.8 ou supérieur est recommandé. Installez les dépendances avec la commande suivante :

    pip install -r requirements.txt

### 2. Lancement

Pour l'interface graphique (GUI - recommandée) :

    python interface_complete.py

Pour l'interface en ligne de commande (CLI) :

    python main.py

### 3. Mise à jour des modèles

Pour régénérer les matrices statistiques ou ajouter de nouvelles langues à la base :

    python src/wiki_statistiques.py
