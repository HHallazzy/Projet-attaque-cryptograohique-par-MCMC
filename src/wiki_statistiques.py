import urllib.request
import urllib.parse
import json
import unicodedata
import re
import os
from collections import Counter

def recuperer_texte_wikipedia(titre_page: str) -> str:
    """
    Récupère le texte brut d'une page Wikipedia en français via l'API REST.
    """
    titre_encode = urllib.parse.quote(titre_page)
    url = f"https://fr.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={titre_encode}&format=json"
    
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
                    print(f"Erreur : La page '{titre_page}' n'a pas ete trouvee sur Wikipedia.")
                    return ""
                return pages[page_id]['extract']
    except Exception as e:
        print(f"Erreur de connexion a Wikipedia : {e}")
        return ""

def nettoyer_texte(texte: str) -> str:
    """
    Nettoie le texte pour ne garder que l'alphabet [A-Z] et l'espace (27 caracteres).
    """
    texte_sans_accents = ''.join(c for c in unicodedata.normalize('NFD', texte) 
                                 if unicodedata.category(c) != 'Mn')
    texte_maj = texte_sans_accents.upper()
    texte_espaces = re.sub(r'[\n\t]', ' ', texte_maj)
    texte_filtre = re.sub(r'[^A-Z ]', '', texte_espaces)
    texte_final = re.sub(r' +', ' ', texte_filtre)
    
    return texte_final.strip()

def obtenir_texte_reference(titre_page: str) -> str:
    """
    Vérifie si le texte de référence existe en cache pour CE sujet précis.
    Si oui, le charge. Sinon, le télécharge, le nettoie et le sauvegarde.
    """
    nom_fichier = titre_page.replace(" ", "_").lower()
    chemin_cache = f"data/wiki_{nom_fichier}.txt"
    
    dossier_cache = os.path.dirname(chemin_cache)
    if dossier_cache and not os.path.exists(dossier_cache):
        os.makedirs(dossier_cache)

    if os.path.exists(chemin_cache):
        print(f"Chargement du texte depuis le cache : {chemin_cache}")
        with open(chemin_cache, 'r', encoding='utf-8') as fichier:
            return fichier.read()
    
    print(f"Téléchargement de la page '{titre_page}'...")
    texte_brut = recuperer_texte_wikipedia(titre_page)
    
    if not texte_brut:
        return ""
        
    print("Nettoyage du texte...")
    texte_propre = nettoyer_texte(texte_brut)
    
    with open(chemin_cache, 'w', encoding='utf-8') as fichier:
        fichier.write(texte_propre)
    print(f"Texte sauvegardé dans le cache : {chemin_cache}")
        
    return texte_propre

def calculer_statistiques(texte: str) -> dict:
    """
    Calcule les occurrences et les frequences des 27 caracteres.
    """
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
        
    # Création d'une liste des lettres (sans l'espace) triées par fréquence décroissante
    lettres_triees = sorted([c for c in alphabet if c != ' '], 
                            key=lambda x: resultats['frequences'][x], 
                            reverse=True)
    resultats['ordre_lettres'] = lettres_triees
        
    return resultats

def sauvegarder_statistiques_json(stats_nouvelles: dict, titre_source: str, chemin_fichier="data/stats_reference.json"):
    """
    Sauvegarde et accumule le dictionnaire de statistiques au format JSON.
    Empêche les doublons en mémorisant les sources déjà traitées.
    """
    dossier_cache = os.path.dirname(chemin_fichier)
    if dossier_cache and not os.path.exists(dossier_cache):
        os.makedirs(dossier_cache)
        
    # Structure de base avec la nouvelle clé 'sources_traitees'
    stats_globales = {
        'total': 0,
        'occurrences': {char: 0 for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ "},
        'frequences': {},
        'ordre_lettres': [],
        'sources_traitees': [] 
    }

    # 1. Lire les anciennes statistiques
    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
                stats_anciennes = json.load(fichier)
                stats_globales['total'] = stats_anciennes.get('total', 0)
                stats_globales['occurrences'] = stats_anciennes.get('occurrences', stats_globales['occurrences'])
                stats_globales['sources_traitees'] = stats_anciennes.get('sources_traitees', [])
        except json.JSONDecodeError:
            pass

    # 2. VÉRIFICATION ANTI-DOUBLON
    if titre_source in stats_globales['sources_traitees']:
        print(f"\n[INFO] La page '{titre_source}' est déjà dans la base de données.")
        print("-> Accumulation annulée pour éviter de fausser les statistiques.")
        return # On arrête la fonction ici

    # 3. Additionner les nouvelles occurrences
    stats_globales['total'] += stats_nouvelles['total']
    for char, count in stats_nouvelles['occurrences'].items():
        stats_globales['occurrences'][char] += count
        
    # 4. Mémoriser la nouvelle source
    stats_globales['sources_traitees'].append(titre_source)

    # 5. Recalculer les fréquences globales
    for char, count in stats_globales['occurrences'].items():
        stats_globales['frequences'][char] = (count / stats_globales['total'] * 100) if stats_globales['total'] > 0 else 0

    # 6. Recalculer l'ordre des lettres (sans l'espace)
    alphabet_sans_espace = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lettres_triees = sorted(list(alphabet_sans_espace), 
                            key=lambda x: stats_globales['frequences'][x], 
                            reverse=True)
    stats_globales['ordre_lettres'] = lettres_triees

    # 7. Sauvegarder
    with open(chemin_fichier, 'w', encoding='utf-8') as fichier:
        json.dump(stats_globales, fichier, indent=4)
        
    print(f"\n[SUCCÈS] Statistiques de '{titre_source}' accumulées !")
    print(f"Total des caractères dans la base de données : {stats_globales['total']}")

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    sujet_wiki = "chiffrement_par_décalage"
    
    texte_ref = obtenir_texte_reference(sujet_wiki)
    
    if texte_ref:
        print(f"\nLongueur du texte de reference : {len(texte_ref)} caracteres.")
        
        stats = calculer_statistiques(texte_ref)
        occurrences_triees = sorted(stats['occurrences'].items(), key=lambda x: x[1], reverse=True)
        
        print("\nStatistiques des 27 caracteres :")
        for char, count in occurrences_triees:
            affichage_char = "[ESPACE]" if char == " " else char
            print(f"'{affichage_char}' : {count} fois ({stats['frequences'][char]:.2f}%)")
            
        # Appel de la fonction de sauvegarde de statistiques
        sauvegarder_statistiques_json(stats, sujet_wiki)