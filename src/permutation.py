def verifier_cle(cle: list[int]) -> bool:
    """
    Vérifie que la clé contient exactement tous les index de 0 à n-1 sans doublon.
    Exemple valide pour une taille de 4 : [3, 0, 2, 1].
    """
    n = len(cle)
    return set(cle) == set(range(n))

def chiffrer_permutation(texte: str, cle: list[int]) -> str:
    """
    Chiffre un texte en déplaçant les caractères de chaque bloc
    vers leurs nouvelles positions.
    """
    n = len(cle)
    
    # Le texte doit être un multiple de la taille de la clé
    restant = len(texte) % n
    if restant != 0:
        texte += " " * (n - restant)
        
    resultat = []
    
    # Découpage et traitement par blocs
    for i in range(0, len(texte), n):
        bloc_clair = texte[i:i+n]
        bloc_chiffre = [''] * n
        
        # On place chaque caractère à sa nouvelle position
        for pos_initiale, char in enumerate(bloc_clair):
            nouvelle_pos = cle[pos_initiale]
            bloc_chiffre[nouvelle_pos] = char
            
        resultat.extend(bloc_chiffre)
        
    return "".join(resultat)

def inverser_cle(cle: list[int]) -> list[int]:
    """
    Construit la clé inverse. Si l'index 0 va à la position 3, 
    la clé inverse dira que l'index 3 retourne à la position 0.
    """
    n = len(cle)
    cle_inverse = [0] * n
    
    for pos_initiale, pos_cible in enumerate(cle):
        cle_inverse[pos_cible] = pos_initiale
        
    return cle_inverse

def dechiffrer_permutation(cryptogramme: str, cle: list[int]) -> str:
    """
    Déchiffre le texte en appliquant la clé inverse.
    """
    cle_inverse = inverser_cle(cle)
    return chiffrer_permutation(cryptogramme, cle_inverse)

# ==========================================
# EXECUTION TEST
# ==========================================
if __name__ == "__main__":
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