import random

def generer_cle(n: int) -> list[int]:
    """
    Génère une clé de permutation aléatoire de taille n.
    Utile pour générer des clés de départ pour l'algorithme MCMC (Partie 1.5).
    """
    # Crée une liste ordonnée de 0 à n-1 (ex: [0, 1, 2, 3])
    cle = list(range(n))
    # Mélange la liste sur place pour créer la permutation aléatoire
    random.shuffle(cle)
    return cle

def muter_permutation(cle_actuelle: list[int]) -> list[int]:
    """
    Crée une variation de la clé en DÉPLAÇANT un sous-bloc entier.
    (Conforme aux exigences de la chaîne de Markov pour la permutation).
    """
    n = len(cle_actuelle)
    if n <= 1:
        return cle_actuelle.copy()
        
    nouvelle_cle = cle_actuelle.copy()
    
    # 1. Choisir aléatoirement la taille du bloc à déplacer (entre 1 et n-1 éléments)
    taille_bloc = random.randint(1, n - 1)
    
    # 2. Choisir l'index de départ du bloc (pour ne pas déborder de la liste)
    index_depart = random.randint(0, n - taille_bloc)
    
    # LIGNE COMPLEXE (Extraction et suppression) :
    # 3. On copie le sous-segment dans 'bloc', puis on utilise 'del' avec le slicing [:] 
    # pour effacer ce segment de la liste d'origine. La liste se rétracte automatiquement.
    bloc = nouvelle_cle[index_depart : index_depart + taille_bloc]
    del nouvelle_cle[index_depart : index_depart + taille_bloc]
    
    # 4. Choisir une nouvelle position d'insertion dans la liste restante
    index_insertion = random.randint(0, len(nouvelle_cle))
    
    # LIGNE COMPLEXE (Réinsertion astucieuse) :
    # 5. En Python, affecter une liste à un slice vide [i:i] insère les éléments 
    # à cet index précis en décalant le reste vers la droite, sans rien écraser.
    nouvelle_cle[index_insertion:index_insertion] = bloc
    
    return nouvelle_cle

def verifier_cle(cle: list[int]) -> bool:
    """
    Vérifie que la clé contient exactement tous les index de 0 à n-1 sans doublon.
    Exemple valide pour une taille de 4 : [3, 0, 2, 1].
    """
    n = len(cle)
    # L'utilisation de set() élimine les doublons. Si la taille et le contenu 
    # correspondent exactement à une suite mathématique parfaite (range), la clé est valide.
    return set(cle) == set(range(n))

def chiffrer_permutation(texte: str, cle: list[int]) -> str:
    """
    Chiffre un texte en déplaçant les caractères de chaque bloc
    vers leurs nouvelles positions.
    """
    n = len(cle)
    
    # LIGNE COMPLEXE (Le Padding / Remplissage) :
    # Le texte doit être un multiple exact de la taille de la clé.
    # L'opérateur modulo (%) trouve le reste de la division. S'il manque des cases,
    # on ajoute le nombre exact d'espaces nécessaires à la fin du texte.
    restant = len(texte) % n
    if restant != 0:
        texte += " " * (n - restant)
        
    resultat = []
    
    # Découpage du texte avec un pas de 'n' (traitement bloc par bloc)
    for i in range(0, len(texte), n):
        bloc_clair = texte[i:i+n]
        
        # On pré-alloue une liste vide de la bonne taille pour accueillir les lettres mélangées
        bloc_chiffre = [''] * n
        
        # On place chaque caractère à sa nouvelle position dictée par la clé
        for pos_initiale, char in enumerate(bloc_clair):
            nouvelle_pos = cle[pos_initiale]
            bloc_chiffre[nouvelle_pos] = char
            
        # extend() ajoute le contenu de la liste à notre résultat global, contrairement à append() 
        # qui ajouterait la liste elle-même (créant des listes imbriquées).
        resultat.extend(bloc_chiffre)
        
    return "".join(resultat)

def inverser_cle(cle: list[int]) -> list[int]:
    """
    Construit la clé inverse. Si l'index 0 va à la position 3, 
    la clé inverse dira que l'index 3 retourne à la position 0.
    """
    n = len(cle)
    # On prépare une liste pleine de zéros de la même taille
    cle_inverse = [0] * n
    
    # La logique est inversée : la position d'arrivée ('pos_cible') de la clé d'origine 
    # devient l'index de notre nouvelle clé, et on y stocke la position de départ.
    for pos_initiale, pos_cible in enumerate(cle):
        cle_inverse[pos_cible] = pos_initiale
        
    return cle_inverse

def dechiffrer_permutation(cryptogramme: str, cle: list[int]) -> str:
    """
    Déchiffre le texte en appliquant la clé inverse.
    """
    # C'est la beauté mathématique de la permutation : déchiffrer, 
    # c'est simplement chiffrer à nouveau mais avec le chemin de retour.
    cle_inverse = inverser_cle(cle)
    return chiffrer_permutation(cryptogramme, cle_inverse)

# ==========================================
# EXECUTION TEST
# ==========================================
if __name__ == "__main__":
    print("--- TEST 1 : Exemple exact du sujet ---")
    cle_exemple = [3, 0, 2, 1]
    texte = "BONJOUR"
    
    if verifier_cle(cle_exemple):
        chiffre = chiffrer_permutation(texte, cle_exemple)
        dechiffre = dechiffrer_permutation(chiffre, cle_exemple)
        
        print(f"Clé utilisée  : {cle_exemple}")
        print(f"Clé inverse   : {inverser_cle(cle_exemple)}")
        print(f"Texte clair   : '{texte}'")
        print(f"Cryptogramme  : '{chiffre}'")
        print(f"Texte retrouvé: '{dechiffre}'")
        
    print("\n--- TEST 2 : Test avec une clé aléatoire ---")
    taille_bloc = 6 # On choisit une taille de bloc au hasard
    cle_aleatoire = generer_cle(taille_bloc)
    texte_long = "LE PROJET AVANCE SUPER BIEN"
    
    if verifier_cle(cle_aleatoire):
        chiffre_alea = chiffrer_permutation(texte_long, cle_aleatoire)
        dechiffre_alea = dechiffrer_permutation(chiffre_alea, cle_aleatoire)
        
        print(f"Clé générée (taille {taille_bloc}) : {cle_aleatoire}")
        print(f"Texte clair   : '{texte_long}'")
        print(f"Cryptogramme  : '{chiffre_alea}'")
        print(f"Texte retrouvé: '{dechiffre_alea}'")