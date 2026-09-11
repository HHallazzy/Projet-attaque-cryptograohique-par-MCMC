import random
import json
import os
from collections import Counter
from wiki_statistiques import obtenir_texte_reference

# On utilise ici un alphabet strict de 26 lettres car le sujet précise 
# que l'espace est conservé tel quel (il n'est pas permuté).
ALPHABET_26 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Ordre d'apparition par défaut (au cas où le fichier JSON de la partie 1.2 manque)
ORDRE_FREQ_FR = "EAISTNRULODMPCVQGBFJHZXYKW"

def generer_cle() -> str:
    """
    Tiret 1 (Partie 1) : Définir une clé de chiffrement.
    Génère une permutation aléatoire des 26 lettres de l'alphabet.
    """
    lettres = list(ALPHABET_26)
    random.shuffle(lettres)
    return "".join(lettres)

def verifier_cle(cle: str) -> bool:
    """
    Tiret 1 (Partie 2) : Vérifier une clé de chiffrement.
    Contrôle que la clé fait bien 26 caractères et contient 
    exactement une fois chaque lettre de l'alphabet.
    """
    if len(cle) != 26:
        print("Erreur : La clé doit contenir exactement 26 caractères.")
        return False
        
    if set(cle) != set(ALPHABET_26):
        print("Erreur : La clé contient des doublons ou des caractères non autorisés.")
        return False
        
    return True

def chiffrer_texte(texte_clair: str, cle: str) -> str:
    """
    Tiret 2 : Appliquer la clé à un texte clair pour obtenir un cryptogramme.
    Remplace chaque lettre selon la permutation de la clé, en ignorant les espaces.
    """
    table_substitution = str.maketrans(ALPHABET_26, cle)
    texte_chiffre = texte_clair.translate(table_substitution)
    return texte_chiffre

def inverser_cle(cle: str) -> str:
    """
    Tiret 3 : Construire l'inverse de cette clé quand elle est connue.
    Permet de retrouver la permutation exacte pour le déchiffrement.
    """
    cle_inverse = "".join(ALPHABET_26[cle.index(lettre)] for lettre in ALPHABET_26)
    return cle_inverse

def dechiffrer_texte(cryptogramme: str, cle: str) -> str:
    """
    Tiret 4 : Déchiffrer un texte chiffré avec une clé connue.
    """
    cle_inverse = inverser_cle(cle)
    table_substitution = str.maketrans(ALPHABET_26, cle_inverse)
    texte_dechiffre = cryptogramme.translate(table_substitution)
    return texte_dechiffre

# ==========================================
# ATTAQUE SEQUENTIELLE INTERACTIVE (Saisie Manuelle)
# ==========================================

def appliquer_traduction_partielle(cryptogramme: str, cle_trouvee: dict) -> str:
    """
    Applique les correspondances validées au texte.
    Affiche des '_' pour les lettres non encore décodées.
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
    Mode interactif manuel : Affiche les statistiques et laisse l'utilisateur
    saisir ses propres choix avec des contrôles de sécurité.
    """
    # 1. Chargement des statistiques
    chemin_stats = "data/stats_reference.json"
    ordre_reference = list(ORDRE_FREQ_FR) 
    
    if os.path.exists(chemin_stats):
        try:
            with open(chemin_stats, 'r', encoding='utf-8') as fichier:
                stats = json.load(fichier)
                if 'ordre_lettres' in stats:
                    ordre_reference = stats['ordre_lettres']
                    print(f"[INFO] Stats de la base de données chargées avec succès !")
        except Exception:
            print("[ATTENTION] Erreur de lecture du JSON. Utilisation des stats par défaut.")
    else:
        print("[ATTENTION] Fichier JSON introuvable. Utilisation des stats par défaut.")

    # 2. Analyse des fréquences du cryptogramme
    lettres_chiffrees = cryptogramme.replace(" ", "")
    compteur = Counter(lettres_chiffrees)
    lettres_triees = [lettre for lettre, freq in compteur.most_common()]
    
    cle_trouvee = {} # Dictionnaire des validations (ex: {X->E, Y->T})
    
    print("\n" + "="*50)
    print(" DÉBUT DE L'ATTAQUE INTERACTIVE (MODE MANUEL)")
    print("="*50)
    
    # 3. Boucle d'analyse pour chaque lettre chiffrée
    for lettre_chif in lettres_triees:
        valide = False
        
        while not valide:
            # On calcule les lettres claires qui n'ont pas encore été utilisées
            lettres_disponibles = [L for L in ordre_reference if L not in cle_trouvee.values()]
            
            if not lettres_disponibles:
                break # L'alphabet complet a été trouvé
                
            # Affichage de l'aperçu du texte (limité à 300 caractères pour la lisibilité)
            apercu = ""
            for char in cryptogramme[:300]:
                if char == " ":
                    apercu += " "
                elif char in cle_trouvee:
                    apercu += cle_trouvee[char]
                elif char == lettre_chif:
                    apercu += "[?]" # Mise en évidence de la lettre en cours de traitement
                else:
                    apercu += "_"
                    
            print(f"\n[APERÇU] : {apercu}")
            print(f"La lettre chiffrée '{lettre_chif}' est apparue {compteur[lettre_chif]} fois.")
            
            # Affichage de l'aide à la décision
            print(f"-> Déjà validé : {', '.join(f'{k}->{v}' for k, v in cle_trouvee.items())}")
            print(f"-> Lettres dispo (par ordre de proba) : {', '.join(lettres_disponibles)}")
            
            # Saisie utilisateur sécurisée : utilisation de 1 et 2 pour éviter le conflit avec les lettres
            choix = input(f"Saisissez la lettre claire (1 = Passer, 2 = Quitter) : ").strip().upper()
            
            if choix == '2':
                print("\n[INFO] Arrêt de l'analyse interactive.")
                return appliquer_traduction_partielle(cryptogramme, cle_trouvee)
                
            elif choix == '1' or choix == '': # On accepte aussi la touche "Entrée" vide pour passer vite
                print(f"[INFO] Vous avez passé la lettre '{lettre_chif}'.")
                break # On sort du while pour passer à la lettre chiffrée suivante
                
            # Vérifications de sécurité de la saisie
            elif len(choix) != 1 or choix not in ALPHABET_26:
                print("[ERREUR] Saisie invalide. Veuillez entrer UNE seule lettre de A à Z (ou 1 / 2).")
                
            elif choix in cle_trouvee.values():
                print(f"[ERREUR] Vous avez déjà utilisé la lettre '{choix}' ! Choisissez-en une autre.")
                
            else:
                cle_trouvee[lettre_chif] = choix
                valide = True
                print(f"[SUCCÈS] '{lettre_chif}' est maintenant remplacé par '{choix}'.")
                
    print("\n" + "="*50)
    print(" FIN DE L'ATTAQUE INTERACTIVE")
    print("="*50)
    return appliquer_traduction_partielle(cryptogramme, cle_trouvee)

# ==========================================
# EXECUTION TEST
# ==========================================
if __name__ == "__main__":
    print("Test des outils de substitution (Section 1.3)")
    
    ma_cle = generer_cle()
    
    if verifier_cle(ma_cle):
        print("\n--- Récupération d'un texte pour l'attaque ---")
        texte_wiki = obtenir_texte_reference("Chiffre_de_Vigenère")
        
        if texte_wiki:
            texte_test = texte_wiki[:2000]
            cryptogramme_test = chiffrer_texte(texte_test, ma_cle)
            
            print(f"\nCryptogramme généré ({len(cryptogramme_test)} caractères).")
            print("Lancement de l'assistant de cryptanalyse...")
            
            texte_craque = attaque_frequentielle(cryptogramme_test)
            
            print(f"\nRésultat final de votre attaque :\n{texte_craque[:500]}...")