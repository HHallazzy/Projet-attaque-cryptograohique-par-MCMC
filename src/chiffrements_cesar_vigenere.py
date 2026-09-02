def chiffrer_cesar(texte: str, cle: int) -> str:
    """
    Chiffre un texte avec le chiffre de César.
    Conserve les espaces, modifie uniquement les lettres de A à Z.
    """
    resultat = []
    for char in texte.upper():
        if 'A' <= char <= 'Z':
            # Décalage dans l'alphabet de 26 lettres
            code = (ord(char) - ord('A') + cle) % 26
            resultat.append(chr(code + ord('A')))
        elif char == ' ':
            resultat.append(' ')
    return "".join(resultat)

def dechiffrer_cesar(texte: str, cle: int) -> str:
    """
    Déchiffre un texte chiffré par César.
    """
    return chiffrer_cesar(texte, -cle)


def chiffrer_vigenere(texte: str, mot_cle: str) -> str:
    """
    Chiffre un texte avec le chiffre de Vigenère.
    Le mot-clé ne s'applique qu'aux lettres (ignore les espaces dans l'avancement de la clé).
    """
    resultat = []
    mot_cle = mot_cle.upper().replace(" ", "")
    index_cle = 0
    
    for char in texte.upper():
        if 'A' <= char <= 'Z':
            decalage = ord(mot_cle[index_cle % len(mot_cle)]) - ord('A')
            code = (ord(char) - ord('A') + decalage) % 26
            resultat.append(chr(code + ord('A')))
            index_cle += 1
        elif char == ' ':
            resultat.append(' ')
    return "".join(resultat)

def dechiffrer_vigenere(texte: str, mot_cle: str) -> str:
    """
    Déchiffre un texte chiffré par Vigenère.
    """
    resultat = []
    mot_cle = mot_cle.upper().replace(" ", "")
    index_cle = 0
    
    for char in texte.upper():
        if 'A' <= char <= 'Z':
            decalage = ord(mot_cle[index_cle % len(mot_cle)]) - ord('A')
            code = (ord(char) - ord('A') - decalage) % 26
            resultat.append(chr(code + ord('A')))
            index_cle += 1
        elif char == ' ':
            resultat.append(' ')
    return "".join(resultat)


# --- Tests pour valider les fonctions ---
if __name__ == "__main__":
    clair = "LE PROJET CRYPTO EST LANCE"
    
    # Test César
    chiffre_c = chiffrer_cesar(clair, 3)
    dechiffre_c = dechiffrer_cesar(chiffre_c, 3)
    print(f"César Chiffré : {chiffre_c}")
    print(f"César Déchiffré: {dechiffre_c}\n")
    
    # Test Vigenère
    cle_v = "MCMC"
    chiffre_v = chiffrer_vigenere(clair, cle_v)
    dechiffre_v = dechiffrer_vigenere(chiffre_v, cle_v)
    print(f"Vigenère Chiffré : {chiffre_v}")
    print(f"Vigenère Déchiffré: {dechiffre_v}")