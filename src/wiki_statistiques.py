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
    # Création d'un nom de fichier adapté au titre (remplace les espaces par des tirets bas)
    nom_fichier = titre_page.replace(" ", "_").lower()
    chemin_cache = f"data/wiki_{nom_fichier}.txt"
    
    # Si le dossier data n'existe pas, on le crée
    dossier_cache = os.path.dirname(chemin_cache)
    if dossier_cache and not os.path.exists(dossier_cache):
        os.makedirs(dossier_cache)

    # Vérification de la présence du cache pour ce fichier précis
    if os.path.exists(chemin_cache):
        print(f"Chargement du texte depuis le cache : {chemin_cache}")
        with open(chemin_cache, 'r', encoding='utf-8') as fichier:
            return fichier.read()
    
    # Si pas de cache, on effectue la procédure complète
    print(f"Téléchargement de la page '{titre_page}'...")
    texte_brut = recuperer_texte_wikipedia(titre_page)
    
    if not texte_brut:
        return ""
        
    print("Nettoyage du texte...")
    texte_propre = nettoyer_texte(texte_brut)
    
    # Sauvegarde dans le cache
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
        
    return resultats

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    sujet_wiki = "Acide_désoxyribonucléique"
    
    # Utilisation de la nouvelle fonction avec mise en cache
    texte_ref = obtenir_texte_reference(sujet_wiki)
    
    if texte_ref:
        print(f"\nLongueur du texte de reference : {len(texte_ref)} caracteres.")
        
        stats = calculer_statistiques(texte_ref)
        occurrences_triees = sorted(stats['occurrences'].items(), key=lambda x: x[1], reverse=True)
        
        # Affichage des 27 caractères comme demandé dans le sujet
        print("\nStatistiques des 27 caracteres :")
        for char, count in occurrences_triees:
            affichage_char = "[ESPACE]" if char == " " else char
            print(f"'{affichage_char}' : {count} fois ({stats['frequences'][char]:.2f}%)")