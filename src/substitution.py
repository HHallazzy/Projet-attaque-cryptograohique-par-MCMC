"""
Module dédié au chiffrement par substitution mono-alphabétique.
Gère la génération, l'application et l'inversion des clés cryptographiques.
Fournit également l'opérateur de mutation (voisinage) indispensable à la chaîne 
de Markov (MCMC), ainsi qu'une interface d'attaque fréquentielle interactive.
"""

import random
import json
import os
from collections import Counter
from wiki_statistiques import obtenir_texte_reference

# L'espace cryptographique est strictement limité aux 26 lettres majuscules.
# Conformément au cahier des charges, les espaces sont préservés et exclus de la permutation.
ALPHABET_26 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Distribution statistique théorique de la langue française (Ordre décroissant de fréquence)
# Utilisée comme solution de repli (Fallback) si le modèle JSON de la partie 1.2 est inaccessible.
ORDRE_FREQ_FR = "EAISTNRULODMPCVQGBFJHZXYKW"

def generer_cle() -> str:
    """
    Tiret 1 (Partie 1) : Définir une clé de chiffrement.
    Génère une clé en créant une permutation aléatoire uniforme de l'alphabet standard.
    L'espace des clés possibles est de 26! (environ 4.03 x 10^26).
    """
    lettres = list(ALPHABET_26)
    random.shuffle(lettres)
    return "".join(lettres)

def muter_substitution(cle_actuelle: str) -> str:
    """
    Génère un état voisin pour l'algorithme Metropolis-Hastings (MCMC).
    La mutation consiste en une simple transposition (échange) de deux lettres choisies 
    selon une loi de probabilité uniforme, garantissant la réversibilité de la chaîne de Markov.
    """
    cle_liste = list(cle_actuelle)
    
    # Échantillonnage sans remise de 2 indices distincts
    i, j = random.sample(range(26), 2)
    
    # Transposition des deux éléments (Swap O(1))
    cle_liste[i], cle_liste[j] = cle_liste[j], cle_liste[i]
    
    return "".join(cle_liste)

def verifier_cle(cle: str) -> bool:
    """
    Tiret 1 (Partie 2) : Vérifier une clé de chiffrement.
    Valide l'intégrité structurelle de la clé (bijection parfaite avec l'alphabet).
    """
    if len(cle) != 26:
        print("[ERREUR] La clé doit contenir exactement 26 caractères.")
        return False
        
    # L'utilisation d'un Set (Ensemble) permet de vérifier l'absence de doublons en O(N)
    if set(cle) != set(ALPHABET_26):
        print("[ERREUR] La clé contient des doublons ou des caractères non autorisés.")
        return False
        
    return True

def chiffrer_texte(texte_clair: str, cle: str) -> str:
    """
    Tiret 2 : Appliquer la clé à un texte clair pour obtenir un cryptogramme.
    Utilise la méthode optimisée en C de Python (str.maketrans et translate) 
    pour un traitement de complexité O(L) où L est la longueur du texte.
    """
    table_substitution = str.maketrans(ALPHABET_26, cle)
    return texte_clair.translate(table_substitution)

def inverser_cle(cle: str) -> str:
    """
    Tiret 3 : Construire l'inverse de cette clé quand elle est connue.
    Calcule la permutation inverse K^(-1) telle que E(D(Texte, K), K^(-1)) = Texte.
    """
    # Pour chaque lettre de l'alphabet standard, on cherche sa position dans la clé chiffrée
    return "".join(ALPHABET_26[cle.index(lettre)] for lettre in ALPHABET_26)

def dechiffrer_texte(cryptogramme: str, cle: str) -> str:
    """
    Tiret 4 : Déchiffrer un texte chiffré avec une clé connue.
    Applique la table de traduction générée par l'inversion de la clé.
    """
    cle_inverse = inverser_cle(cle)
    table_substitution = str.maketrans(ALPHABET_26, cle_inverse)
    return cryptogramme.translate(table_substitution)

# ==========================================
# ATTAQUE SÉQUENTIELLE INTERACTIVE (Section 1.3)
# ==========================================

def appliquer_traduction_partielle(cryptogramme: str, cle_trouvee: dict) -> str:
    """
    Applique un masque de déchiffrement partiel sur le cryptogramme.
    Les caractères dont la substitution est inconnue sont masqués par un underscore '_'.
    """
    resultat = ""
    for char in cryptogramme:
        if char == " ":
            resultat += " "
        elif char in cle_trouvee:
            resultat += cle_trouvee[char]
        else:
            resultat += "_"
    return resultat

def attaque_frequentielle(cryptogramme: str) -> str:
    """
    Tiret 5 : Développer une attaque fréquentielle (Section 1.3).
    Processus interactif assisté : le système propose des substitutions basées sur 
    l'analyse de fréquence (unigrammes), et l'utilisateur valide ou rejette les choix.
    """
    # 1. Chargement de la distribution statistique (Modèle d'entraînement)
    chemin_stats = "data/stats_reference.json"
    ordre_reference = list(ORDRE_FREQ_FR) 
    
    if os.path.exists(chemin_stats):
        try:
            with open(chemin_stats, 'r', encoding='utf-8') as fichier:
                stats = json.load(fichier)
                if 'ordre_lettres' in stats:
                    ordre_reference = stats['ordre_lettres']
                    print("[INFO] Statistiques de la base de données chargées avec succès.")
        except Exception:
            print("[ATTENTION] Erreur de lecture du JSON. Bascule sur la distribution théorique par défaut.")
    else:
        print("[ATTENTION] Modèle JSON introuvable. Bascule sur la distribution théorique par défaut.")

    # 2. Extraction des fréquences d'apparition dans le texte chiffré
    lettres_chiffrees = cryptogramme.replace(" ", "")
    compteur = Counter(lettres_chiffrees)
    
    # Tri décroissant des lettres selon leur occurrence
    lettres_triees = [lettre for lettre, freq in compteur.most_common()]
    
    # Dictionnaire de correspondance validée par l'utilisateur (ex: {'X': 'E'})
    cle_trouvee = {}
    
    print("\n" + "="*50)
    print(" DÉBUT DE L'ATTAQUE INTERACTIVE (MODE MANUEL)")
    print("="*50)
    
    # 3. Résolution itérative guidée par l'utilisateur
    for lettre_chif in lettres_triees:
        valide = False
        
        while not valide:
            # Identification de l'espace des lettres claires non encore assignées
            lettres_disponibles = [L for L in ordre_reference if L not in cle_trouvee.values()]
            
            if not lettres_disponibles:
                break
                
            # Génération de l'aperçu textuel contextuel (Tronqué à 300 caractères)
            apercu = ""
            for char in cryptogramme[:300]:
                if char == " ":
                    apercu += " "
                elif char in cle_trouvee:
                    apercu += cle_trouvee[char]
                elif char == lettre_chif:
                    apercu += "[?]" # Focalisation visuelle sur le caractère en cours d'analyse
                else:
                    apercu += "_"
                    
            print(f"\n[APERÇU] : {apercu}")
            print(f"La lettre chiffrée '{lettre_chif}' est apparue {compteur[lettre_chif]} fois.")
            print(f"-> Déjà validé : {', '.join(f'{k}->{v}' for k, v in cle_trouvee.items())}")
            print(f"-> Lettres dispo (par ordre de probabilité) : {', '.join(lettres_disponibles)}")
            
            # Saisie sécurisée des instructions utilisateur
            choix = input("Saisissez la lettre claire (1 = Passer, 2 = Quitter) : ").strip().upper()
            
            if choix == '2':
                print("\n[INFO] Interruption de l'analyse interactive par l'utilisateur.")
                return appliquer_traduction_partielle(cryptogramme, cle_trouvee)
                
            elif choix == '1' or choix == '':
                print(f"[INFO] Analyse de la lettre '{lettre_chif}' différée.")
                break 
                
            # Validation de l'intégrité de la saisie (Protection contre les erreurs de frappe)
            elif len(choix) != 1 or choix not in ALPHABET_26:
                print("[ERREUR] Entrée non valide. Saisissez une unique lettre de A à Z.")
                
            elif choix in cle_trouvee.values():
                print(f"[ERREUR] La lettre '{choix}' est déjà assignée dans la clé partielle.")
                
            else:
                cle_trouvee[lettre_chif] = choix
                valide = True
                print(f"[SUCCÈS] Mappage enregistré : '{lettre_chif}' -> '{choix}'.")
                
    print("\n" + "="*50)
    print(" FIN DE L'ATTAQUE INTERACTIVE")
    print("="*50)
    return appliquer_traduction_partielle(cryptogramme, cle_trouvee)

# ==========================================
# MODULE DE TEST UNITAIRE
# ==========================================
if __name__ == "__main__":
    print("Test d'intégration des outils de substitution (Section 1.3)")
    
    ma_cle = generer_cle()
    
    if verifier_cle(ma_cle):
        print("\n--- Récupération d'un corpus de texte pour le banc d'essai ---")
        texte_wiki = obtenir_texte_reference("Chiffre_de_Vigenère")
        
        if texte_wiki:
            texte_test = texte_wiki[:2000]
            cryptogramme_test = chiffrer_texte(texte_test, ma_cle)
            
            print(f"\nCryptogramme cible généré ({len(cryptogramme_test)} caractères).")
            print("Initialisation de l'assistant de cryptanalyse fréquentielle...")
            
            texte_craque = attaque_frequentielle(cryptogramme_test)
            
            print(f"\nRésultat final restitué :\n{texte_craque[:500]}...")