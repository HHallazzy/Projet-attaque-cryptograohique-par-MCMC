import sys
import os
import json
import random
import urllib.parse

sys.path.insert(0, os.path.abspath('src'))

import substitution
import permutation
from attaque_mcmc import attaque_mcmc_substitution, attaque_mcmc_permutation
from wiki_statistiques import obtenir_texte_reference

def selectionner_langue() -> str:
    """Scanne le dossier data et demande à l'utilisateur de choisir une langue."""
    dossier_data = 'data'
    if not os.path.exists(dossier_data):
        return None
        
    # Liste uniquement les sous-dossiers (fr, en, es...)
    langues = [d for d in os.listdir(dossier_data) if os.path.isdir(os.path.join(dossier_data, d))]
    
    if not langues:
        return None
        
    print("\n" + "="*50)
    print("--- SÉLECTION DE LA LANGUE ---")
    for i, lang in enumerate(langues, 1):
        print(f"{i}. {lang.upper()}")
        
    while True:
        choix = input(f"Choisissez une langue (1-{len(langues)}) : ")
        if choix.isdigit() and 1 <= int(choix) <= len(langues):
            return langues[int(choix)-1]
        print("Choix invalide.")

def charger_texte_cible(langue: str) -> str:
    """Prend un fichier texte au hasard dans le dossier de la langue pour faire la cible."""
    dossier_langue = os.path.join('data', langue)
    fichiers = [f for f in os.listdir(dossier_langue) if f.endswith('.txt')]
    
    if not fichiers:
        return None
        
    fichier_choisi = random.choice(fichiers)
    print(f"[INFO] Fichier source utilisé (Aléatoire) : {fichier_choisi}")
    
    with open(os.path.join(dossier_langue, fichier_choisi), 'r', encoding='utf-8') as f:
        return f.read()

def choisir_source_texte(langue: str) -> str:
    """Demande à l'utilisateur s'il veut un texte aléatoire ou une page précise."""
    print("\n--- SOURCE DU TEXTE À ATTAQUER ---")
    print("1. Tirer un texte au hasard dans la base de données locale")
    print("2. Fournir une page Wikipédia spécifique (Titre ou URL)")
    choix = input("Votre choix (1/2) : ")
    
    if choix == "2":
        saisie = input("\nEntrez le titre de la page ou l'URL complète : ").strip()
        
        # Astuce : Extraction automatique si le prof colle une URL complète
        if "wikipedia.org/wiki/" in saisie:
            saisie = saisie.split("wikipedia.org/wiki/")[-1]
            saisie = urllib.parse.unquote(saisie) # Transforme les %C3%A9 en 'é'
            
        print(f"\n[INFO] Téléchargement et préparation de la page : {saisie}")
        texte = obtenir_texte_reference(saisie, lang=langue)
        
        if texte:
            return texte
        print("[ATTENTION] Impossible de récupérer cette page. Bascule sur un texte aléatoire local.")
        
    # Choix 1 ou solution de repli en cas d'erreur de téléchargement
    return charger_texte_cible(langue)

def main():
    langue = selectionner_langue()
    if not langue:
        print("Erreur : Aucune donnée de langue trouvée. Lancez src/wiki_statistiques.py d'abord.")
        return

    chemin_stats = os.path.join('data', langue, 'stats_reference.json')
    if not os.path.exists(chemin_stats):
        print(f"Erreur : Le fichier {chemin_stats} est introuvable.")
        return
        
    with open(chemin_stats, 'r', encoding='utf-8') as f:
        fichier_complet = json.load(f)
        stats_reference = fichier_complet.get("digrammes", {})

    print("\n" + "="*50)
    print(f"   OUTIL D'ATTAQUE MCMC - Mode : {langue.upper()}")
    print("="*50)
    print("1. Attaquer une substitution mono-alphabétique")
    print("2. Attaquer une permutation (transposition par blocs)")
    print("3. Quitter")
    choix = input("\nQue souhaites-tu faire ? (1/2/3) : ")

    if choix in ["1", "2"]:
        # Appel de notre nouvelle fonction de sélection de source
        texte_complet = choisir_source_texte(langue)
        if not texte_complet:
            print("Erreur : Aucun texte de référence n'a pu être chargé.")
            return

        texte_clair = texte_complet[:2500] 
        iterations_str = input("\nCombien d'itérations pour le MCMC ? (Défaut: 15000) : ")
        iterations = int(iterations_str) if iterations_str.isdigit() else 15000

        if choix == "1":
            cle_secrete = substitution.generer_cle()
            cryptogramme = substitution.chiffrer_texte(texte_clair, cle_secrete)
            
            print("\n[+] Création de la cible (Substitution) terminée.")
            print(f"Clé secrète cible     : {cle_secrete}")
            print(f"Cryptogramme (aperçu) : {cryptogramme[:80]}...")
            print(f"\nLancement de l'attaque sur {iterations} itérations (Burn-in de 15%)...")
            
            top_cles = attaque_mcmc_substitution(cryptogramme, iterations, stats_reference)
            
            print("\n" + "="*50)
            print("--- RÉSULTATS (CLÉS LES PLUS VISITÉES - 3 MAX SELON CONVERGENCE) ---")
            
            for rang, (cle, visites) in enumerate(top_cles[:3], 1):
                texte_dechiffre = substitution.dechiffrer_texte(cryptogramme, cle)
                lettres_correctes = sum(1 for a, b in zip(cle_secrete, cle) if a == b)
                print(f"\n[#{rang}] Clé : {cle} (Visitée {visites} fois)")
                print(f"      Précision : {lettres_correctes}/26 exactes")
                print(f"      Texte     : {texte_dechiffre[:120]}...")

        elif choix == "2":
            taille_bloc = 10
            cle_secrete = permutation.generer_cle(taille_bloc)
            cryptogramme = permutation.chiffrer_permutation(texte_clair, cle_secrete)
            
            print("\n[+] Création de la cible (Permutation) terminée.")
            print(f"Clé secrète (indices) : {cle_secrete}")
            print(f"Cryptogramme (aperçu) : {cryptogramme[:80]}...")
            print(f"\nLancement de l'attaque sur {iterations} itérations (Burn-in de 15%)...")
            
            top_cles = attaque_mcmc_permutation(cryptogramme, iterations, stats_reference, taille_bloc)
            
            print("\n" + "="*50)
            print("--- RÉSULTATS (CLÉS LES PLUS VISITÉES - 3 MAX SELON CONVERGENCE) ---")
            
            for rang, (cle, visites) in enumerate(top_cles[:3], 1):
                texte_dechiffre = permutation.dechiffrer_permutation(cryptogramme, cle)
                indices_corrects = sum(1 for a, b in zip(cle_secrete, cle) if a == b)
                print(f"\n[#{rang}] Clé : {cle} (Visitée {visites} fois)")
                print(f"      Précision : {indices_corrects}/{taille_bloc} exactes")
                print(f"      Texte     : {texte_dechiffre[:120]}...")

    elif choix == "3":
        print("Fermeture du programme.")
    else:
        print("Choix invalide.")

if __name__ == "__main__":
    main()