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

# ==========================================
# EXECUTION TEST
# ==========================================
if __name__ == "__main__":
    print("--- Test des outils de substitution (Section 1.3) ---")
    
    # 1. Définition et vérification (Tiret 1)
    ma_cle = generer_cle()
    print(f"Alphabet clair : {ALPHABET_26}")
    print(f"Clé générée    : {ma_cle}")
    
    if verifier_cle(ma_cle):
        print("\n[OK] La clé est valide.")
        
        # 2. Chiffrement (Tiret 2)
        texte_original = "LE PROJET AVANCE TRES BIEN"
        print(f"\nTexte clair    : {texte_original}")
        
        cryptogramme = chiffrer_texte(texte_original, ma_cle)
        print(f"Cryptogramme   : {cryptogramme}")