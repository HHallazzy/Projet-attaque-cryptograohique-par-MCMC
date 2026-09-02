# Importation de la fonction de cache créée dans le fichier précédent
from wiki_statistiques import obtenir_texte_reference
import random

# Définition globale de notre alphabet de référence
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "

def creer_dictionnaires_conversion():
    """
    Crée les correspondances entre les 27 caractères et les indices 0-26.
    """
    char_to_index = {char: idx for idx, char in enumerate(ALPHABET)}
    index_to_char = {idx: char for idx, char in enumerate(ALPHABET)}
    return char_to_index, index_to_char

def compter_digrammes(texte_reference: str) -> list:
    """
    Tiret 1 : Établir les statistiques des digrammes.
    Retourne une matrice 27x27 (liste de listes).
    """
    char_to_index, _ = creer_dictionnaires_conversion()
    matrice_comptage = [[0 for _ in range(27)] for _ in range(27)]
    
    for i in range(len(texte_reference) - 1):
        char_actuel = texte_reference[i]
        char_suivant = texte_reference[i+1]
        
        if char_actuel in char_to_index and char_suivant in char_to_index:
            idx_actuel = char_to_index[char_actuel]
            idx_suivant = char_to_index[char_suivant]
            matrice_comptage[idx_actuel][idx_suivant] += 1
            
    return matrice_comptage

def construire_matrice_transition(matrice_comptage: list) -> list:
    """
    Tiret 2 : Construire la matrice de transitions de taille 27x27.
    """
    matrice_probabilites = [[0.0 for _ in range(27)] for _ in range(27)]
    
    for i in range(27):
        somme_ligne = sum(matrice_comptage[i])
        for j in range(27):
            if somme_ligne == 0:
                matrice_probabilites[i][j] = 1.0 / 27.0
            else:
                matrice_probabilites[i][j] = matrice_comptage[i][j] / somme_ligne
                
    return matrice_probabilites

def afficher_statistiques_digrammes(matrice_comptage: list):
    """
    Affiche le total et la liste complète des 729 digrammes, 
    triés par ordre d'apparition.
    """
    _, index_to_char = creer_dictionnaires_conversion()
    
    # 1. Calcul du total absolu de digrammes comptés
    total_digrammes = sum(sum(ligne) for ligne in matrice_comptage)
    
    # 2. Création d'une liste plate pour trier facilement les 729 valeurs
    stats = []
    for i in range(27):
        for j in range(27):
            char1 = index_to_char[i]
            char2 = index_to_char[j]
            compte = matrice_comptage[i][j]
            frequence = (compte / total_digrammes * 100) if total_digrammes > 0 else 0
            stats.append((char1, char2, compte, frequence))
            
    # 3. Tri par ordre décroissant (du plus fréquent au moins fréquent)
    stats.sort(key=lambda x: x[2], reverse=True)
    
    # 4. Affichage
    print(f"\nTotal des digrammes : {total_digrammes}")
    print("Statistiques des 729 digrammes :")
    for char1, char2, compte, freq in stats:
        # Pour que l'affichage soit lisible dans la console, on remplace visuellement l'espace par un tiret bas '_'
        affichage_c1 = "_" if char1 == " " else char1
        affichage_c2 = "_" if char2 == " " else char2
        
        print(f"'{affichage_c1}{affichage_c2}' : {compte} fois ({freq:.4f}%)")

def generer_texte_markov(matrice_probabilites: list, longueur: int = 100) -> str:
    """
    Génère du texte aléatoire en naviguant dans la matrice de transition.
    Initialisé par "espace" selon la consigne.
    """
    char_to_index, index_to_char = creer_dictionnaires_conversion()
    
    # Initialisation
    char_actuel = " "
    texte_genere = [char_actuel]
    
    for _ in range(longueur - 1):
        idx_actuel = char_to_index[char_actuel]
        probabilites = matrice_probabilites[idx_actuel]
        
        # Tirage pondéré du prochain index
        idx_suivant = random.choices(range(27), weights=probabilites, k=1)[0]
        char_suivant = index_to_char[idx_suivant]
        
        texte_genere.append(char_suivant)
        char_actuel = char_suivant
        
    return "".join(texte_genere)

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    # Assure-toi que le sujet correspond bien à un fichier existant dans ton dossier data/ 
    # ou qu'il sera téléchargé par l'import.
    sujet_wiki = "Chiffre_de_Vigenère"
    
    texte_ref = obtenir_texte_reference(sujet_wiki)
    
    if texte_ref:
        print(f"\nCalcul sur un texte de {len(texte_ref)} caractères...")
        
        # Tiret 1 : Comptage et affichage complet
        comptage = compter_digrammes(texte_ref)
        afficher_statistiques_digrammes(comptage)
        
        # Tiret 2 : Création de la matrice de probabilités pour la suite
        probabilites = construire_matrice_transition(comptage)

        # Tiret 3 : Génération de texte aléatoire
        print("\n--- Génération de texte par chaîne de Markov ---")
        texte_aleatoire = generer_texte_markov(probabilites, longueur=150)
        print(f"\nRésultat (150 caractères) :\n{texte_aleatoire}")