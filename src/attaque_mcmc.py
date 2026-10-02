import math
import random
from collections import Counter

import substitution
import permutation

def calculer_log_score(texte_dechiffre: str, log_stats_reference: dict, n_gram: int) -> float:
    """
    Mesure la plausibilité linguistique avec une optimisation de complexité O(L).
    Au lieu de boucler sur tout l'alphabet, on ne calcule que sur les N-grammes présents.
    """
    # Découpage du texte selon la taille demandée (2 ou 3)
    ngrams_texte = Counter(texte_dechiffre[i:i+n_gram] for i in range(len(texte_dechiffre)-(n_gram-1)))
    
    log_score = 0.0
    for ngram, f_k in ngrams_texte.items():
        # Si le N-gramme n'existe pas dans le modèle, ln(1) = 0.0
        ln_r = log_stats_reference.get(ngram, 0.0) 
        log_score += f_k * ln_r
            
    return log_score

def attaque_mcmc_substitution(cryptogramme: str, iterations: int, stats_ngrams: dict, n_gram: int = 2) -> list:
    log_stats_reference = {k: math.log(v) for k, v in stats_ngrams.items() if v > 0}
    
    cle_courante = substitution.generer_cle()
    texte_courant = substitution.dechiffrer_texte(cryptogramme, cle_courante)
    score_courant = calculer_log_score(texte_courant, log_stats_reference, n_gram)
    
    frequences_visites = {}
    burn_in = int(iterations * 0.15)
    
    for i in range(iterations):
        cle_voisine = substitution.muter_substitution(cle_courante)
        texte_voisin = substitution.dechiffrer_texte(cryptogramme, cle_voisine)
        score_voisin = calculer_log_score(texte_voisin, log_stats_reference, n_gram)
        
        delta = score_voisin - score_courant
        
        if delta > 0 or math.log(random.uniform(0, 1)) < delta:
            cle_courante = cle_voisine
            score_courant = score_voisin
            
        if i >= burn_in:
            frequences_visites[cle_courante] = frequences_visites.get(cle_courante, 0) + 1
            
    top_cles = sorted(frequences_visites.items(), key=lambda x: x[1], reverse=True)
    return top_cles

def attaque_mcmc_permutation(cryptogramme: str, iterations: int, stats_ngrams: dict, taille_bloc: int, n_gram: int = 2) -> list:
    log_stats_reference = {k: math.log(v) for k, v in stats_ngrams.items() if v > 0}
    
    cle_courante = permutation.generer_cle(taille_bloc)
    texte_courant = permutation.dechiffrer_permutation(cryptogramme, cle_courante)
    score_courant = calculer_log_score(texte_courant, log_stats_reference, n_gram)
    
    frequences_visites = {}
    burn_in = int(iterations * 0.15)
    
    for i in range(iterations):
        cle_voisine = permutation.muter_permutation(cle_courante)
        texte_voisin = permutation.dechiffrer_permutation(cryptogramme, cle_voisine)
        score_voisin = calculer_log_score(texte_voisin, log_stats_reference, n_gram)
        
        delta = score_voisin - score_courant
        
        if delta > 0 or math.log(random.uniform(0, 1)) < delta:
            cle_courante = cle_voisine
            score_courant = score_voisin
            
        if i >= burn_in:
            cle_tuple = tuple(cle_courante)
            frequences_visites[cle_tuple] = frequences_visites.get(cle_tuple, 0) + 1
            
    top_cles_tuples = sorted(frequences_visites.items(), key=lambda x: x[1], reverse=True)
    top_cles = [(list(cle), visites) for cle, visites in top_cles_tuples]
    
    return top_cles