"""
Module d'Ingestion et de Modélisation Statistique (Mode Massif).
Génère une matrice ultra-précise en ingérant 20 articles majeurs par langue.
"""

import urllib.request
import urllib.parse
import json
import unicodedata
import re
import os
import time
from collections import Counter

def recuperer_texte_wikipedia(titre_page: str, lang: str = 'fr') -> str:
    """Récupère le texte brut d'une page Wikipédia via son API."""
    titre_encode = urllib.parse.quote(titre_page)
    url = f"https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={titre_encode}&format=json"
    
    requete = urllib.request.Request(
        url,
        headers={'User-Agent': 'ProjetMCMC/2.0'}
    )
    
    try:
        with urllib.request.urlopen(requete) as response:
            data = json.loads(response.read().decode('utf-8'))
            pages = data['query']['pages']
            for page_id in pages:
                # L'API utilise l'identifiant -1 pour signaler qu'aucune page
                # correspondant au titre demandé n'a été trouvée.
                if page_id == '-1':
                    print(f"[ERREUR] Page '{titre_page}' introuvable ({lang}).")
                    return ""
                return pages[page_id]['extract']
    except Exception as e:
        print(f"[ERREUR] Connexion à Wikipédia : {e}")
        return ""

def nettoyer_texte(texte: str) -> str:
    """Normalise le texte pour ne conserver que les lettres et les espaces."""
    # La décomposition Unicode sépare les lettres de leurs accents ; les
    # caractères de catégorie « Mn » correspondent ensuite aux accents.
    texte_sans_accents = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
    texte_maj = texte_sans_accents.upper()
    texte_espaces = re.sub(r'[\n\t]', ' ', texte_maj)
    # Les espaces sont conservés car ils participent aux statistiques
    # d'occurrences et aux n-grammes du modèle linguistique.
    texte_filtre = re.sub(r'[^A-Z ]', '', texte_espaces)
    return re.sub(r' +', ' ', texte_filtre).strip()

def obtenir_texte_reference(titre_page: str, lang: str = 'fr') -> str:
    """Retourne le texte nettoyé depuis le cache ou depuis Wikipédia."""
    nom_fichier = titre_page.replace(" ", "_").lower()
    chemin_cache = f"data/{lang}/wiki_{nom_fichier}.txt"
    
    dossier_cache = os.path.dirname(chemin_cache)
    if dossier_cache and not os.path.exists(dossier_cache):
        os.makedirs(dossier_cache)

    if os.path.exists(chemin_cache):
        with open(chemin_cache, 'r', encoding='utf-8') as fichier:
            return fichier.read()
    
    texte_brut = recuperer_texte_wikipedia(titre_page, lang)
    if not texte_brut: return ""
        
    # Le texte nettoyé est mis en cache afin d'éviter de refaire une requête
    # réseau lors des exécutions suivantes.
    texte_propre = nettoyer_texte(texte_brut)
    with open(chemin_cache, 'w', encoding='utf-8') as fichier:
        fichier.write(texte_propre)
    return texte_propre

def calculer_statistiques(texte: str) -> dict:
    """Calcule les occurrences et fréquences des lettres et des espaces."""
    compteur = Counter(texte)
    total_caracteres = len(texte)
    resultats = {'total': total_caracteres, 'occurrences': {}, 'frequences': {}}
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ ":
        nb = compteur.get(char, 0)
        # Une fréquence n'est calculée que si le texte contient au moins un
        # caractère, afin d'éviter une division par zéro.
        resultats['occurrences'][char] = nb
        resultats['frequences'][char] = (nb / total_caracteres * 100) if total_caracteres > 0 else 0
    return resultats

def calculer_statistiques_ngrams(texte: str, n: int) -> dict:
    """Compte les séquences contiguës de ``n`` caractères."""
    # La borne exclut les fenêtres incomplètes à la fin du texte. Chaque
    # position de départ produit ainsi un n-gramme de longueur exactement n.
    ngrams = [texte[i:i+n] for i in range(len(texte)-(n-1))]
    compteur = Counter(ngrams)
    return {ngram: count for ngram, count in compteur.items() if len(ngram) == n}

def sauvegarder_statistiques_json(stats_nouvelles: dict, stats_digrammes: dict, stats_trigrammes: dict, titre_source: str, lang: str = 'fr'):
    """Fusionne les statistiques d'une source dans le modèle JSON de la langue."""
    chemin_fichier = f"data/{lang}/stats_reference.json"
    os.makedirs(os.path.dirname(chemin_fichier), exist_ok=True)
        
    stats_globales = {
        'total': 0, 'occurrences': {char: 0 for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ "},
        'frequences': {}, 'ordre_lettres': [], 'sources_traitees': [],
        'digrammes': {}, 'trigrammes': {}
    }

    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as f:
                stats_anciennes = json.load(f)
                stats_globales.update(stats_anciennes)
        except json.JSONDecodeError:
            # Un fichier vide ou invalide ne doit pas empêcher la régénération
            # du modèle à partir des statistiques courantes.
            pass

    # Cette vérification rend l'opération idempotente : relancer le script ne
    # double pas les données d'une source déjà intégrée.
    if titre_source in stats_globales['sources_traitees']: return 

    stats_globales['total'] += stats_nouvelles['total']
    for char, count in stats_nouvelles['occurrences'].items():
        stats_globales['occurrences'][char] += count
        
    # Les n-grammes sont additionnés séparément afin de conserver la fréquence
    # cumulée d'une même séquence dans plusieurs articles.
    for digramme, count in stats_digrammes.items():
        stats_globales['digrammes'][digramme] = stats_globales['digrammes'].get(digramme, 0) + count
        
    for trigramme, count in stats_trigrammes.items():
        stats_globales['trigrammes'][trigramme] = stats_globales['trigrammes'].get(trigramme, 0) + count

    stats_globales['sources_traitees'].append(titre_source)

    with open(chemin_fichier, 'w', encoding='utf-8') as f:
        json.dump(stats_globales, f, indent=4)
    print(f"[SUCCÈS] Statistiques ajoutées au modèle {lang.upper()} (Source: {titre_source})")

if __name__ == "__main__":
    print("="*60)
    print("   GÉNÉRATION DES MATRICES DE PROBABILITÉS")
    print("="*60)
    
    # L'ensemble des sujets fournit un corpus diversifié pour limiter la
    # dépendance du modèle à un seul domaine lexical.
    pages_a_traiter = [
        # FRANÇAIS (20 nouvelles pages)
        ("fr", "Europe"), ("fr", "Afrique"), ("fr", "Seconde_Guerre_mondiale"), 
        ("fr", "Philosophie"), ("fr", "Psychologie"), ("fr", "Biologie"), ("fr", "Chimie"), 
        ("fr", "Astronomie"), ("fr", "Terre"), ("fr", "Océan"), ("fr", "Économie"), 
        ("fr", "Politique"), ("fr", "Internet"), ("fr", "Intelligence_artificielle"), 
        ("fr", "Électricité"), ("fr", "Lumière"), ("fr", "Temps"), ("fr", "Mathématiques"), 
        ("fr", "Physique_quantique"), ("fr", "Japon"),
        
        # ANGLAIS (20 nouvelles pages)
        ("en", "Europe"), ("en", "Africa"), ("en", "World_War_II"), 
        ("en", "Philosophy"), ("en", "Psychology"), ("en", "Biology"), ("en", "Chemistry"), 
        ("en", "Astronomy"), ("en", "Earth"), ("en", "Ocean"), ("en", "Economics"), 
        ("en", "Politics"), ("en", "Internet"), ("en", "Artificial_intelligence"), 
        ("en", "Electricity"), ("en", "Light"), ("en", "Time"), ("en", "Geometry"), 
        ("en", "Quantum_mechanics"), ("en", "Japan"),
        
        # ESPAGNOL (20 nouvelles pages)
        ("es", "Europa"), ("es", "África"), ("es", "Segunda_Guerra_Mundial"), 
        ("es", "Filosofía"), ("es", "Psicología"), ("es", "Biología"), ("es", "Química"), 
        ("es", "Astronomía"), ("es", "Tierra"), ("es", "Océano"), ("es", "Economía"), 
        ("es", "Política"), ("es", "Internet"), ("es", "Inteligencia_artificial"), 
        ("es", "Electricidad"), ("es", "Luz"), ("es", "Tiempo"), ("es", "Geometría"), 
        ("es", "Mecánica_cuántica"), ("es", "Japón"),
        
        # ITALIEN (Nouvelle langue - 20 pages)
        ("it", "Europa"), ("it", "Africa"), ("it", "Seconda_guerra_mondiale"), 
        ("it", "Filosofia"), ("it", "Psicologia"), ("it", "Biologia"), ("it", "Chimica"), 
        ("it", "Astronomia"), ("it", "Terra"), ("it", "Oceano"), ("it", "Economia"), 
        ("it", "Politica"), ("it", "Internet"), ("it", "Intelligenza_artificiale"), 
        ("it", "Elettricità"), ("it", "Luce"), ("it", "Tempo"), ("it", "Matematica"), 
        ("it", "Meccanica_quantistica"), ("it", "Giappone")
    ]
    
    for langue, sujet in pages_a_traiter:
        texte_ref = obtenir_texte_reference(sujet, lang=langue)
        if texte_ref:
            stats = calculer_statistiques(texte_ref)
            stats_dig = calculer_statistiques_ngrams(texte_ref, 2)
            stats_tri = calculer_statistiques_ngrams(texte_ref, 3) 
            sauvegarder_statistiques_json(stats, stats_dig, stats_tri, sujet, lang=langue)
        time.sleep(5)