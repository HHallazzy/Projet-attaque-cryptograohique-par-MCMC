import random

# On utilise ici un alphabet strict de 26 lettres car le sujet précise 
# que l'espace est conservé tel quel (il n'est pas permuté).
ALPHABET_26 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def generer_cle() -> str:
    """
    Tiret 1 (Partie 1) : Définir une clé de chiffrement.
    Génère une permutation aléatoire des 26 lettres de l'alphabet.
    """
    # On transforme la chaîne en liste pour pouvoir la mélanger
    lettres = list(ALPHABET_26)
    
    # Mélange aléatoire (permutation)
    random.shuffle(lettres)
    
    # On reforme une chaîne de caractères
    return "".join(lettres)

def verifier_cle(cle: str) -> bool:
    """
    Tiret 1 (Partie 2) : Vérifier une clé de chiffrement.
    Contrôle que la clé fait bien 26 caractères et contient 
    exactement une fois chaque lettre de l'alphabet.
    """
    # Vérification 1 : La longueur
    if len(cle) != 26:
        print("Erreur : La clé doit contenir exactement 26 caractères.")
        return False
        
    # Vérification 2 : Les caractères uniques correspondent exactement à A-Z
    # L'utilisation de set() élimine les doublons automatiquement.
    if set(cle) != set(ALPHABET_26):
        print("Erreur : La clé contient des doublons ou des caractères non autorisés.")
        return False
        
    return True

def chiffrer_texte(texte_clair: str, cle: str) -> str:
    """
    Tiret 2 : Appliquer la clé à un texte clair pour obtenir un cryptogramme.
    Remplace chaque lettre selon la permutation de la clé, en ignorant les espaces.
    """
    # Création d'une table de correspondance (mapping) entre l'alphabet normal et la clé
    table_substitution = str.maketrans(ALPHABET_26, cle)
    
    # La méthode translate parcourt la chaîne en C (très rapide) et remplace
    # les caractères selon la table. Tout caractère absent de la table (l'espace)
    # reste strictement inchangé.
    texte_chiffre = texte_clair.translate(table_substitution)
    
    return texte_chiffre

def inverser_cle(cle: str) -> str:
    """
    Tiret 3 : Construire l'inverse de cette clé quand elle est connue.
    Permet de retrouver la permutation exacte pour le déchiffrement.
    """
    # Pour chaque lettre de A à Z (ALPHABET_26), on cherche sa position dans la clé chiffrée.
    # Cette position nous donne l'index de la lettre claire d'origine.
    cle_inverse = "".join(ALPHABET_26[cle.index(lettre)] for lettre in ALPHABET_26)
    
    return cle_inverse

def dechiffrer_texte(cryptogramme: str, cle: str) -> str:
    """
    Tiret 4 : Déchiffrer un texte chiffré avec une clé connue.
    """
    # 1. On calcule la clé inverse
    cle_inverse = inverser_cle(cle)
    
    # 2. On applique exactement la même mécanique optimisée que pour le chiffrement
    table_substitution = str.maketrans(ALPHABET_26, cle_inverse)
    texte_dechiffre = cryptogramme.translate(table_substitution)
    
    return texte_dechiffre

# ==========================================
# EXECUTION TEST
# ==========================================
if __name__ == "__main__":
    print("Test des outils de substitution (Section 1.3)")
    
    # 1. Définition et vérification (Tiret 1)
    ma_cle = generer_cle()
    print(f"Alphabet clair : {ALPHABET_26}")
    print(f"Clé générée    : {ma_cle}")
    
    if verifier_cle(ma_cle):
        # 2. Chiffrement (Tiret 2)
        texte_original = "LE PROJET AVANCE TRES BIEN"
        print(f"\nTexte clair    : {texte_original}")
        
        cryptogramme = chiffrer_texte(texte_original, ma_cle)
        print(f"Cryptogramme   : {cryptogramme}")
        
        # 3. Inversion de la clé (Tiret 3)
        cle_inverse = inverser_cle(ma_cle)
        print(f"\nClé inverse    : {cle_inverse}")
        
        # 4. Déchiffrement (Tiret 4)
        texte_retrouve = dechiffrer_texte(cryptogramme, ma_cle)
        print(f"Texte retrouvé : {texte_retrouve}")
        
        # Vérification finale
        if texte_original == texte_retrouve:
            print("\n[SUCCÈS] Le cycle chiffrement/déchiffrement fonctionne parfaitement.")