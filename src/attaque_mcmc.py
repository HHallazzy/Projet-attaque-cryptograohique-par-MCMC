import math
import random
from collections import Counter

import substitution
import permutation

def calculer_log_score(texte_dechiffre: str, log_stats_reference: dict) -> float:
    """
    Mesure la plausibilité linguistique d'un texte déchiffré.
    Utilise les logarithmes PRÉCALCULÉS pour optimiser la vitesse de calcul (Phase 2).
    """
    digrammes_texte = Counter(texte_dechiffre[i:i+2] for i in range(len(texte_dechiffre)-1))
    
    log_score = 0.0
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "
    
    # On parcourt les 27^2 = 729 couples possibles
    for x in alphabet:
        for y in alphabet:
            xy = x + y
            f_k = 1 + digrammes_texte.get(xy, 0)
            
            # ln_r est déjà calculé. Si le digramme est inconnu, ln(1) = 0.0
            ln_r = log_stats_reference.get(xy, 0.0) 
            
            log_score += f_k * ln_r
            
    return log_score

def attaque_mcmc_substitution(cryptogramme: str, iterations: int, stats_reference: dict) -> list:
    """
    Pilote l'algorithme Metropolis-Hastings pour la substitution.
    Implémente le Burn-in et l'échantillonnage par fréquences de visites (Phase 3).
    """
    # PRÉCALCUL : On calcule les logarithmes une seule fois avant la boucle
    log_stats_reference = {k: math.log(v) for k, v in stats_reference.items() if v > 0}
    
    cle_courante = substitution.generer_cle()
    texte_courant = substitution.dechiffrer_texte(cryptogramme, cle_courante)
    score_courant = calculer_log_score(texte_courant, log_stats_reference)
    
    frequences_visites = {}
    burn_in = int(iterations * 0.15) # 15% d'itérations ignorées au début
    
    for i in range(iterations):
        cle_voisine = substitution.muter_substitution(cle_courante)
        texte_voisin = substitution.dechiffrer_texte(cryptogramme, cle_voisine)
        score_voisin = calculer_log_score(texte_voisin, log_stats_reference)
        
        delta = score_voisin - score_courant
        
        # Test d'acceptation probabiliste
        if delta > 0 or math.log(random.uniform(0, 1)) < delta:
            cle_courante = cle_voisine
            score_courant = score_voisin
            
        # ENREGISTREMENT : On compte les visites uniquement après la chauffe
        if i >= burn_in:
            frequences_visites[cle_courante] = frequences_visites.get(cle_courante, 0) + 1
            
    # Trie les clés par nombre de visites décroissant
    top_cles = sorted(frequences_visites.items(), key=lambda x: x[1], reverse=True)
    return top_cles


def attaque_mcmc_permutation(cryptogramme: str, iterations: int, stats_reference: dict, longueur_l: int) -> list:
    """
    Pilote l'algorithme Metropolis-Hastings pour la permutation par blocs.
    """
    log_stats_reference = {k: math.log(v) for k, v in stats_reference.items() if v > 0}
    
    cle_courante = permutation.generer_cle(longueur_l)
    texte_courant = permutation.dechiffrer_permutation(cryptogramme, cle_courante)
    score_courant = calculer_log_score(texte_courant, log_stats_reference)
    
    frequences_visites = {}
    burn_in = int(iterations * 0.15)
    
    for i in range(iterations):
        cle_voisine = permutation.muter_permutation(cle_courante)
        texte_voisin = permutation.dechiffrer_permutation(cryptogramme, cle_voisine)
        score_voisin = calculer_log_score(texte_voisin, log_stats_reference)
        
        delta = score_voisin - score_courant
        
        if delta > 0 or math.log(random.uniform(0, 1)) < delta:
            cle_courante = cle_voisine
            score_courant = score_voisin
            
        if i >= burn_in:
            # Les listes ne peuvent pas être des clés de dictionnaire, on convertit en tuple
            cle_tuple = tuple(cle_courante)
            frequences_visites[cle_tuple] = frequences_visites.get(cle_tuple, 0) + 1
            
    top_cles_tuples = sorted(frequences_visites.items(), key=lambda x: x[1], reverse=True)
    # Reconversion des tuples en listes pour la propreté du code
    top_cles = [(list(cle), visites) for cle, visites in top_cles_tuples]
    
    return top_cles