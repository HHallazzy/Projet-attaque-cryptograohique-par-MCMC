import urllib.request
import urllib.parse
import json
import unicodedata
import re
import os
from collections import Counter

def recuperer_texte_wikipedia(titre_page: str, lang: str = 'fr') -> str:
    titre_encode = urllib.parse.quote(titre_page)
    url = f"https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={titre_encode}&format=json"
    
    requete = urllib.request.Request(
        url,
        headers={'User-Agent': 'ProjetMCMC/1.0'}
    )
    
    try:
        with urllib.request.urlopen(requete) as response:
            data = json.loads(response.read().decode('utf-8'))
            pages = data['query']['pages']
            for page_id in pages:
                if page_id == '-1':
                    print(f"Erreur : La page '{titre_page}' introuvable ({lang}).")
                    return ""
                return pages[page_id]['extract']
    except Exception as e:
        print(f"Erreur de connexion a Wikipedia : {e}")
        return ""

def nettoyer_texte(texte: str) -> str:
    texte_sans_accents = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
    texte_maj = texte_sans_accents.upper()
    texte_espaces = re.sub(r'[\n\t]', ' ', texte_maj)
    texte_filtre = re.sub(r'[^A-Z ]', '', texte_espaces)
    return re.sub(r' +', ' ', texte_filtre).strip()

def obtenir_texte_reference(titre_page: str, lang: str = 'fr') -> str:
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
        
    texte_propre = nettoyer_texte(texte_brut)
    with open(chemin_cache, 'w', encoding='utf-8') as fichier:
        fichier.write(texte_propre)
    return texte_propre

def calculer_statistiques(texte: str) -> dict:
    compteur = Counter(texte)
    total_caracteres = len(texte)
    resultats = {'total': total_caracteres, 'occurrences': {}, 'frequences': {}}
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ ":
        nb = compteur.get(char, 0)
        resultats['occurrences'][char] = nb
        resultats['frequences'][char] = (nb / total_caracteres * 100) if total_caracteres > 0 else 0
    return resultats

def calculer_statistiques_ngrams(texte: str, n: int) -> dict:
    """Calcule les N-grammes (2 pour digrammes, 3 pour trigrammes)."""
    ngrams = [texte[i:i+n] for i in range(len(texte)-(n-1))]
    compteur = Counter(ngrams)
    return {ngram: count for ngram, count in compteur.items() if len(ngram) == n}

def sauvegarder_statistiques_json(stats_nouvelles: dict, stats_digrammes: dict, stats_trigrammes: dict, titre_source: str, lang: str = 'fr'):
    chemin_fichier = f"data/{lang}/stats_reference.json"
    os.makedirs(os.path.dirname(chemin_fichier), exist_ok=True)
        
    stats_globales = {
        'total': 0, 'occurrences': {char: 0 for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ "},
        'frequences': {}, 'ordre_lettres': [], 'sources_traitees': [],
        'digrammes': {}, 'trigrammes': {} # <-- Ajout du dictionnaire Trigrammes
    }

    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as f:
                stats_anciennes = json.load(f)
                stats_globales.update(stats_anciennes)
        except json.JSONDecodeError: pass

    if titre_source in stats_globales['sources_traitees']: return 

    stats_globales['total'] += stats_nouvelles['total']
    for char, count in stats_nouvelles['occurrences'].items():
        stats_globales['occurrences'][char] += count
        
    for digramme, count in stats_digrammes.items():
        stats_globales['digrammes'][digramme] = stats_globales['digrammes'].get(digramme, 0) + count
        
    for trigramme, count in stats_trigrammes.items():
        stats_globales['trigrammes'][trigramme] = stats_globales['trigrammes'].get(trigramme, 0) + count

    stats_globales['sources_traitees'].append(titre_source)

    with open(chemin_fichier, 'w', encoding='utf-8') as f:
        json.dump(stats_globales, f, indent=4)
    print(f"[SUCCÈS] Statistiques '{lang.upper()}' (Digrammes & Trigrammes) enregistrées !")

if __name__ == "__main__":
    pages_a_traiter = [
        ("fr", "Chiffre_de_Vigenère"), ("fr", "Cryptographie"), ("fr", "Souris"),
        ("en", "Cryptography"), ("en", "Computer_science"), ("es", "Criptografía")
    ]
    for langue, sujet in pages_a_traiter:
        texte_ref = obtenir_texte_reference(sujet, lang=langue)
        if texte_ref:
            stats = calculer_statistiques(texte_ref)
            stats_dig = calculer_statistiques_ngrams(texte_ref, 2)
            stats_tri = calculer_statistiques_ngrams(texte_ref, 3) # <-- Calcul trigrammes
            sauvegarder_statistiques_json(stats, stats_dig, stats_tri, sujet, lang=langue)