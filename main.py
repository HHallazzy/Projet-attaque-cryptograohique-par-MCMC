import sys
import os
import json

sys.path.insert(0, os.path.abspath('src'))

import substitution
import permutation
from attaque_mcmc import attaque_mcmc_substitution, attaque_mcmc_permutation
from wiki_statistiques import obtenir_texte_reference

def main():
    chemin_stats = os.path.join('data', 'stats_reference.json')
    if not os.path.exists(chemin_stats):
        print(f"Erreur : Le fichier {chemin_stats} est introuvable.")
        return
        
    with open(chemin_stats, 'r', encoding='utf-8') as f:
        fichier_complet = json.load(f)
        stats_reference = fichier_complet.get("digrammes", {})

    # Menu interactif
    print("="*50)
    print("   OUTIL D'ATTAQUE CRYPTOGRAPHIQUE MCMC")
    print("="*50)
    print("1. Attaquer une substitution mono-alphabétique")
    print("2. Attaquer une permutation (transposition par blocs)")
    print("3. Quitter")
    choix = input("\nQue souhaites-tu faire ? (1/2/3) : ")

    if choix in ["1", "2"]:
        texte_complet = obtenir_texte_reference("Chiffre_de_Vigenère")
        if not texte_complet:
            return

        # On prend un échantillon représentatif pour le calcul (optimisation du temps)
        texte_clair = texte_complet[:2500] 
        iterations_str = input("\nCombien d'itérations pour le MCMC ? (Défaut: 15000) : ")
        iterations = int(iterations_str) if iterations_str.isdigit() else 15000

        if choix == "1":
            cle_secrete = substitution.generer_cle()
            cryptogramme = substitution.chiffrer_texte(texte_clair, cle_secrete)
            
            print("\n[+] Création de la cible (Substitution) terminée.")
            print(f"Cryptogramme (aperçu) : {cryptogramme[:80]}...")
            print(f"\nLancement de l'attaque sur {iterations} itérations...")
            
            cle_trouvee, texte_trouve = attaque_mcmc_substitution(cryptogramme, iterations, stats_reference)
            
            print("\n" + "="*50)
            print("--- RÉSULTATS DE L'ALGORITHME ---")
            print(f"Clé déduite       : {cle_trouvee}")
            print(f"Texte déchiffré   : {texte_trouve[:150]}... (tronqué)")
            
            lettres_correctes = sum(1 for a, b in zip(cle_secrete, cle_trouvee) if a == b)
            print(f"\nPrécision de clé  : {lettres_correctes}/26 lettres exactes.")

        elif choix == "2":
            taille_bloc = 10 # Taille standard pour tester
            cle_secrete = permutation.generer_cle(taille_bloc)
            # Utilisation de chiffrer_permutation au lieu de chiffrer_texte pour correspondre à ton fichier
            cryptogramme = permutation.chiffrer_permutation(texte_clair, cle_secrete)
            
            print("\n[+] Création de la cible (Permutation) terminée.")
            print(f"Clé secrète (indices) : {cle_secrete}")
            print(f"Cryptogramme (aperçu) : {cryptogramme[:80]}...")
            print(f"\nLancement de l'attaque sur {iterations} itérations...")
            
            # Appel de l'attaque MCMC pour la permutation
            cle_trouvee, texte_trouve = attaque_mcmc_permutation(cryptogramme, iterations, stats_reference, taille_bloc)
            
            print("\n" + "="*50)
            print("--- RÉSULTATS DE L'ALGORITHME ---")
            print(f"Clé déduite       : {cle_trouvee}")
            print(f"Texte déchiffré   : {texte_trouve[:150]}... (tronqué)")
            
            indices_corrects = sum(1 for a, b in zip(cle_secrete, cle_trouvee) if a == b)
            print(f"\nPrécision de clé  : {indices_corrects}/{taille_bloc} positions exactes.")

    elif choix == "3":
        print("Fermeture du programme.")
    else:
        print("Choix invalide.")

if __name__ == "__main__":
    main()