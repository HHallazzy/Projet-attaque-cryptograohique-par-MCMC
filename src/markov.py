from wiki_statistiques import obtenir_texte_reference
import random

# Définition globale de notre alphabet de référence (26 lettres + 1 espace = 27 états possibles)
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "

def creer_dictionnaires_conversion():
    """
    Crée les correspondances entre les 27 caractères et les indices 0-26.
    """
    # LIGNE COMPLEXE (Compréhension de liste avec énumération) :
    # Les tableaux/matrices en Python n'acceptent que des nombres comme coordonnées (ex: matrice[0][1]).
    # enumerate() associe automatiquement un chiffre à chaque lettre (0:'A', 1:'B', ... 26:' ').
    char_to_index = {char: idx for idx, char in enumerate(ALPHABET)}
    index_to_char = {idx: char for idx, char in enumerate(ALPHABET)}
    
    return char_to_index, index_to_char

def compter_digrammes(texte_reference: str) -> list:
    """
    Tiret 1 : Établir les statistiques des digrammes.
    Retourne une matrice 27x27 (liste de listes).
    """
    char_to_index, _ = creer_dictionnaires_conversion()
    
    # Création d'une grille vierge de 27 lignes et 27 colonnes remplie de zéros.
    matrice_comptage = [[0 for _ in range(27)] for _ in range(27)]
    
    # On parcourt le texte lettre par lettre, en s'arrêtant à l'avant-dernière 
    # pour pouvoir toujours regarder la lettre suivante (i+1).
    for i in range(len(texte_reference) - 1):
        char_actuel = texte_reference[i]
        char_suivant = texte_reference[i+1]
        
        # On vérifie que nos caractères font bien partie de notre alphabet autorisé
        if char_actuel in char_to_index and char_suivant in char_to_index:
            # On traduit nos deux lettres en coordonnées (X, Y)
            idx_actuel = char_to_index[char_actuel]
            idx_suivant = char_to_index[char_suivant]
            
            # On ajoute +1 à cette case précise (ex: si on lit "QU", on incrémente la case [Q][U])
            matrice_comptage[idx_actuel][idx_suivant] += 1
            
    return matrice_comptage

def construire_matrice_transition(matrice_comptage: list) -> list:
    """
    Tiret 2 : Construire la matrice de transitions de taille 27x27.
    Transforme les nombres bruts en probabilités (entre 0.0 et 1.0).
    """
    matrice_probabilites = [[0.0 for _ in range(27)] for _ in range(27)]
    
    for i in range(27):
        # On calcule combien de fois la lettre 'i' a été suivie par n'importe quelle autre lettre
        somme_ligne = sum(matrice_comptage[i])
        
        for j in range(27):
            if somme_ligne == 0:
                # LIGNE COMPLEXE (Sécurité mathématique) :
                # Si une lettre n'est JAMAIS apparue dans le texte (somme = 0), on ne peut pas diviser par zéro.
                # On répartit donc une probabilité égale pour toutes les lettres suivantes (1 chance sur 27).
                matrice_probabilites[i][j] = 1.0 / 27.0
            else:
                # Calcul de probabilité classique : (occurrences du digramme) / (total des digrammes commençant par cette lettre)
                matrice_probabilites[i][j] = matrice_comptage[i][j] / somme_ligne
                
    return matrice_probabilites

def afficher_statistiques_digrammes(matrice_comptage: list):
    """
    Affiche le total et la liste complète des 729 digrammes, 
    triés par ordre d'apparition.
    """
    _, index_to_char = creer_dictionnaires_conversion()
    
    # Calcul du total absolu de digrammes comptés dans toute la grille
    total_digrammes = sum(sum(ligne) for ligne in matrice_comptage)
    
    # Création d'une liste plate pour extraire les données de la grille 2D
    stats = []
    for i in range(27):
        for j in range(27):
            char1 = index_to_char[i]
            char2 = index_to_char[j]
            compte = matrice_comptage[i][j]
            # Calcul du pourcentage d'apparition global
            frequence = (compte / total_digrammes * 100) if total_digrammes > 0 else 0
            stats.append((char1, char2, compte, frequence))
            
    # LIGNE COMPLEXE (Tri par fonction anonyme) :
    # lambda x: x[2] indique à Python de trier la liste en se basant uniquement sur 
    # le 3ème élément de chaque sous-liste (qui correspond au 'compte' brut). 
    # reverse=True met les plus grands nombres en premier.
    stats.sort(key=lambda x: x[2], reverse=True)
    
    # Affichage du résultat
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
    
    # On commence toujours par un espace
    char_actuel = " "
    texte_genere = [char_actuel]
    
    for _ in range(longueur - 1):
        idx_actuel = char_to_index[char_actuel]
        
        # On récupère la ligne de probabilités correspondant à notre lettre actuelle
        # Ex: Si on est sur 'Q', probabilites contiendra une forte valeur pour 'U' et presque 0 pour les autres.
        probabilites = matrice_probabilites[idx_actuel]
        
        # LIGNE COMPLEXE (Le cœur de la génération de Markov) :
        # random.choices tire un nombre au sort (de 0 à 26), MAIS ce tirage est pipé (weights=probabilites).
        # Plus un digramme a un pourcentage élevé dans le tableau, plus il a de chances d'être tiré.
        # [0] extrait la valeur unique renvoyée par la fonction sous forme de liste.
        idx_suivant = random.choices(range(27), weights=probabilites, k=1)[0]
        char_suivant = index_to_char[idx_suivant]
        
        texte_genere.append(char_suivant)
        
        # La lettre que l'on vient de tirer devient notre point de départ pour la boucle suivante
        char_actuel = char_suivant
        
    return "".join(texte_genere)

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    sujet_wiki = "Chiffre_de_Vigenère"
    
    texte_ref = obtenir_texte_reference(sujet_wiki)
    
    if texte_ref:
        print(f"\nCalcul sur un texte de {len(texte_ref)} caractères...")
        
        # Tiret 1 : Comptage et affichage complet
        comptage = compter_digrammes(texte_ref)
        afficher_statistiques_digrammes(comptage)
        
        # Tiret 2 : Création de la matrice de probabilités pour la suite
        probabilites = construire_matrice_transition(comptage)

        # Tiret 3 : Génération de texte aléatoire (qui aura des sonorités françaises !)
        print("\n--- Génération de texte par chaîne de Markov ---")
        texte_aleatoire = generer_texte_markov(probabilites, longueur=150)
        print(f"\nRésultat (150 caractères) :\n{texte_aleatoire}")