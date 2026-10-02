"""
Module d'Ingestion de Données Personnalisées[cite: 6].
Permet d'étendre la base d'entraînement de l'algorithme MCMC avec des textes 
spécifiques (fichiers locaux ou saisie manuelle) pour générer des matrices 
de probabilités sur mesure, indépendantes de Wikipédia.
"""

import os
import sys

# Réutilisation des fonctions métier du module principal pour garantir
# la cohérence du traitement mathématique et de la normalisation[cite: 6].
from wiki_statistiques import (
    nettoyer_texte, 
    calculer_statistiques, 
    calculer_statistiques_ngrams, 
    sauvegarder_statistiques_json
)

def generer_statistiques_sur_mesure():
    """
    Interface en ligne de commande pour la création de modèles statistiques personnalisés.
    Prend en charge l'ingestion de fichiers bruts, leur normalisation vers l'alphabet 
    cryptographique (27 caractères), et le calcul des matrices de probabilités N-grammes[cite: 6].
    """
    print("="*60)
    print("   CRÉATION D'UNE MATRICE DE STATISTIQUES SUR MESURE")
    print("="*60)
    print("1. Saisir ou coller un texte (idéal pour des textes courts)")
    print("2. Fournir le chemin d'un fichier .txt local (Recommandé)")
    
    choix = input("\nVotre choix (1/2) : ").strip()
    
    texte_brut = ""
    titre_source = "Texte_Personnalise"

    if choix == "1":
        # Mode interactif pour des tests rapides (ex: copier/coller un paragraphe)[cite: 6]
        print("\nCollez votre texte ci-dessous (appuyez sur Entrée pour valider) :")
        texte_brut = input("> ")
        titre_source = input("Donnez un nom court à cette source (ex: Rap, Victor_Hugo, Code) : ").strip()
        
    elif choix == "2":
        # Mode fichier : Le double strip() gère automatiquement les guillemets ajoutés 
        # par Windows lors d'un glisser-déposer de fichier dans le terminal[cite: 6].
        chemin_fichier = input("\nEntrez le chemin absolu ou relatif de votre fichier (.txt) : ").strip().strip("\"'")
        
        if not os.path.exists(chemin_fichier):
            print(f"[ERREUR] Le fichier '{chemin_fichier}' est introuvable.")
            return
            
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            texte_brut = f.read()
            
        # Extraction du nom du fichier pour nommer la source dans la base de données[cite: 6]
        titre_source = os.path.basename(chemin_fichier).replace(".txt", "")
        
    else:
        print("[ERREUR] Choix invalide.")
        return

    if not texte_brut.strip():
        print("[ERREUR] Le texte fourni est vide.")
        return

    print(f"\n[INFO] Traitement de '{titre_source}' ({len(texte_brut)} caractères)...")
    
    # 1. Normalisation : Conversion du texte brut vers l'espace cryptographique strict (A-Z + Espace)[cite: 6]
    texte_propre = nettoyer_texte(texte_brut)
    
    # 2. Archivage du texte cible : Sauvegarde dans un dossier dédié ('autressources')
    # Permettra à l'outil principal (main.py / interface_complete.py) de chiffrer ce texte directement[cite: 6].
    dossier_cible = os.path.join("data", "autressources")
    os.makedirs(dossier_cible, exist_ok=True)
    chemin_texte_propre = os.path.join(dossier_cible, f"{titre_source}.txt")
    
    with open(chemin_texte_propre, 'w', encoding='utf-8') as f:
        f.write(texte_propre)
    print(f"[INFO] Texte formaté (alphabet de 27 caractères) sauvegardé dans : {chemin_texte_propre}")

    # 3. Évaluation statistique : Génération des vecteurs de probabilités (1D, 2D, 3D)[cite: 6]
    print("[INFO] Calcul de la matrice de probabilités...")
    stats = calculer_statistiques(texte_propre)
    stats_dig = calculer_statistiques_ngrams(texte_propre, 2)
    stats_tri = calculer_statistiques_ngrams(texte_propre, 3)

    # 4. Persistance : Injection dans le modèle JSON sous le namespace spécifique 'autressources'[cite: 6]
    sauvegarder_statistiques_json(stats, stats_dig, stats_tri, titre_source, lang="autressources")
    
    print("\n[SUCCÈS] Matrice générée et ajoutée au projet !")

if __name__ == "__main__":
    generer_statistiques_sur_mesure()