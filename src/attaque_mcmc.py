import math
import random
from collections import Counter

# Importation des modules existants selon l'architecture définie
import substitution
import permutation

def calculer_log_score(texte_dechiffre: str, stats_reference: dict) -> float:
    """
    Mesure la plausibilité linguistique d'un texte déchiffré.
    Utilise la somme des logarithmes pour éviter l'overflow.
    """
    # On compte les occurrences des digrammes dans le texte déchiffré
    # zip permet de créer des paires de caractères consécutifs rapidement
    digrammes_texte = Counter(texte_dechiffre[i:i+2] for i in range(len(texte_dechiffre)-1))
    
    log_score = 0.0
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "
    
    # On parcourt les 27^2 = 729 couples possibles (x,y)
    for x in alphabet:
        for y in alphabet:
            xy = x + y
            # fk(x,y) = 1 + occurrences dans le texte déchiffré
            f_k = 1 + digrammes_texte.get(xy, 0)
            
            # r(x,y) = 1 + occurrences dans la référence
            # On suppose que stats_reference contient déjà cette valeur r(x,y) pour chaque clé 'xy'
            # Si le digramme n'est pas dans le dico, sa valeur par défaut est 1 (0 occurrence + 1)
            r_xy = stats_reference.get(xy, 1) 
            
            # ln S(k) = Somme ( fk(x,y) * ln(r(x,y)) )
            log_score += f_k * math.log(r_xy)
            
    return log_score

def muter_substitution(cle_actuelle: str) -> str:
    """
    Génère une clé voisine par transposition de deux lettres au hasard.
    """
    cle_liste = list(cle_actuelle)
    # Tirage de 2 indices distincts entre 0 et 25
    i, j = random.sample(range(26), 2)
    # Échange (transposition)
    cle_liste[i], cle_liste[j] = cle_liste[j], cle_liste[i]
    return "".join(cle_liste)

def muter_permutation(cle_actuelle: list) -> list:
    """
    Crée une variation de la clé de permutation en intervertissant deux index.
    """
    nouvelle_cle = cle_actuelle.copy()
    i, j = random.sample(range(len(nouvelle_cle)), 2)
    nouvelle_cle[i], nouvelle_cle[j] = nouvelle_cle[j], nouvelle_cle[i]
    return nouvelle_cle

def attaque_mcmc_substitution(cryptogramme: str, iterations: int, stats_reference: dict) -> tuple:
    """
    Pilote l'algorithme Metropolis-Hastings pour la substitution mono-alphabétique.
    Retourne la meilleure clé trouvée et le texte déchiffré correspondant.
    """
    # 1. Initialisation (État 0)
    cle_courante = substitution.generer_cle()
    texte_courant = substitution.dechiffrer_texte(cryptogramme, cle_courante)
    score_courant = calculer_log_score(texte_courant, stats_reference)
    
    # Historique absolu (Optimisation mémoire)
    meilleure_cle_absolue = cle_courante
    meilleur_score_absolu = score_courant
    meilleur_texte = texte_courant
    
    # 2. Boucle de Markov
    for _ in range(iterations):
        # Mutation
        cle_voisine = muter_substitution(cle_courante)
        texte_voisin = substitution.dechiffrer_texte(cryptogramme, cle_voisine)
        score_voisin = calculer_log_score(texte_voisin, stats_reference)
        
        # Sélection
        delta = score_voisin - score_courant
        
        # Si le score voisin est meilleur (delta > 0), ou si accepté par probabilité U
        if delta > 0 or math.log(random.uniform(0, 1)) < delta:
            # On accepte la mutation
            cle_courante = cle_voisine
            score_courant = score_voisin
            
            # Mise à jour du record absolu si nécessaire
            if score_courant > meilleur_score_absolu:
                meilleur_score_absolu = score_courant
                meilleure_cle_absolue = cle_courante
                meilleur_texte = texte_voisin
                
    return meilleure_cle_absolue, meilleur_texte


def attaque_mcmc_permutation(cryptogramme: str, iterations: int, stats_reference: dict, longueur_l: int) -> tuple:
    """
    Pilote l'algorithme Metropolis-Hastings pour la permutation par blocs.
    """
    # 1. Initialisation
    cle_courante = permutation.generer_cle(longueur_l)
    texte_courant = permutation.dechiffrer_permutation(cryptogramme, cle_courante)
    score_courant = calculer_log_score(texte_courant, stats_reference)
    
    meilleure_cle_absolue = cle_courante
    meilleur_score_absolu = score_courant
    meilleur_texte = texte_courant
    
    # 2. Boucle de Markov
    for _ in range(iterations):
        # Mutation
        cle_voisine = muter_permutation(cle_courante)
        texte_voisin = permutation.dechiffrer_permutation(cryptogramme, cle_voisine)
        score_voisin = calculer_log_score(texte_voisin, stats_reference)
        
        # Sélection
        delta = score_voisin - score_courant
        
        if delta > 0 or math.log(random.uniform(0, 1)) < delta:
            # On accepte d'aller dans l'état k'
            cle_courante = cle_voisine
            score_courant = score_voisin
            
            if score_courant > meilleur_score_absolu:
                meilleur_score_absolu = score_courant
                meilleure_cle_absolue = cle_courante
                meilleur_texte = texte_voisin
                
    return meilleure_cle_absolue, meilleur_texte