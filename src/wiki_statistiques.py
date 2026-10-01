import urllib.request
import urllib.parse
import json
import unicodedata
import re
import os
from collections import Counter

def recuperer_texte_wikipedia(titre_page: str, lang: str = 'fr') -> str:
    """
    Récupère le texte brut d'une page Wikipedia dans la langue spécifiée.
    """
    titre_encode = urllib.parse.quote(titre_page)
    # L'URL intègre désormais la variable 'lang' (fr, en, es, de...)
    url = f"https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={titre_encode}&format=json"
    
    requete = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'ProjetMCMC/1.0 (https://github.com/HHallazzy/Projet-attaque-cryptograohique-par-MCMC)'
        }
    )
    
    try:
        with urllib.request.urlopen(requete) as response:
            data = json.loads(response.read().decode('utf-8'))
            pages = data['query']['pages']
            
            for page_id in pages:
                if page_id == '-1':
                    print(f"Erreur : La page '{titre_page}' n'a pas ete trouvee sur Wikipedia ({lang}).")
                    return ""
                return pages[page_id]['extract']
    except Exception as e:
        print(f"Erreur de connexion a Wikipedia : {e}")
        return ""

def nettoyer_texte(texte: str) -> str:
    """
    Nettoie le texte pour ne garder que l'alphabet [A-Z] et l'espace.
    Gère automatiquement les caractères internationaux (é->E, ñ->N, etc.)
    """
    texte_sans_accents = ''.join(c for c in unicodedata.normalize('NFD', texte) 
                                 if unicodedata.category(c) != 'Mn')
    texte_maj = texte_sans_accents.upper()
    texte_espaces = re.sub(r'[\n\t]', ' ', texte_maj)
    texte_filtre = re.sub(r'[^A-Z ]', '', texte_espaces)
    texte_final = re.sub(r' +', ' ', texte_filtre)
    
    return texte_final.strip()

def obtenir_texte_reference(titre_page: str, lang: str = 'fr') -> str:
    """
    Vérifie si le texte existe en cache. Le cache est organisé par langue.
    """
    nom_fichier = titre_page.replace(" ", "_").lower()
    # Le chemin intègre maintenant le dossier de la langue
    chemin_cache = f"data/{lang}/wiki_{nom_fichier}.txt"
    
    dossier_cache = os.path.dirname(chemin_cache)
    if dossier_cache and not os.path.exists(dossier_cache):
        os.makedirs(dossier_cache)

    if os.path.exists(chemin_cache):
        print(f"Chargement du texte depuis le cache : {chemin_cache}")
        with open(chemin_cache, 'r', encoding='utf-8') as fichier:
            return fichier.read()
    
    print(f"Téléchargement de la page '{titre_page}' (Langue : {lang.upper()})...")
    texte_brut = recuperer_texte_wikipedia(titre_page, lang)
    
    if not texte_brut:
        return ""
        
    print("Nettoyage du texte...")
    texte_propre = nettoyer_texte(texte_brut)
    
    with open(chemin_cache, 'w', encoding='utf-8') as fichier:
        fichier.write(texte_propre)
    print(f"Texte sauvegardé dans le cache : {chemin_cache}")
        
    return texte_propre

def calculer_statistiques(texte: str) -> dict:
    compteur = Counter(texte)
    total_caracteres = len(texte)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "
    
    resultats = {
        'total': total_caracteres,
        'occurrences': {},
        'frequences': {}
    }
    
    for char in alphabet:
        nb = compteur.get(char, 0)
        resultats['occurrences'][char] = nb
        resultats['frequences'][char] = (nb / total_caracteres * 100) if total_caracteres > 0 else 0
        
    lettres_triees = sorted([c for c in alphabet if c != ' '], 
                            key=lambda x: resultats['frequences'][x], 
                            reverse=True)
    resultats['ordre_lettres'] = lettres_triees
        
    return resultats

def calculer_statistiques_digrammes(texte: str) -> dict:
    digrammes = [texte[i:i+2] for i in range(len(texte)-1)]
    compteur = Counter(digrammes)
    
    resultats = {}
    for digramme, count in compteur.items():
        if len(digramme) == 2: 
            resultats[digramme] = count
            
    return resultats

def sauvegarder_statistiques_json(stats_nouvelles: dict, stats_digrammes: dict, titre_source: str, lang: str = 'fr'):
    """
    Sauvegarde le JSON dans le dossier propre à sa langue.
    """
    chemin_fichier = f"data/{lang}/stats_reference.json"
    
    dossier_cache = os.path.dirname(chemin_fichier)
    if dossier_cache and not os.path.exists(dossier_cache):
        os.makedirs(dossier_cache)
        
    stats_globales = {
        'total': 0,
        'occurrences': {char: 0 for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ "},
        'frequences': {},
        'ordre_lettres': [],
        'sources_traitees': [],
        'digrammes': {}
    }

    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
                stats_anciennes = json.load(fichier)
                stats_globales['total'] = stats_anciennes.get('total', 0)
                stats_globales['occurrences'] = stats_anciennes.get('occurrences', stats_globales['occurrences'])
                stats_globales['sources_traitees'] = stats_anciennes.get('sources_traitees', [])
                stats_globales['digrammes'] = stats_anciennes.get('digrammes', {})
        except json.JSONDecodeError:
            pass

    if titre_source in stats_globales['sources_traitees']:
        print(f"\n[INFO] La page '{titre_source}' est déjà dans la base '{lang.upper()}'.")
        return 

    stats_globales['total'] += stats_nouvelles['total']
    for char, count in stats_nouvelles['occurrences'].items():
        stats_globales['occurrences'][char] += count
        
    for digramme, count in stats_digrammes.items():
        stats_globales['digrammes'][digramme] = stats_globales['digrammes'].get(digramme, 0) + count

    stats_globales['sources_traitees'].append(titre_source)

    for char, count in stats_globales['occurrences'].items():
        stats_globales['frequences'][char] = (count / stats_globales['total'] * 100) if stats_globales['total'] > 0 else 0

    alphabet_sans_espace = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lettres_triees = sorted(list(alphabet_sans_espace), 
                            key=lambda x: stats_globales['frequences'][x], 
                            reverse=True)
    stats_globales['ordre_lettres'] = lettres_triees

    with open(chemin_fichier, 'w', encoding='utf-8') as fichier:
        json.dump(stats_globales, fichier, indent=4)
        
    print(f"[SUCCÈS] Statistiques '{lang.upper()}' de '{titre_source}' accumulées !")

# ==========================================
# EXECUTION (Test Multilingue)
# ==========================================
if __name__ == "__main__":
    # Liste de tuples (langue, page_wikipedia) pour tester la nouvelle architecture
    pages_a_traiter = [
        ("fr", "Chiffre_de_Vigenère"),
        ("fr", "Cryptographie"),
        ("en", "Cryptography"),
        ("en", "Computer_science"),
        ("es", "Criptografía")
    ]
    
    for langue, sujet in pages_a_traiter:
        print(f"\n{'='*50}")
        print(f" TRAITEMENT : {sujet} ({langue.upper()})")
        print(f"{'='*50}")
        
        texte_ref = obtenir_texte_reference(sujet, lang=langue)
        
        if texte_ref:
            stats = calculer_statistiques(texte_ref)
            stats_dig = calculer_statistiques_digrammes(texte_ref)
            sauvegarder_statistiques_json(stats, stats_dig, sujet, lang=langue)