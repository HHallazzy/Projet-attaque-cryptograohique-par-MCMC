"""
Interface en Ligne de Commande (CLI) pour l'outil de Cryptanalyse MCMC.
Permet d'exécuter des attaques par chaînes de Markov (Metropolis-Hastings) directement dans le terminal.
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
# Importation de tous les outils statistiques pour permettre la sauvegarde optionnelle
# Ces fonctions servent à récupérer un texte externe et, si l'utilisateur
# l'autorise, à mettre à jour les modèles statistiques de la langue choisie.
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
    # `page` est indexée à partir de zéro, tandis que l'affichage commence à 1.
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
        
        if choix == 'R': return None
        elif choix == 'S' and page < total_pages - 1: page += 1
        elif choix == 'P' and page > 0: page -= 1
        elif choix.isdigit() and 1 <= int(choix) <= len(fichiers_page):
            fichier_choisi = fichiers_page[int(choix) - 1]
            with open(os.path.join(dossier_langue, fichier_choisi), 'r', encoding='utf-8') as f:
                return f.read()

def choisir_source_texte(langue: str) -> tuple:
    """Retourne le texte cible et un booléen indiquant s'il provient d'une source externe (pour sauvegarde stats)."""
    while True:
        print("\n--- SOURCE DU TEXTE À ATTAQUER ---")
        print("1. Tirer un texte au hasard dans la base de données locale")
        print("2. Fournir une page Wikipédia précise (Titre ou URL complète)")
        print("3. Choisir un texte spécifique dans la base locale (Liste paginée)")
        
        choix = input("Votre choix (1/2/3) : ").strip()
        
        if choix == "1":
            return charger_texte_cible(langue), False
            
        elif choix == "2":
            saisie = input("\nEntrez le titre de la page ou l'URL : ").strip()
            if "wikipedia.org/wiki/" in saisie:
                # Une URL Wikipédia encode parfois les caractères accentués.
                # On extrait uniquement le titre puis on le décode avant l'appel
                # réseau afin que le module de récupération reçoive un titre lisible.
                saisie = urllib.parse.unquote(saisie.split("wikipedia.org/wiki/")[-1])

            texte = obtenir_texte_reference(saisie, lang=langue)
            # Une source externe peut enrichir le modèle, mais uniquement après
            # confirmation explicite de l'utilisateur dans la boucle principale.
            return texte, True
            
        elif choix == "3":
            return choisir_fichier_local(langue), True
            
        print("[ERREUR] Veuillez taper '1', '2' ou '3'.")

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
            texte_complet, est_nouveau = choisir_source_texte(langue)
            if not texte_complet: continue
            
            # Un texte choisi manuellement ou téléchargé peut ne pas appartenir
            # à la langue sélectionnée. La confirmation évite donc d'ajouter
            # des fréquences incohérentes au modèle de référence.
            if est_nouveau:
                print("\n[?] Ce texte n'est pas issu du tirage aléatoire standard.")
                print("Voulez-vous ENREGISTRER ses statistiques dans la matrice d'apprentissage ?")
                print("(⚠️ Répondez NON si le texte n'est pas dans la bonne langue pour éviter de polluer le modèle)")
                rep_save = input("Votre choix (O/N) : ").strip().upper()
                if rep_save == 'O':
                    tp = nettoyer_texte(texte_complet)
                    sauvegarder_statistiques_json(
                        calculer_statistiques(tp), 
                        calculer_statistiques_ngrams(tp, 2), 
                        calculer_statistiques_ngrams(tp, 3), 
                        f"Texte_Manuel_{random.randint(100, 999)}", lang=langue
                    )
                    print("[INFO] Modèle statistique mis à jour avec succès.")
                
            # La limite réduit le coût de l'attaque tout en conservant assez de
            # contexte linguistique pour distinguer les clés candidates.
            texte_clair = texte_complet[:2500]
            n_gram = selectionner_ngram()
            stats_brutes = stats_tri if n_gram == 3 else stats_dig
            
            # Les fréquences sont normalisées par le nombre total de n-grammes.
            # La valeur minimale 1 empêche une division par zéro si le fichier
            # de statistiques est vide ou incomplet.
            total_ngrams = max(1, sum(stats_brutes.values()))
            # Les trigrammes sont plus nombreux et plus discriminants : leur
            # échelle de référence est donc plus élevée que celle des digrammes.
            echelle_ref = 10000.0 if n_gram == 3 else 2500.0
            facteur_lissage = 6.0
            
            # Le logarithme transforme les produits de probabilités en sommes,
            # ce qui limite les sous-dépassements numériques. Le lissage `1 +`
            # garantit en outre une valeur définie pour chaque n-gramme observé.
            log_stats_actives = {
                k: math.log(1.0 + (v / total_ngrams) * echelle_ref) / facteur_lissage 
                for k, v in stats_brutes.items() if v > 0
            }

            # Une chaîne plus longue explore davantage de clés, mais augmente le
            # temps de calcul. 10 000 itérations constituent le compromis proposé
            # par défaut pour une exécution interactive.
            iterations_str = input("\nCombien d'itérations pour le MCMC ? (Défaut: 10000) : ").strip()
            iterations = int(iterations_str) if iterations_str.isdigit() else 10000

            if choix == "1":
                # Le cryptogramme est généré à partir d'une clé connue uniquement
                # pour permettre de mesurer la qualité de l'attaque simulée.
                cle_secrete = substitution.generer_cle()
                cryptogramme = substitution.chiffrer_texte(texte_clair, cle_secrete)
                print(f"\n[>] Lancement de l'attaque MCMC sur {iterations} itérations...")
                top_cles = attaque_mcmc_substitution(cryptogramme, iterations, log_stats_actives, n_gram)
                
                print("\n--- RÉSULTATS (CLÉS LES PLUS VISITÉES APRÈS CHAUFFE) ---")
                for rang, (cle, visites) in enumerate(top_cles[:3], 1):
                    texte_dechiffre = substitution.dechiffrer_texte(cryptogramme, cle)
                    # La comparaison position par position mesure le nombre de
                    # lettres correctement retrouvées par la chaîne de Markov.
                    print(f"\n[#{rang}] Visites : {visites} fois | Précision : {sum(1 for a, b in zip(cle_secrete, cle) if a == b)}/26")
                    print(f"Clé : {cle}\nTexte : {texte_dechiffre[:120]}...")

            elif choix == "2":
                # La permutation travaille sur des blocs de taille fixe ; chaque
                # clé est donc une permutation des positions de ce bloc.
                taille_bloc = 10
                cle_secrete = permutation.generer_cle(taille_bloc)
                cryptogramme = permutation.chiffrer_permutation(texte_clair, cle_secrete)
                print(f"\n[>] Lancement de l'attaque MCMC sur {iterations} itérations...")
                top_cles = attaque_mcmc_permutation(cryptogramme, iterations, log_stats_actives, taille_bloc, n_gram)
                
                print("\n--- RÉSULTATS (CLÉS LES PLUS VISITÉES APRÈS CHAUFFE) ---")
                for rang, (cle, visites) in enumerate(top_cles[:3], 1):
                    texte_dechiffre = permutation.dechiffrer_permutation(cryptogramme, cle)
                    # Pour une permutation, la précision compare les positions
                    # du bloc et non les 26 lettres de l'alphabet.
                    print(f"\n[#{rang}] Visites : {visites} fois | Précision : {sum(1 for a, b in zip(cle_secrete, cle) if a == b)}/{taille_bloc}")
                    print(f"Clé : {cle}\nTexte : {texte_dechiffre[:120]}...")

if __name__ == "__main__":
    main()