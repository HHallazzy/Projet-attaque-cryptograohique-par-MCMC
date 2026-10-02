import os
import sys

# Importation de nos outils existants pour ne pas réinventer la roue
from wiki_statistiques import (
    nettoyer_texte, 
    calculer_statistiques, 
    calculer_statistiques_ngrams, 
    sauvegarder_statistiques_json
)

def generer_statistiques_sur_mesure():
    print("="*60)
    print("   CRÉATION D'UNE MATRICE DE STATISTIQUES SUR MESURE")
    print("="*60)
    print("1. Saisir ou coller un texte (idéal pour des textes courts)")
    print("2. Fournir le chemin d'un fichier .txt local (Recommandé)")
    
    choix = input("\nVotre choix (1/2) : ").strip()
    
    texte_brut = ""
    titre_source = "Texte_Personnalise"

    if choix == "1":
        print("\nCollez votre texte ci-dessous (appuyez sur Entrée pour valider) :")
        texte_brut = input("> ")
        titre_source = input("Donnez un nom court à cette source (ex: Rap, Victor_Hugo, Code) : ").strip()
        
    elif choix == "2":
        # Le strip("\"'") permet de gérer le glisser-déposer de Windows dans la console
        chemin_fichier = input("\nEntrez le chemin absolu ou relatif de votre fichier (.txt) : ").strip().strip("\"'")
        
        if not os.path.exists(chemin_fichier):
            print(f"[ERREUR] Le fichier '{chemin_fichier}' est introuvable.")
            return
            
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            texte_brut = f.read()
            
        # On utilise le nom du fichier comme titre de source
        titre_source = os.path.basename(chemin_fichier).replace(".txt", "")
        
    else:
        print("[ERREUR] Choix invalide.")
        return

    if not texte_brut.strip():
        print("[ERREUR] Le texte fourni est vide.")
        return

    print(f"\n[INFO] Traitement de '{titre_source}' ({len(texte_brut)} caractères)...")
    
    # 1. Nettoyage du texte avec notre fonction universelle (retire accents, ponctuation, etc.)
    texte_propre = nettoyer_texte(texte_brut)
    
    # 2. Sauvegarde d'une copie propre dans data/autressources/ pour pouvoir l'attaquer plus tard
    dossier_cible = os.path.join("data", "autressources")
    os.makedirs(dossier_cible, exist_ok=True)
    chemin_texte_propre = os.path.join(dossier_cible, f"{titre_source}.txt")
    
    with open(chemin_texte_propre, 'w', encoding='utf-8') as f:
        f.write(texte_propre)
    print(f"[INFO] Texte formaté (alphabet de 27 caractères) sauvegardé dans : {chemin_texte_propre}")

    # 3. Calculs mathématiques (Digrammes & Trigrammes)
    print("[INFO] Calcul de la matrice de probabilités...")
    stats = calculer_statistiques(texte_propre)
    stats_dig = calculer_statistiques_ngrams(texte_propre, 2)
    stats_tri = calculer_statistiques_ngrams(texte_propre, 3)

    # 4. Injection dans la base de données sous le "lang" autressources
    sauvegarder_statistiques_json(stats, stats_dig, stats_tri, titre_source, lang="autressources")
    
    print("\n[SUCCÈS] Matrice générée et ajoutée au projet !")

if __name__ == "__main__":
    generer_statistiques_sur_mesure()