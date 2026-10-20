"""
Interface en Ligne de Commande (CLI) pour l'outil de Cryptanalyse MCMC.
Permet d'exécuter des attaques par chaînes de Markov (Metropolis-Hastings) directement dans le terminal.
Intègre la prise en charge de textes clairs (pour générer des cibles) et de cryptogrammes fournis.
"""

import math
import sys
import os
import json
import random
import urllib.parse

# Le dossier `src` contient les modules métier du projet. Il est ajouté en tête
# du chemin de recherche afin de garantir que ces modules locaux sont chargés.
sys.path.insert(0, os.path.abspath('src'))

import substitution
import permutation
from attaque_mcmc import attaque_mcmc_substitution, attaque_mcmc_permutation
from wiki_statistiques import (
    obtenir_texte_reference, nettoyer_texte,
    calculer_statistiques, calculer_statistiques_ngrams, sauvegarder_statistiques_json
)

def selectionner_langue() -> str:
    """Scanne dynamiquement l'arborescence 'data/' pour lister les modèles statistiques disponibles."""
    dossier_data = 'data'
    if not os.path.exists(dossier_data):
        print("[ERREUR] Le dossier 'data' est introuvable. Lancez 'wiki_statistiques.py' en premier.")
        return None

    # Chaque sous-dossier représente une langue et contient ses textes ainsi
    # que le fichier de statistiques utilisé par l'attaque.
    langues = sorted([d for d in os.listdir(dossier_data) if os.path.isdir(os.path.join(dossier_data, d))])
    
    if not langues:
        print("[ERREUR] Aucune langue trouvée dans le dossier 'data'.")
        return None
        
    print("\n" + "="*60)
    print("--- SÉLECTION DE LA LANGUE D'ANALYSE ---")
    for i, lang in enumerate(langues, 1):
        print(f"{i}. {lang.upper()}")
        
    while True:
        choix = input(f"Choisissez une langue (1-{len(langues)}) : ").strip()
        if choix.isdigit() and 1 <= int(choix) <= len(langues):
            return langues[int(choix)-1]
        print(f"[ERREUR] Saisie invalide.")

def charger_texte_cible(langue: str) -> str:
    """Sélectionne aléatoirement un texte de référence dans la base locale."""
    dossier_langue = os.path.join('data', langue)
    fichiers = [f for f in os.listdir(dossier_langue) if f.endswith('.txt')]
    
    if not fichiers:
        return None
        
    fichier_choisi = random.choice(fichiers)
    print(f"\n[INFO] Fichier source sélectionné aléatoirement : {fichier_choisi}")
    with open(os.path.join(dossier_langue, fichier_choisi), 'r', encoding='utf-8') as f:
        return f.read()

def choisir_fichier_local(langue: str) -> str:
    """Affiche une liste paginée des fichiers locaux disponibles (par blocs de 10)."""
    dossier_langue = os.path.join('data', langue)
    fichiers = sorted([f for f in os.listdir(dossier_langue) if f.endswith('.txt')])
    
    if not fichiers:
        return None
        
    # La pagination évite d'afficher une liste trop longue dans le terminal.
    page, limite = 0, 10
    total_pages = max(1, (len(fichiers) - 1) // limite + 1)
    
    while True:
        print(f"\n--- FICHIERS DISPONIBLES ({langue.upper()}) - Page {page+1}/{total_pages} ---")
        debut = page * limite
        fichiers_page = fichiers[debut:debut+limite]
        
        for i, fichier in enumerate(fichiers_page, 1):
            print(f"{i}. {fichier}")
            
        instructions = f"Entrez un numéro (1-{len(fichiers_page)}), 'S' (Suivant), 'P' (Précédent), ou 'R' (Retour)"
        choix = input(f"{instructions} : ").strip().upper()
        
        if choix == 'R':
            return None 
        elif choix == 'S' and page < total_pages - 1:
            page += 1
        elif choix == 'P' and page > 0:
            page -= 1
        elif choix.isdigit() and 1 <= int(choix) <= len(fichiers_page):
            fichier_choisi = fichiers_page[int(choix) - 1]
            with open(os.path.join(dossier_langue, fichier_choisi), 'r', encoding='utf-8') as f:
                return f.read()

def demander_texte_manuel() -> str:
    """Permet de coller un texte chiffré directement dans le terminal."""
    print("\nCollez votre texte chiffré ci-dessous (appuyez sur Entrée à vide pour valider) :")
    lignes = []
    while True:
        ligne = input()
        if not ligne:
            break
        lignes.append(ligne)
    return " ".join(lignes).strip()

def demander_fichier_absolu() -> str:
    """Permet de charger un fichier externe via son chemin."""
    chemin = input("\nEntrez le chemin absolu ou relatif de votre fichier (.txt) : ").strip().strip("\"'")
    if os.path.exists(chemin):
        with open(chemin, 'r', encoding='utf-8') as f:
            return f.read()
    print(f"[ERREUR] Le fichier '{chemin}' est introuvable.")
    return None

def choisir_source_texte(langue: str) -> tuple:
    """Retourne (texte, est_nouveau, est_cryptogramme) selon le choix de l'utilisateur."""
    while True:
        print("\n--- SOURCE DE LA CIBLE ---")
        print("1. Texte Clair : Tirer au hasard dans la base locale")
        print("2. Texte Clair : Choisir dans la base locale (Liste)")
        print("3. Texte Clair : Fournir une page Wikipédia")
        print("4. Cryptogramme : Coller le texte chiffré")
        print("5. Cryptogramme : Fournir le chemin d'un fichier .txt")
        choix = input("Votre choix (1-5) : ").strip()
        
        if choix == "1":
            return charger_texte_cible(langue), False, False
        elif choix == "2":
            return choisir_fichier_local(langue), True, False
        elif choix == "3":
            saisie = input("\nEntrez le titre de la page ou l'URL : ").strip()
            if "wikipedia.org/wiki/" in saisie:
                saisie = urllib.parse.unquote(saisie.split("wikipedia.org/wiki/")[-1])
            texte = obtenir_texte_reference(saisie, lang=langue)
            return texte, True, False
        elif choix == "4":
            texte = demander_texte_manuel()
            return texte, False, True
        elif choix == "5":
            texte = demander_fichier_absolu()
            return texte, False, True
        else:
            print("[ERREUR] Veuillez taper un nombre entre 1 et 5.")

def selectionner_ngram() -> int:
    """Définit la profondeur de l'analyse linguistique (Digrammes ou Trigrammes)."""
    print("\n--- NIVEAU D'ANALYSE ---")
    print("1. Digrammes (N=2) : Rapide.")
    print("2. Trigrammes (N=3) : Ultra-précis (Évite les optimums locaux / anagrammes).")
    
    while True:
        choix_ngram = input("Votre choix (1/2) : ").strip()
        if choix_ngram == "1": return 2
        elif choix_ngram == "2": return 3

def main():
    langue = selectionner_langue()
    if not langue: return

    chemin_stats = os.path.join('data', langue, 'stats_reference.json')
    if not os.path.exists(chemin_stats): return
        
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
        
        choix = input("\nVotre choix : ").strip()
        
        if choix == "3": break
            
        elif choix in ["1", "2"]:
            resultat = choisir_source_texte(langue)
            if not resultat or not resultat[0]: continue
            texte_brut, est_nouveau, est_cryptogramme = resultat
            
            # Sécurité anti-pollution : Ne propose d'apprendre que si c'est un texte clair externe
            if est_nouveau and not est_cryptogramme:
                print("\n[?] Ce texte clair n'est pas issu du tirage aléatoire standard.")
                print("Voulez-vous ENREGISTRER ses statistiques dans la matrice d'apprentissage ?")
                print("(⚠️ Répondez NON si le texte n'est pas dans la bonne langue pour éviter de polluer le modèle)")
                rep_save = input("Votre choix (O/N) : ").strip().upper()
                if rep_save == 'O':
                    tp = nettoyer_texte(texte_brut)
                    sauvegarder_statistiques_json(
                        calculer_statistiques(tp), 
                        calculer_statistiques_ngrams(tp, 2), 
                        calculer_statistiques_ngrams(tp, 3), 
                        f"Texte_Manuel_{random.randint(100, 999)}", lang=langue
                    )
                    print("[INFO] Modèle statistique mis à jour avec succès.")
            
            # Nettoyage systématique pour garantir le format mathématique, même sur un cryptogramme
            texte_cible = nettoyer_texte(texte_brut)[:2500] 
            
            n_gram = selectionner_ngram()
            stats_brutes = stats_tri if n_gram == 3 else stats_dig
            
            # Normalisation et Lissage de la courbe
            total_ngrams = max(1, sum(stats_brutes.values()))
            echelle_ref = 10000.0 if n_gram == 3 else 2500.0
            facteur_lissage = 6.0
            
            log_stats_actives = {
                k: math.log(1.0 + (v / total_ngrams) * echelle_ref) / facteur_lissage
                for k, v in stats_brutes.items() if v > 0
            }

            iterations_str = input("\nCombien d'itérations pour le MCMC ? (Défaut: 10000) : ").strip()
            iterations = int(iterations_str) if iterations_str.isdigit() else 10000

            if choix == "1":
                if est_cryptogramme:
                    cryptogramme = texte_cible
                    cle_secrete = "INCONNUE"
                    print("\n[+] Cible chargée directement depuis le cryptogramme fourni.")
                else:
                    cle_secrete = substitution.generer_cle()
                    cryptogramme = substitution.chiffrer_texte(texte_cible, cle_secrete)
                    print("\n[+] Création de la cible (Substitution) terminée.")
                    
                print(f"[>] Lancement de l'attaque MCMC sur {iterations} itérations...")
                top_cles = attaque_mcmc_substitution(cryptogramme, iterations, log_stats_actives, n_gram)
                
                print("\n--- RÉSULTATS (CLÉS LES PLUS VISITÉES APRÈS CHAUFFE) ---")
                for rang, (cle, visites) in enumerate(top_cles[:3], 1):
                    texte_dechiffre = substitution.dechiffrer_texte(cryptogramme, cle)
                    prec_str = "?/26" if cle_secrete == "INCONNUE" else f"{sum(1 for a, b in zip(cle_secrete, cle) if a == b)}/26"
                    print(f"\n[#{rang}] Visites : {visites} fois | Précision absolue : {prec_str}")
                    print(f"Clé : {cle}\nDécodé : {texte_dechiffre[:120]}...")

            elif choix == "2":
                taille_bloc_str = input("\nTaille du bloc pour la permutation (Défaut: 10) : ").strip()
                taille_bloc = int(taille_bloc_str) if taille_bloc_str.isdigit() else 10
                
                if est_cryptogramme:
                    cryptogramme = texte_cible
                    cle_secrete = "INCONNUE"
                    print(f"\n[+] Cible chargée depuis le cryptogramme fourni (Blocs de {taille_bloc}).")
                else:
                    cle_secrete = permutation.generer_cle(taille_bloc)
                    cryptogramme = permutation.chiffrer_permutation(texte_cible, cle_secrete)
                    print(f"\n[+] Création de la cible (Permutation, Blocs de {taille_bloc}) terminée.")
                    
                print(f"[>] Lancement de l'attaque MCMC sur {iterations} itérations...")
                top_cles = attaque_mcmc_permutation(cryptogramme, iterations, log_stats_actives, taille_bloc, n_gram)
                
                print("\n--- RÉSULTATS (CLÉS LES PLUS VISITÉES APRÈS CHAUFFE) ---")
                for rang, (cle, visites) in enumerate(top_cles[:3], 1):
                    texte_dechiffre = permutation.dechiffrer_permutation(cryptogramme, cle)
                    prec_str = f"?/{taille_bloc}" if cle_secrete == "INCONNUE" else f"{sum(1 for a, b in zip(cle_secrete, cle) if a == b)}/{taille_bloc}"
                    print(f"\n[#{rang}] Visites : {visites} fois | Précision absolue : {prec_str}")
                    print(f"Clé : {cle}\nDécodé : {texte_dechiffre[:200]}...")

if __name__ == "__main__":
    main()