import sys
import os
import json
import random
import urllib.parse

# Permet d'importer les modules depuis le dossier src/
sys.path.insert(0, os.path.abspath('src'))

import substitution
import permutation
from attaque_mcmc import attaque_mcmc_substitution, attaque_mcmc_permutation
from wiki_statistiques import obtenir_texte_reference

def selectionner_langue() -> str:
    """
    Scanne le dossier 'data' pour trouver les langues disponibles.
    Force l'utilisateur à faire un choix valide via une boucle de sécurité.
    """
    dossier_data = 'data'
    if not os.path.exists(dossier_data):
        print("[ERREUR] Le dossier 'data' est introuvable. Lancez 'wiki_statistiques.py' en premier.")
        return None
        
    # Liste uniquement les sous-dossiers (ex: fr, en, es)
    langues = [d for d in os.listdir(dossier_data) if os.path.isdir(os.path.join(dossier_data, d))]
    
    if not langues:
        print("[ERREUR] Aucune langue trouvée dans le dossier 'data'.")
        return None
        
    print("\n" + "="*60)
    print("--- SÉLECTION DE LA LANGUE D'ANALYSE ---")
    print("Les statistiques de cette langue seront utilisées pour le décryptage.")
    for i, lang in enumerate(langues, 1):
        print(f"{i}. {lang.upper()}")
        
    # Boucle de validation de saisie (empêche les plantages si l'utilisateur tape des lettres)
    while True:
        choix = input(f"Choisissez une langue (1-{len(langues)}) : ").strip()
        if choix.isdigit() and 1 <= int(choix) <= len(langues):
            return langues[int(choix)-1]
        print(f"[ERREUR] Saisie invalide. Veuillez entrer un nombre entre 1 et {len(langues)}.")

def charger_texte_cible(langue: str) -> str:
    """
    Pioche un fichier texte au hasard dans le dossier de la langue sélectionnée.
    Sert de choix principal (option 1) ou de solution de secours (échec option 2).
    """
    dossier_langue = os.path.join('data', langue)
    fichiers = [f for f in os.listdir(dossier_langue) if f.endswith('.txt')]
    
    if not fichiers:
        print(f"[ERREUR] Aucun fichier texte trouvé pour la langue {langue.upper()}.")
        return None
        
    fichier_choisi = random.choice(fichiers)
    print(f"\n[INFO] Fichier source sélectionné aléatoirement : {fichier_choisi}")
    
    with open(os.path.join(dossier_langue, fichier_choisi), 'r', encoding='utf-8') as f:
        return f.read()

def choisir_source_texte(langue: str) -> str:
    """
    Demande à l'utilisateur l'origine du texte à attaquer.
    Intègre une boucle de sécurité pour forcer un choix '1' ou '2'.
    """
    print("\n--- SOURCE DU TEXTE À ATTAQUER ---")
    print("1. Tirer un texte au hasard dans la base de données locale")
    print("2. Fournir une page Wikipédia précise (Titre ou URL complète)")
    
    # Validation stricte du choix utilisateur
    while True:
        choix = input("Votre choix (1/2) : ").strip()
        if choix in ["1", "2"]:
            break
        print("[ERREUR] Veuillez taper '1' ou '2'.")
    
    if choix == "2":
        saisie = input("\nEntrez le titre de la page ou l'URL : ").strip()
        
        # Astuce technique : Si le prof entre une URL complète, on extrait juste le titre à la fin
        if "wikipedia.org/wiki/" in saisie:
            saisie = urllib.parse.unquote(saisie.split("wikipedia.org/wiki/")[-1])
            
        print(f"\n[INFO] Préparation de la page Wikipédia : {saisie}")
        texte = obtenir_texte_reference(saisie, lang=langue)
        
        if texte:
            return texte
        print("[ATTENTION] Impossible de télécharger la page. Bascule sur un texte aléatoire local...")
        
    # Par défaut (choix 1) ou si le téléchargement a échoué (choix 2)
    return charger_texte_cible(langue)

def selectionner_ngram() -> int:
    """
    Demande le niveau de précision statistique (Digrammes ou Trigrammes).
    Garantit une saisie valide via une boucle infinie.
    """
    print("\n--- NIVEAU D'ANALYSE (RÉSOLUTION DES ANAGRAMMES) ---")
    print("1. Digrammes (Blocs de 2 lettres) : Rapide, adapté aux textes très longs.")
    print("2. Trigrammes (Blocs de 3 lettres) : Plus lourd, mais ultra-précis (évite les maximums locaux).")
    
    while True:
        choix_ngram = input("Votre choix (1/2) : ").strip()
        if choix_ngram == "1":
            return 2
        elif choix_ngram == "2":
            return 3
        print("[ERREUR] Veuillez taper '1' ou '2'.")

def main():
    # ==========================================
    # 1. INITIALISATION DE L'ENVIRONNEMENT
    # ==========================================
    langue = selectionner_langue()
    if not langue:
        return # Arrêt propre si aucune langue n'est configurée

    chemin_stats = os.path.join('data', langue, 'stats_reference.json')
    if not os.path.exists(chemin_stats):
        print(f"[ERREUR] Le fichier de statistiques {chemin_stats} est introuvable.")
        return
        
    # Chargement des matrices de probabilités en mémoire
    with open(chemin_stats, 'r', encoding='utf-8') as f:
        fichier_complet = json.load(f)
        stats_dig = fichier_complet.get("digrammes", {})
        stats_tri = fichier_complet.get("trigrammes", {})

    # ==========================================
    # 2. MENU PRINCIPAL DE L'APPLICATION
    # ==========================================
    while True: # La boucle permet de relancer des attaques sans relancer le script
        print("\n" + "="*60)
        print(f"   OUTIL D'ATTAQUE MCMC - Mode : {langue.upper()}")
        print("="*60)
        print("1. Attaquer une substitution mono-alphabétique")
        print("2. Attaquer une permutation (transposition par blocs)")
        print("3. Quitter le programme")
        
        choix = input("\nQue souhaites-tu faire ? (1/2/3) : ").strip()
        
        if choix == "3":
            print("\n[INFO] Fermeture du programme. À bientôt !")
            break
            
        elif choix in ["1", "2"]:
            # --- 2.1 Configuration de l'attaque ---
            texte_complet = choisir_source_texte(langue)
            if not texte_complet:
                print("[ERREUR] Impossible de charger un texte de référence. Retour au menu.")
                continue
                
            # Limitation à 2500 caractères pour garder des temps de calcul décents en MCMC
            texte_clair = texte_complet[:2500] 
            
            n_gram = selectionner_ngram()
            stats_actives = stats_tri if n_gram == 3 else stats_dig

            iterations_str = input("\nCombien d'itérations pour le MCMC ? (Défaut: 15000) : ").strip()
            iterations = int(iterations_str) if iterations_str.isdigit() else 15000
            if not iterations_str.isdigit():
                print(f"[INFO] Valeur par défaut appliquée : {iterations} itérations.")

            # ==========================================
            # 3. EXÉCUTION DE L'ATTAQUE CIBLÉE
            # ==========================================
            if choix == "1":
                # --- ATTAQUE PAR SUBSTITUTION ---
                cle_secrete = substitution.generer_cle()
                cryptogramme = substitution.chiffrer_texte(texte_clair, cle_secrete)
                
                print("\n[+] Création de la cible (Substitution) terminée.")
                print(f"[>] Lancement de l'attaque MCMC (N={n_gram}) sur {iterations} itérations...")
                print("[>] Note : Les 15 premiers % (Période de chauffe) seront ignorés des statistiques.")
                
                # Appel du module d'échantillonnage de Metropolis-Hastings
                top_cles = attaque_mcmc_substitution(cryptogramme, iterations, stats_actives, n_gram)
                
                # --- AFFICHAGE DES RÉSULTATS ---
                print("\n" + "="*60)
                print("--- RÉSULTATS (CLÉS LES PLUS VISITÉES APRÈS CHAUFFE) ---")
                
                for rang, (cle, visites) in enumerate(top_cles[:3], 1):
                    texte_dechiffre = substitution.dechiffrer_texte(cryptogramme, cle)
                    lettres_correctes = sum(1 for a, b in zip(cle_secrete, cle) if a == b)
                    print(f"\n[#{rang}] Clé proposée : {cle}")
                    print(f"      Nombre de visites : {visites} fois")
                    print(f"      Précision absolue : {lettres_correctes}/26 exactes")
                    print(f"      Texte déchiffré   : {texte_dechiffre[:120]}...")

            elif choix == "2":
                # --- ATTAQUE PAR PERMUTATION ---
                taille_bloc = 10 # Standard de l'exercice
                cle_secrete = permutation.generer_cle(taille_bloc)
                cryptogramme = permutation.chiffrer_permutation(texte_clair, cle_secrete)
                
                print("\n[+] Création de la cible (Permutation) terminée.")
                print(f"[>] Lancement de l'attaque MCMC (N={n_gram}) sur {iterations} itérations...")
                print("[>] Note : Les 15 premiers % (Période de chauffe) seront ignorés des statistiques.")
                
                # Appel du module d'échantillonnage de Metropolis-Hastings
                top_cles = attaque_mcmc_permutation(cryptogramme, iterations, stats_actives, taille_bloc, n_gram)
                
                # --- AFFICHAGE DES RÉSULTATS ---
                print("\n" + "="*60)
                print("--- RÉSULTATS (CLÉS LES PLUS VISITÉES APRÈS CHAUFFE) ---")
                
                for rang, (cle, visites) in enumerate(top_cles[:3], 1):
                    texte_dechiffre = permutation.dechiffrer_permutation(cryptogramme, cle)
                    indices_corrects = sum(1 for a, b in zip(cle_secrete, cle) if a == b)
                    print(f"\n[#{rang}] Clé proposée (Indices) : {cle}")
                    print(f"      Nombre de visites : {visites} fois")
                    print(f"      Précision absolue : {indices_corrects}/{taille_bloc} positions exactes")
                    print(f"      Texte déchiffré   : {texte_dechiffre[:120]}...")
        
        else:
            print("[ERREUR] Choix invalide. Veuillez saisir 1, 2 ou 3.")

if __name__ == "__main__":
    main()