import random
from collections import Counter
from wiki_statistiques import obtenir_texte_reference

# On utilise ici un alphabet strict de 26 lettres car le sujet précise 
# que l'espace est conservé tel quel (il n'est pas permuté).
ALPHABET_26 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Ordre d'apparition des lettres en français (approximatif, du plus fréquent au moins fréquent)
ORDRE_FREQ_FR = "EAISTNRULODMPCVQGBFJHZXYKW"

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
    # On vérifie la longueur
    if len(cle) != 26:
        print("Erreur : La clé doit contenir exactement 26 caractères.")
        return False
        
    # on vérifie que les caractères uniques correspondent exactement à A-Z
    # on utilise set() pour éliminer les doublons automatiquement.
    if set(cle) != set(ALPHABET_26):
        print("Erreur : La clé contient des doublons ou des caractères non autorisés.")
        return False
        
    return True

def chiffrer_texte(texte_clair: str, cle: str) -> str:
    """
    Tiret 2 : Appliquer la clé à un texte clair pour obtenir un cryptogramme.
    Remplace chaque lettre selon la permutation de la clé, en ignorant les espaces.
    """
    # On crée une table de correspondance entre l'alphabet normal et la clé
    table_substitution = str.maketrans(ALPHABET_26, cle)
    
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
    # On calcule la clé inverse
    cle_inverse = inverser_cle(cle)
    
    # On applique exactement la même mécanique optimisée que pour le chiffrement
    table_substitution = str.maketrans(ALPHABET_26, cle_inverse)
    texte_dechiffre = cryptogramme.translate(table_substitution)
    
    return texte_dechiffre

def attaque_frequentielle(cryptogramme: str) -> str:
    """
    Tiret 5 : Développer une attaque fréquentielle (Section 1.3).
    Tente de casser le cryptogramme en calquant ses fréquences sur celles du français.
    """
    # 1. On compte toutes les lettres du texte chiffré (en retirant les espaces pour ne pas les compter)
    lettres_chiffrees = cryptogramme.replace(" ", "")
    compteur = Counter(lettres_chiffrees)
    
    # 2. On récupère la liste des lettres chiffrées, triées de la plus à la moins fréquente
    lettres_triees = [lettre for lettre, frequence in compteur.most_common()]
    
    # 3. Si le texte est court, il manque peut-être des lettres de l'alphabet. On complète avec le reste.
    lettres_manquantes = [lettre for lettre in ALPHABET_26 if lettre not in lettres_triees]
    lettres_triees.extend(lettres_manquantes)
    
    lettres_chiffrees_ordonnees = "".join(lettres_triees)
    
    # 4. On crée la table de traduction : la lettre n°1 chiffrée devient E, la n°2 devient A, etc.
    table_craquage = str.maketrans(lettres_chiffrees_ordonnees, ORDRE_FREQ_FR)
    
    # 5. On applique la traduction au cryptogramme
    texte_craque = cryptogramme.translate(table_craquage)
    
    return texte_craque

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

        # 5. Attaque fréquentielle (Tiret 5) sur une page Wikipédia
        print("\n--- Lancement de l'attaque fréquentielle sur la page entière ---")
        
        texte_wiki = obtenir_texte_reference("Chiffre_de_Vigenère")
        
        if texte_wiki:
            print(f"\nChiffrement puis attaque sur la totalité des {len(texte_wiki)} caractères...")
            
            # On chiffre la page
            cryptogramme_long = chiffrer_texte(texte_wiki, ma_cle)
            
            # On attaque sur toute la page
            texte_craque = attaque_frequentielle(cryptogramme_long)
            
            # On affiche les 500 premiers caractères pour voir le résultat
            print(f"\nRésultat attaque (extrait) : \n{texte_craque[:500]}...\n")
            
            if texte_wiki != texte_craque:
                print("Le résultat n'est pas compréhensible, mais on peut déjà voir des mots français apparaître comme 'DE', 'EST'...")