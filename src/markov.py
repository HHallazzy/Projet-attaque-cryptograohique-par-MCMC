import numpy as np

# Définition globale de notre alphabet de référence
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "

def creer_dictionnaires_conversion():
    """Crée les correspondances entre les 27 caractères et les indices 0-26."""
    char_to_index = {char: idx for idx, char in enumerate(ALPHABET)}
    index_to_char = {idx: char for idx, char in enumerate(ALPHABET)}
    return char_to_index, index_to_char

def construire_matrice_transition(texte_reference: str) -> np.ndarray:
    """
    Construit une matrice 27x27 où la cellule [i, j] représente 
    la probabilité de passer du caractère i au caractère j.
    """
    char_to_index, _ = creer_dictionnaires_conversion()
    
    # Initialisation d'une matrice 27x27 remplie de zéros
    matrice_comptage = np.zeros((27, 27))
    
    # 1. Parcours du texte et comptage des digrammes consécutifs
    for i in range(len(texte_reference) - 1):
        char_actuel = texte_reference[i]
        char_suivant = texte_reference[i+1]
        
        # Sécurité : on ignore les caractères hors de notre alphabet strict
        if char_actuel in char_to_index and char_suivant in char_to_index:
            idx_actuel = char_to_index[char_actuel]
            idx_suivant = char_to_index[char_suivant]
            matrice_comptage[idx_actuel, idx_suivant] += 1
            
    # 2. Normalisation des probabilités (la somme de chaque ligne doit être 1)
    sommes_lignes = matrice_comptage.sum(axis=1, keepdims=True)
    
    # Gestion des lignes vides (si une lettre n'a jamais été suivie d'une autre dans un texte court)
    # Pour éviter la division par zéro, on remplace artificiellement par une distribution équiprobable
    lignes_vides = (sommes_lignes == 0).flatten()
    matrice_comptage[lignes_vides] = 1.0 / 27.0
    sommes_lignes[lignes_vides] = 1.0
    
    # La magie de NumPy : on divise toute la matrice par la colonne des sommes en une seule opération
    matrice_probabilites = matrice_comptage / sommes_lignes
    
    return matrice_probabilites