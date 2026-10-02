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
    """Scanne le dossier 'data' pour trouver les langues disponibles."""
    dossier_data = 'data'
    if not os.path.exists(dossier_data):
        print("[ERREUR] Le dossier 'data' est introuvable. Lancez 'wiki_statistiques.py' en premier.")
        return None
        
    langues = sorted([d for d in os.listdir(dossier_data) if os.path.isdir(os.path.join(dossier_data, d))])
    
    if not langues:
        print("[ERREUR] Aucune langue trouvée dans le dossier 'data'.")
        return None
        
    print("\n" + "="*60)
    print("--- SÉLECTION DE LA LANGUE D'ANALYSE ---")
    print("Les statistiques de cette langue seront utilisées pour le décryptage.")
    for i, lang in enumerate(langues, 1):
        print(f"{i}. {lang.upper()}")
        
    while True:
        choix = input(f"Choisissez une langue (1-{len(langues)}) : ").strip()
        if choix.isdigit() and 1 <= int(choix) <= len(langues):
            return langues[int(choix)-1]
        print(f"[ERREUR] Saisie invalide. Veuillez entrer un nombre entre 1 et {len(langues)}.")

def charger_texte_cible(langue: str) -> str:
    """Pioche un fichier texte au hasard dans le dossier de la langue sélectionnée."""
    dossier_langue = os.path.join('data', langue)
    fichiers = [f for f in os.listdir(dossier_langue) if f.endswith('.txt')]
    
    if not fichiers:
        print(f"[ERREUR] Aucun fichier texte trouvé pour la langue {langue.upper()}.")
        return None
        
    fichier_choisi = random.choice(fichiers)
    print(f"\n[INFO] Fichier source sélectionné aléatoirement : {fichier_choisi}")
    
    with open(os.path.join(dossier_langue, fichier_choisi), 'r', encoding='utf-8') as f:
        return f.read()

def choisir_fichier_local(langue: str) -> str:
    """
    Affiche une liste paginée (10 par page) des fichiers locaux disponibles 
    pour éviter de surcharger la console s'il y a des centaines de textes.
    """
    dossier_langue = os.path.join('data', langue)
    fichiers = sorted([f for f in os.listdir(dossier_langue) if f.endswith('.txt')])
    
    if not fichiers:
        print(f"[ERREUR] Aucun fichier texte trouvé pour la langue {langue.upper()}.")
        return None
        
    page = 0
    limite = 10
    total_pages = max(1, (len(fichiers) - 1) // limite + 1)
    
    while True:
        print(f"\n--- FICHIERS DISPONIBLES ({langue.upper()}) - Page {page+1}/{total_pages} ---")
        debut = page * limite
        fichiers_page = fichiers[debut:debut+limite]
        
        for i, fichier in enumerate(fichiers_page, 1):
            print(f"{i}. {fichier}")
            
        print("-" * 60)
        instructions = f"Entrez un numéro (1-{len(fichiers_page)})"
        if total_pages > 1:
            if page > 0: instructions += ", 'P' (Précédent)"
            if page < total_pages - 1: instructions += ", 'S' (Suivant)"
        instructions += ", ou 'R' (Retour au menu)"
        
        choix = input(f"{instructions} : ").strip().upper()
        
        if choix == 'R':
            return None # Retourne au menu de sélection de source
        elif choix == 'S' and page < total_pages - 1:
            page += 1
        elif choix == 'P' and page > 0:
            page -= 1
        elif choix.isdigit():
            idx = int(choix)
            if 1 <= idx <= len(fichiers_page):
                fichier_choisi = fichiers_page[idx - 1]
                print(f"\n[INFO] Fichier source sélectionné : {fichier_choisi}")
                with open(os.path.join(dossier_langue, fichier_choisi), 'r', encoding='utf-8') as f:
                    return f.read()
        else:
            print("[ERREUR] Saisie invalide.")

def choisir_source_texte(langue: str) -> str:
    """Demande à l'utilisateur l'origine du texte à attaquer avec la nouvelle option locale."""
    while True:
        print("\n--- SOURCE DU TEXTE À ATTAQUER ---")
        print("1. Tirer un texte au hasard dans la base de données locale")
        print("2. Fournir une page Wikipédia précise (Titre ou URL complète)")
        print("3. Choisir un texte spécifique dans la base locale (Liste)")
        
        choix = input("Votre choix (1/2/3) : ").strip()
        
        if choix == "1":
            return charger_texte_cible(langue)
            
        elif choix == "2":
            saisie = input("\nEntrez le titre de la page ou l'URL : ").strip()
            if "wikipedia.org/wiki/" in saisie:
                saisie = urllib.parse.unquote(saisie.split("wikipedia.org/wiki/")[-1])
                
            print(f"\n[INFO] Préparation de la page Wikipédia : {saisie}")
            texte = obtenir_texte_reference(saisie, lang=langue)
            
            if texte:
                return texte
            print("[ATTENTION] Impossible de télécharger. Bascule sur un texte aléatoire...")
            return charger_texte_cible(langue)
            
        elif choix == "3":
            texte = choisir_fichier_local(langue)
            if texte:
                return texte
            # Si choisir_fichier_local retourne None (l'utilisateur a tapé 'R'), 
            # la boucle while recommence et réaffiche le menu de source.
            
        else:
            print("[ERREUR] Veuillez taper '1', '2' ou '3'.")

def selectionner_ngram() -> int:
    """Demande le niveau de précision statistique (Digrammes ou Trigrammes)."""
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
    langue = selectionner_langue()
    if not langue:
        return

    chemin_stats = os.path.join('data', langue, 'stats_reference.json')
    if not os.path.exists(chemin_stats):
        print(f"[ERREUR] Le fichier de statistiques {chemin_stats} est introuvable.")
        return
        
    with open(chemin_stats, 'r', encoding='utf-8') as f:
        fichier_complet = json.load(f)
        stats_dig = fichier_complet.get("digrammes", {})
        stats_tri = fichier_complet.get("trigrammes", {})

    while True:
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
            texte_complet = choisir_source_texte(langue)
            if not texte_complet:
                print("[ERREUR] Impossible de charger un texte de référence. Retour au menu.")
                continue
                
            texte_clair = texte_complet[:2500] 
            n_gram = selectionner_ngram()
            stats_actives = stats_tri if n_gram == 3 else stats_dig

            iterations_str = input("\nCombien d'itérations pour le MCMC ? (Défaut: 15000) : ").strip()
            iterations = int(iterations_str) if iterations_str.isdigit() else 15000
            if not iterations_str.isdigit():
                print(f"[INFO] Valeur par défaut appliquée : {iterations} itérations.")

            if choix == "1":
                cle_secrete = substitution.generer_cle()
                cryptogramme = substitution.chiffrer_texte(texte_clair, cle_secrete)
                
                print("\n[+] Création de la cible (Substitution) terminée.")
                print(f"[>] Lancement de l'attaque MCMC (N={n_gram}) sur {iterations} itérations...")
                print("[>] Note : Les 15 premiers % (Période de chauffe) seront ignorés des statistiques.")
                
                top_cles = attaque_mcmc_substitution(cryptogramme, iterations, stats_actives, n_gram)
                
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
                taille_bloc = 10
                cle_secrete = permutation.generer_cle(taille_bloc)
                cryptogramme = permutation.chiffrer_permutation(texte_clair, cle_secrete)
                
                print("\n[+] Création de la cible (Permutation) terminée.")
                print(f"[>] Lancement de l'attaque MCMC (N={n_gram}) sur {iterations} itérations...")
                print("[>] Note : Les 15 premiers % (Période de chauffe) seront ignorés des statistiques.")
                
                top_cles = attaque_mcmc_permutation(cryptogramme, iterations, stats_actives, taille_bloc, n_gram)
                
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