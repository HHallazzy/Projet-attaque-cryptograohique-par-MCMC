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
    # Découpe le texte en blocs de taille n_gram (ex: paires ou trios de lettres) 
    # et compte immédiatement leurs fréquences d'apparition (f_k).
    ngrams_texte = Counter(texte_dechiffre[i:i+n_gram] for i in range(len(texte_dechiffre)-(n_gram-1)))
    
    log_score = 0.0
    for ngram, f_k in ngrams_texte.items():
        # On cherche le log du N-gramme dans notre modèle de référence.
        # Si la combinaison n'existe pas en français (ex: "QQ"), on applique un poids neutre (ln(1) = 0.0) 
        # pour ne pas fausser le score avec des erreurs mathématiques.
        ln_r = log_stats_reference.get(ngram, 0.0) 
        log_score += f_k * ln_r
            
    return log_score

def attaque_mcmc_substitution(cryptogramme: str, iterations: int, stats_ngrams: dict, n_gram: int = 2) -> list:
    # Optimisation CPU majeure : on précalcule tous les logarithmes une seule fois au début,
    # en ignorant les probabilités à zéro pour éviter une erreur mathématique (log(0)).
    log_stats_reference = {k: math.log(v) for k, v in stats_ngrams.items() if v > 0}
    
    # 1. État initial (Génération d'une clé au hasard pour lancer la chaîne)
    cle_courante = substitution.generer_cle()
    texte_courant = substitution.dechiffrer_texte(cryptogramme, cle_courante)
    score_courant = calculer_log_score(texte_courant, log_stats_reference, n_gram)
    
    frequences_visites = {}
    # Période de chauffe : on ignore les 15 premiers % des itérations 
    # le temps que la chaîne atteigne un quartier de clés plausibles.
    burn_in = int(iterations * 0.15) 
    
    # 2. Boucle principale de la chaîne de Markov
    for i in range(iterations):
        # On génère un état voisin (en échangeant 2 lettres) et on l'évalue
        cle_voisine = substitution.muter_substitution(cle_courante)
        texte_voisin = substitution.dechiffrer_texte(cryptogramme, cle_voisine)
        score_voisin = calculer_log_score(texte_voisin, log_stats_reference, n_gram)
        
        # Le delta représente la différence de vraisemblance entre la nouvelle et l'ancienne clé
        delta = score_voisin - score_courant
        
        # Critère d'acceptation de Metropolis-Hastings :
        # - Si delta > 0, la nouvelle clé est meilleure, on l'accepte toujours.
        # - Sinon, on l'accepte avec une probabilité proportionnelle à sa dégradation,
        #   ce qui permet d'éviter de rester bloqué sur un maximum local (effet anagramme).
        if delta > 0 or math.log(random.uniform(0, 1)) < delta:
            cle_courante = cle_voisine
            score_courant = score_voisin
            
        # 3. Échantillonnage : on ne commence à compter les visites qu'après le burn-in
        if i >= burn_in:
            frequences_visites[cle_courante] = frequences_visites.get(cle_courante, 0) + 1
            
    # On trie le dictionnaire pour renvoyer les clés les plus visitées en premier
    top_cles = sorted(frequences_visites.items(), key=lambda x: x[1], reverse=True)
    return top_cles

def attaque_mcmc_permutation(cryptogramme: str, iterations: int, stats_ngrams: dict, taille_bloc: int, n_gram: int = 2) -> list:
    # (Identique à la substitution : précalcul des logarithmes)
    log_stats_reference = {k: math.log(v) for k, v in stats_ngrams.items() if v > 0}
    
    cle_courante = permutation.generer_cle(taille_bloc)
    texte_courant = permutation.dechiffrer_permutation(cryptogramme, cle_courante)
    score_courant = calculer_log_score(texte_courant, log_stats_reference, n_gram)
    
    frequences_visites = {}
    burn_in = int(iterations * 0.15)
    
    for i in range(iterations):
        # La mutation de permutation déplace un sous-bloc entier pour garantir l'irréductibilité
        cle_voisine = permutation.muter_permutation(cle_courante)
        texte_voisin = permutation.dechiffrer_permutation(cryptogramme, cle_voisine)
        score_voisin = calculer_log_score(texte_voisin, log_stats_reference, n_gram)
        
        delta = score_voisin - score_courant
        
        # Test d'acceptation probabiliste
        if delta > 0 or math.log(random.uniform(0, 1)) < delta:
            cle_courante = cle_voisine
            score_courant = score_voisin
            
        if i >= burn_in:
            # Astuce Python : Les listes ne peuvent pas servir de clés dans un dictionnaire 
            # car elles sont mutables. On convertit temporairement la clé en tuple pour la stocker.
            cle_tuple = tuple(cle_courante)
            frequences_visites[cle_tuple] = frequences_visites.get(cle_tuple, 0) + 1
            
    top_cles_tuples = sorted(frequences_visites.items(), key=lambda x: x[1], reverse=True)
    
    # On reconvertit proprement les tuples en listes pour garder un format de sortie cohérent
    top_cles = [(list(cle), visites) for cle, visites in top_cles_tuples]
    
    return top_cles