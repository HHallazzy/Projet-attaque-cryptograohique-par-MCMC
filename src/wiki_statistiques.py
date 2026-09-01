import urllib.request
import urllib.parse
import json
import unicodedata
import re
from collections import Counter

def recuperer_texte_wikipedia(titre_page: str) -> str:
    """
    Récupère le texte brut d'une page Wikipedia en français via l'API REST.
    """
    # Formatage du titre pour l'URL
    titre_encode = urllib.parse.quote(titre_page)
    url = f"https://fr.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={titre_encode}&format=json"
    
    # Création d'une requête avec un User-Agent pour éviter l'erreur 403 de Wikipédia
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
            
            # L'API renvoie les données sous un ID de page dynamique
            for page_id in pages:
                if page_id == '-1':
                    print(f"Erreur : La page '{titre_page}' n'a pas été trouvée sur Wikipédia.")
                    return ""
                return pages[page_id]['extract']
    except Exception as e:
        print(f"Erreur de connexion à Wikipédia : {e}")
        return ""

def nettoyer_texte(texte: str) -> str:
    """
    Nettoie le texte pour ne garder que l'alphabet [A-Z] et l'espace (27 caractères).
    """
    # 1. Supprimer les accents (ex: é -> e, à -> a)
    texte_sans_accents = ''.join(c for c in unicodedata.normalize('NFD', texte) 
                                 if unicodedata.category(c) != 'Mn')
    
    # 2. Convertir tout en majuscules
    texte_maj = texte_sans_accents.upper()
    
    # 3. Remplacer les retours à la ligne et tabulations par un espace
    texte_espaces = re.sub(r'[\n\t]', ' ', texte_maj)
    
    # 4. Supprimer TOUT ce qui n'est pas A-Z ou espace (ponctuation, chiffres, etc.)
    texte_filtre = re.sub(r'[^A-Z ]', '', texte_espaces)
    
    # 5. Réduire les espaces multiples consécutifs en un seul espace
    texte_final = re.sub(r' +', ' ', texte_filtre)
    
    return texte_final.strip()

def calculer_statistiques(texte: str) -> dict:
    """
    Calcule les occurrences et les fréquences des 27 caractères.
    """
    compteur = Counter(texte)
    total_caracteres = len(texte)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "
    
    resultats = {
        'total': total_caracteres,
        'occurrences': {},
        'frequences': {}
    }
    
    # On garantit que les 27 caractères sont présents dans les stats, même si nb = 0
    for char in alphabet:
        nb = compteur.get(char, 0)
        resultats['occurrences'][char] = nb
        resultats['frequences'][char] = (nb / total_caracteres * 100) if total_caracteres > 0 else 0
        
    return resultats

# ==========================================
# TEST DU SCRIPT
# ==========================================
if __name__ == "__main__":
    # Test avec une page qui contient pas mal de texte
    sujet_wiki = "Chiffre_de_Vigenère"
    print(f"--- 1. Récupération de la page '{sujet_wiki}' ---")
    texte_brut = recuperer_texte_wikipedia(sujet_wiki)
    
    if texte_brut:
        print(f"Texte récupéré ({len(texte_brut)} caractères bruts).")
        
        print("\n--- 2. Nettoyage du texte ---")
        texte_propre = nettoyer_texte(texte_brut)
        print(f"Texte nettoyé ({len(texte_propre)} caractères valides).")
        print(f"Aperçu : {texte_propre[:100]}...")
        
        print("\n--- 3. Statistiques simples ---")
        stats = calculer_statistiques(texte_propre)
        print(f"Caractères totaux : {stats['total']}")
        
        # Affichage du Top 5 pour vérifier que l'espace et le E dominent (typique du français)
        occurrences_triees = sorted(stats['occurrences'].items(), key=lambda x: x[1], reverse=True)
        print("\nTop 5 des caractères les plus fréquents :")
        for char, count in occurrences_triees[:5]:
            affichage_char = "[ESPACE]" if char == " " else char
            print(f"'{affichage_char}' : {count} fois ({stats['frequences'][char]:.2f}%)")