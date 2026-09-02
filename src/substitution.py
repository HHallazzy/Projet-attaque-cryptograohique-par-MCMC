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

# ==========================================
# EXECUTION TEST
# ==========================================
if __name__ == "__main__":
    print("--- Test du premier tiret (Section 1.3) ---")
    
    # Définition
    ma_cle = generer_cle()
    print(f"Alphabet clair : {ALPHABET_26}")
    print(f"Clé générée    : {ma_cle}")
    
    # Vérification
    est_valide = verifier_cle(ma_cle)
    print(f"\nLa clé générée est-elle valide ? {'Oui' if est_valide else 'Non'}")
    
    # Test d'une clé cassée pour prouver que la vérification fonctionne
    cle_cassee = "AABCDEFGHIJKLMNOPQRSTUVWXY" # Deux fois 'A', pas de 'Z'
    print(f"\nTest d'une clé cassée ({cle_cassee}) :")
    verifier_cle(cle_cassee)