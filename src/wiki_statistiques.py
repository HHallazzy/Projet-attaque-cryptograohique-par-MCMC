"""
Module d'Ingestion et de Modélisation Statistique.
Ce script génère les matrices de probabilités de référence utilisées par l'algorithme MCMC.
Il aspire des textes (via l'API Wikipédia), les normalise pour l'espace cryptographique (27 caractères),
et calcule les occurrences des N-grammes (Digrammes et Trigrammes) par langue.
"""

import urllib.request
import urllib.parse
import json
import unicodedata
import re
import os
from collections import Counter

def recuperer_texte_wikipedia(titre_page: str, lang: str = 'fr') -> str:
    """
    Interroge l'API officielle de Wikipédia pour extraire le texte brut d'un article.
    Utilise un User-Agent personnalisé pour respecter les conditions d'utilisation de l'API.
    """
    titre_encode = urllib.parse.quote(titre_page)
    # L'API est configurée pour retourner uniquement le texte pur (explaintext=1), sans HTML ni balises wiki
    url = f"https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={titre_encode}&format=json"
    
    requete = urllib.request.Request(
        url,
        headers={'User-Agent': 'ProjetMCMC/1.0'}
    )
    
    try:
        with urllib.request.urlopen(requete) as response:
            data = json.loads(response.read().decode('utf-8'))
            pages = data['query']['pages']
            
            # Parcours du JSON pour extraire le contenu de la page retournée
            for page_id in pages:
                if page_id == '-1':
                    print(f"[ERREUR] La page '{titre_page}' est introuvable ({lang}).")
                    return ""
                return pages[page_id]['extract']
    except Exception as e:
        print(f"[ERREUR] Échec de la connexion à Wikipédia : {e}")
        return ""

def nettoyer_texte(texte: str) -> str:
    """
    Normalise le texte pour le restreindre à l'alphabet cryptographique ciblé (A-Z + Espace).
    Retire les accents, la ponctuation, les chiffres et les sauts de ligne.
    """
    # Décomposition Unicode (NFD) pour séparer les caractères de leurs accents (ex: 'é' devient 'e' + '´')
    texte_sans_accents = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
    texte_maj = texte_sans_accents.upper()
    
    # Remplacement des sauts de ligne et tabulations par des espaces simples
    texte_espaces = re.sub(r'[\n\t]', ' ', texte_maj)
    
    # Suppression stricte de tout caractère n'appartenant pas à [A-Z] ou à l'espace
    texte_filtre = re.sub(r'[^A-Z ]', '', texte_espaces)
    
    # Réduction des espaces multiples consécutifs en un seul espace pour ne pas fausser les probabilités
    return re.sub(r' +', ' ', texte_filtre).strip()

def obtenir_texte_reference(titre_page: str, lang: str = 'fr') -> str:
    """
    Gestionnaire de cache local. Vérifie si le texte de la page a déjà été téléchargé
    et nettoyé auparavant pour éviter des requêtes réseau redondantes (Gain de temps O(1)).
    """
    nom_fichier = titre_page.replace(" ", "_").lower()
    chemin_cache = f"data/{lang}/wiki_{nom_fichier}.txt"
    
    # Création de l'arborescence si la langue n'a jamais été traitée
    dossier_cache = os.path.dirname(chemin_cache)
    if dossier_cache and not os.path.exists(dossier_cache):
        os.makedirs(dossier_cache)

    # Retour depuis le cache local (Lecture rapide)
    if os.path.exists(chemin_cache):
        with open(chemin_cache, 'r', encoding='utf-8') as fichier:
            return fichier.read()
    
    # Si non présent en cache, téléchargement, nettoyage et sauvegarde (Mise en cache)
    texte_brut = recuperer_texte_wikipedia(titre_page, lang)
    if not texte_brut: return ""
        
    texte_propre = nettoyer_texte(texte_brut)
    with open(chemin_cache, 'w', encoding='utf-8') as fichier:
        fichier.write(texte_propre)
        
    return texte_propre

def calculer_statistiques(texte: str) -> dict:
    """
    Calcule les probabilités unigrammes (fréquence d'apparition de chaque lettre).
    Base statistique fondamentale sur l'alphabet de 27 caractères.
    """
    compteur = Counter(texte)
    total_caracteres = len(texte)
    resultats = {'total': total_caracteres, 'occurrences': {}, 'frequences': {}}
    
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ ":
        nb = compteur.get(char, 0)
        resultats['occurrences'][char] = nb
        resultats['frequences'][char] = (nb / total_caracteres * 100) if total_caracteres > 0 else 0
        
    return resultats

def calculer_statistiques_ngrams(texte: str, n: int) -> dict:
    """
    Extrait les fréquences absolues des N-grammes via une approche par fenêtre glissante.
    Utilisé pour générer les matrices de Digrammes (n=2) et Trigrammes (n=3).
    """
    # Création d'une liste de tous les blocs de 'n' caractères consécutifs
    ngrams = [texte[i:i+n] for i in range(len(texte)-(n-1))]
    compteur = Counter(ngrams)
    
    # Filtre de sécurité pour garantir la taille exacte des clés retournées
    return {ngram: count for ngram, count in compteur.items() if len(ngram) == n}

def sauvegarder_statistiques_json(stats_nouvelles: dict, stats_digrammes: dict, stats_trigrammes: dict, titre_source: str, lang: str = 'fr'):
    """
    Agrége (fusionne) les nouvelles statistiques avec le modèle global existant pour une langue donnée.
    Implémente une protection anti-doublon pour éviter le biais statistique d'un texte analysé deux fois.
    """
    chemin_fichier = f"data/{lang}/stats_reference.json"
    os.makedirs(os.path.dirname(chemin_fichier), exist_ok=True)
        
    # Structure de base (Modèle vierge)
    stats_globales = {
        'total': 0, 'occurrences': {char: 0 for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ "},
        'frequences': {}, 'ordre_lettres': [], 'sources_traitees': [],
        'digrammes': {}, 'trigrammes': {}
    }

    # Chargement de la matrice existante pour mise à jour cumulative
    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as f:
                stats_anciennes = json.load(f)
                stats_globales.update(stats_anciennes)
        except json.JSONDecodeError: pass

    # Protection contre le biais : On ignore la source si elle est déjà dans le modèle
    if titre_source in stats_globales['sources_traitees']: return 

    # Addition des unigrammes
    stats_globales['total'] += stats_nouvelles['total']
    for char, count in stats_nouvelles['occurrences'].items():
        stats_globales['occurrences'][char] += count
        
    # Addition vectorielle des digrammes
    for digramme, count in stats_digrammes.items():
        stats_globales['digrammes'][digramme] = stats_globales['digrammes'].get(digramme, 0) + count
        
    # Addition vectorielle des trigrammes
    for trigramme, count in stats_trigrammes.items():
        stats_globales['trigrammes'][trigramme] = stats_globales['trigrammes'].get(trigramme, 0) + count

    # Enregistrement de la trace de traitement
    stats_globales['sources_traitees'].append(titre_source)

    # Persistance sur le disque dur
    with open(chemin_fichier, 'w', encoding='utf-8') as f:
        json.dump(stats_globales, f, indent=4)
        
    print(f"[SUCCÈS] Statistiques '{lang.upper()}' (Digrammes & Trigrammes) enregistrées (Source: {titre_source}) !")

if __name__ == "__main__":
    # Liste initiale d'articles Wikipédia pour entraîner les modèles de base
    pages_a_traiter = [
        ("fr", "Chiffre_de_Vigenère"), ("fr", "Cryptographie"), ("fr", "Souris"),
        ("en", "Cryptography"), ("en", "Computer_science"), ("es", "Criptografía")
    ]
    
    print("="*60)
    print("   CRÉATION / MISE À JOUR DES MATRICES DE PROBABILITÉS")
    print("="*60)
    
    for langue, sujet in pages_a_traiter:
        texte_ref = obtenir_texte_reference(sujet, lang=langue)
        if texte_ref:
            # Extraction des variables aléatoires (1D, 2D, 3D)
            stats = calculer_statistiques(texte_ref)
            stats_dig = calculer_statistiques_ngrams(texte_ref, 2)
            stats_tri = calculer_statistiques_ngrams(texte_ref, 3) 
            
            # Injection dans le modèle de la langue correspondante
            sauvegarder_statistiques_json(stats, stats_dig, stats_tri, sujet, lang=langue)