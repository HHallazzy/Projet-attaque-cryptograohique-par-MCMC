def chiffrer_cesar(texte: str, cle: int) -> str:
    """
    Chiffre un texte avec le chiffre de César.
    Conserve les espaces, modifie uniquement les lettres de A à Z.
    """
    resultat = []
    # On standardise tout en majuscules pour simplifier les calculs mathématiques
    for char in texte.upper():
        # On ne chiffre que les lettres de l'alphabet (on ignore la ponctuation, etc.)
        if 'A' <= char <= 'Z':
            # LIGNE COMPLEXE (La mécanique de César) :
            # 1. ord(char) - ord('A') : Convertit la lettre en un chiffre de 0 (A) à 25 (Z).
            # 2. + cle : Applique le décalage demandé.
            # 3. % 26 : L'opérateur modulo agit comme un cadran. Si on dépasse Z (25), on repart à A (0).
            code = (ord(char) - ord('A') + cle) % 26
            
            # chr(...) fait l'inverse : il retransforme notre chiffre (0-25) en vraie lettre ASCII
            resultat.append(chr(code + ord('A')))
            
        # Si le caractère est un espace, on l'ajoute tel quel sans le chiffrer
        elif char == ' ':
            resultat.append(' ')
            
    # On recolle la liste de caractères pour former la chaîne finale
    return "".join(resultat)

def dechiffrer_cesar(texte: str, cle: int) -> str:
    """
    Déchiffre un texte chiffré par César.
    """
    # Astuce élégante : Déchiffrer un décalage de +3, c'est simplement chiffrer avec un décalage de -3.
    # On réutilise donc notre fonction précédente pour éviter de dupliquer le code.
    return chiffrer_cesar(texte, -cle)


def chiffrer_vigenere(texte: str, mot_cle: str) -> str:
    """
    Chiffre un texte avec le chiffre de Vigenère.
    Le mot-clé ne s'applique qu'aux lettres (ignore les espaces dans l'avancement de la clé).
    """
    resultat = []
    # On s'assure que la clé est propre (majuscules, sans espaces)
    mot_cle = mot_cle.upper().replace(" ", "")
    
    # On doit suivre manuellement l'avancement dans le mot-clé.
    # On ne peut pas utiliser la boucle 'for' du texte, car les espaces dans le texte
    # ne doivent pas faire avancer la clé (sinon ça désynchronise tout).
    index_cle = 0 
    
    for char in texte.upper():
        if 'A' <= char <= 'Z':
            # LIGNE COMPLEXE (Le décalage dynamique) :
            # On cherche quelle lettre de la clé utiliser avec : mot_cle[index_cle % len(mot_cle)]
            # Le modulo permet de répéter la clé à l'infini (ex: MCMC MCMC MCMC).
            # Ensuite, on convertit cette lettre en valeur de décalage (A=0, B=1, C=2...).
            decalage = ord(mot_cle[index_cle % len(mot_cle)]) - ord('A')
            
            # Même mécanique que César, mais avec notre décalage variable
            code = (ord(char) - ord('A') + decalage) % 26
            resultat.append(chr(code + ord('A')))
            
            # On n'avance dans le mot-clé que si on a effectivement chiffré une lettre
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
            # On récupère le décalage dynamique de la même manière qu'au chiffrement
            decalage = ord(mot_cle[index_cle % len(mot_cle)]) - ord('A')
            
            # LIGNE COMPLEXE (L'inversion) :
            # Au lieu de faire '+ decalage', on fait '- decalage' pour revenir en arrière.
            # Le modulo 26 gère parfaitement les nombres négatifs en Python (ex: -1 % 26 = 25, soit 'Z').
            code = (ord(char) - ord('A') - decalage) % 26
            resultat.append(chr(code + ord('A')))
            
            index_cle += 1
            
        elif char == ' ':
            resultat.append(' ')
            
    return "".join(resultat)


# --- Tests pour valider les fonctions ---
# Ce bloc ne s'exécute que si on lance ce fichier directement (pratique pour tester).
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