"""
Interface graphique de l'outil de cryptanalyse par chaîne de Markov Monte-Carlo.

Tkinter gère les interactions avec l'utilisateur, Matplotlib visualise
l'évolution du score et un thread dédié exécute les calculs afin de ne pas
bloquer la boucle d'événements de l'interface.
"""

import sys
import os
import json
import random
import math
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import urllib.parse

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Les modules métier sont stockés dans ``src`` et ne font pas partie du
# paquet installé ; ce chemin doit donc être disponible avant les imports.
sys.path.insert(0, os.path.abspath('src'))
import substitution
import permutation
from attaque_mcmc import calculer_log_score
from wiki_statistiques import obtenir_texte_reference, nettoyer_texte

class ApplicationMCMC(tk.Tk):
    """
    Fenêtre principale de l'application de cryptanalyse (Mode Présentation).
    Gère l'interface utilisateur, le calibrage statistique et le pilotage du thread MCMC.
    """
    
    def __init__(self):
        super().__init__()
        self.title("Logiciel de Cryptanalyse MCMC - IUT d'Amiens (Mode Présentation)")
        # Dimensions adaptées pour une visibilité optimale sur vidéoprojecteur
        self.geometry("1400x1000")
        self.configure(padx=15, pady=15)
        
        # Interception de la fermeture pour tuer proprement les threads en arrière-plan
        self.protocol("WM_DELETE_WINDOW", self.fermer_application)
        
        self.en_cours = False
        self.x_data = [] 
        self.y_data = [] 
        
        self.appliquer_style_presentation()
        self.creer_widgets()
        self.charger_langues()

    def appliquer_style_presentation(self):
        """Configure une présentation lisible sur un écran ou un vidéoprojecteur."""
        style = ttk.Style()
        style.theme_use('clam')
        
        police_globale = ("Segoe UI", 12)
        police_titre = ("Segoe UI", 12, "bold")
        
        style.configure(".", font=police_globale)
        style.configure("TLabelframe.Label", font=police_titre, foreground="#005a9e")
        style.configure("TButton", font=("Segoe UI", 12, "bold"), padding=10)
        style.configure("TCombobox", padding=5)
        style.configure("TRadiobutton", font=police_globale)
        
        # Matplotlib utilise sa propre configuration de styles : elle doit être
        # définie séparément des styles ttk appliqués aux widgets Tkinter.
        plt.rc('font', size=12)
        plt.rc('axes', titlesize=14, labelsize=12)
        plt.rc('xtick', labelsize=10)
        plt.rc('ytick', labelsize=10)

    def fermer_application(self):
        """Ferme l'application et interrompt les ressources de l'interface."""
        self.quit()
        self.destroy()
        os._exit(0)

    def creer_widgets(self):
        """Construit les contrôles de paramétrage et les zones de résultats."""
        
        # ==========================================
        # PANNEAU GAUCHE : PARAMÉTRAGE DE L'ATTAQUE
        # ==========================================
        frame_gauche = ttk.LabelFrame(self, text="Paramètres de l'attaque", padding=15)
        frame_gauche.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        
        ttk.Label(frame_gauche, text="1. Modèle Statistique :").pack(anchor=tk.W, pady=(0, 5))
        self.combo_langue = ttk.Combobox(frame_gauche, state="readonly", font=("Segoe UI", 11))
        self.combo_langue.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(frame_gauche, text="2. Type de chiffrement :").pack(anchor=tk.W, pady=(0, 5))
        self.combo_attaque = ttk.Combobox(frame_gauche, state="readonly", 
                                          values=["Substitution", "Permutation (Blocs de 10)"], font=("Segoe UI", 11))
        self.combo_attaque.current(0)
        self.combo_attaque.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(frame_gauche, text="3. Précision Mathématique :").pack(anchor=tk.W, pady=(0, 5))
        self.var_ngram = tk.IntVar(value=2)
        ttk.Radiobutton(frame_gauche, text="Digrammes (N=2)", variable=self.var_ngram, value=2).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(frame_gauche, text="Trigrammes (N=3)", variable=self.var_ngram, value=3).pack(anchor=tk.W, pady=2)
        
        ttk.Label(frame_gauche, text="\n4. Source de la cible :").pack(anchor=tk.W, pady=(0, 5))
        self.combo_source = ttk.Combobox(frame_gauche, state="readonly", 
                                         values=[
                                             "Aléatoire (Base locale)", 
                                             "Parcourir un fichier local (.txt)", 
                                             "Saisir ou coller un texte",
                                             "Saisir URL/Titre Wikipédia"
                                         ], font=("Segoe UI", 11))
        self.combo_source.current(0)
        self.combo_source.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(frame_gauche, text="5. Nombre d'itérations :").pack(anchor=tk.W, pady=(0, 5))
        self.spin_iterations = ttk.Spinbox(frame_gauche, from_=1000, to=100000, increment=1000, font=("Segoe UI", 12))
        self.spin_iterations.set(10000)
        self.spin_iterations.pack(fill=tk.X, pady=(0, 30))
        
        self.btn_lancer = ttk.Button(frame_gauche, text="▶ LANCER L'ATTAQUE", command=self.demarrer_mcmc)
        self.btn_lancer.pack(fill=tk.X)
        
        # ==========================================
        # PANNEAU DROIT : VISUALISATION DES RÉSULTATS
        # ==========================================
        frame_droit = ttk.Frame(self)
        frame_droit.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        police_code = ("Consolas", 14)
        
        frame_original = ttk.LabelFrame(frame_droit, text="Texte Original (Cible propre)", padding=10)
        frame_original.pack(fill=tk.X, pady=(0, 10))
        
        self.var_texte_original = tk.StringVar(value="Le texte formaté apparaîtra ici au lancement...")
        self.lbl_texte_original = ttk.Label(frame_original, textvariable=self.var_texte_original, 
                                            wraplength=900, font=police_code, foreground="#0078D7")
        self.lbl_texte_original.pack(fill=tk.X)
        
        frame_texte = ttk.LabelFrame(frame_droit, text="Texte Déchiffré (Temps Réel)", padding=10)
        frame_texte.pack(fill=tk.X, pady=(0, 10))
        
        self.var_texte_courant = tk.StringVar(value="En attente du lancement...")
        self.lbl_texte = ttk.Label(frame_texte, textvariable=self.var_texte_courant, 
                                   wraplength=900, font=police_code)
        self.lbl_texte.pack(fill=tk.X)
        
        frame_graph = ttk.LabelFrame(frame_droit, text="Suivi de l'Algorithme", padding=5)
        frame_graph.pack(fill=tk.BOTH, expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 3.5), dpi=100)
        self.ax.set_title("Évolution du Log-Score (Acceptations et rejets)")
        self.ax.set_xlabel("Itérations")
        self.ax.set_ylabel("Score")
        
        self.ligne_score, = self.ax.plot([], [], 'b-', linewidth=1.2, alpha=0.8, label="Score Courant")
        self.ax.legend()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_graph)
        self.toolbar = NavigationToolbar2Tk(self.canvas, frame_graph)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        frame_rapport = ttk.LabelFrame(frame_droit, text="Rapport Final et Résultats", padding=10)
        frame_rapport.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.txt_rapport = tk.Text(frame_rapport, height=8, font=("Consolas", 13), wrap=tk.WORD)
        self.txt_rapport.pack(fill=tk.BOTH, expand=True)
        self.txt_rapport.insert(tk.END, "En attente du lancement...")
        self.txt_rapport.config(state=tk.DISABLED)

    def charger_langues(self):
        """Recherche les langues disponibles dans les sous-répertoires de ``data``."""
        if os.path.exists('data'):
            langues = sorted([d.upper() for d in os.listdir('data') if os.path.isdir(os.path.join('data', d))])
            if langues:
                self.combo_langue['values'] = langues
                self.combo_langue.current(0)
                return
        messagebox.showwarning("Attention", "Aucune donnée trouvée. Lancez wiki_statistiques.py.")

    def demander_texte_manuel(self) -> str:
        """Affiche une boîte de dialogue modale et retourne le texte saisi."""
        dialog = tk.Toplevel(self)
        dialog.title("Saisie manuelle du texte")
        dialog.geometry("800x500")
        dialog.transient(self) 
        dialog.grab_set()

        ttk.Label(dialog, text="Collez ou tapez votre texte ci-dessous :").pack(pady=(10, 5), padx=10, anchor=tk.W)
        
        # Une liste mutable permet au callback de transmettre sa valeur à la
        # portée appelante avant la fermeture de la fenêtre modale.
        resultat = [""]
        def valider():
            resultat[0] = text_area.get("1.0", tk.END).strip()
            dialog.destroy()
            
        # Le bouton est placé avant la zone de texte afin de rester visible
        # lorsque celle-ci est agrandie par ``fill=tk.BOTH``.
        ttk.Button(dialog, text="Valider ce texte", command=valider).pack(side=tk.BOTTOM, pady=15)
        
        text_area = tk.Text(dialog, wrap=tk.WORD, font=("Consolas", 12))
        text_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.wait_window(dialog)
        return resultat[0] if resultat[0] else None

    def preparer_texte_cible(self, langue: str) -> str:
        """
        Charge le texte cible selon la source choisie dans l'interface.

        La méthode centralise les quatre modes d'entrée afin que le lancement
        de l'attaque reçoive toujours un texte brut, quelle que soit son origine.
        """
        choix = self.combo_source.get()
        
        if "Aléatoire" in choix:
            dossier = os.path.join('data', langue.lower())
            fichiers = [f for f in os.listdir(dossier) if f.endswith('.txt')]
            if fichiers:
                with open(os.path.join(dossier, random.choice(fichiers)), 'r', encoding='utf-8') as f:
                    return f.read()
                    
        elif "fichier local" in choix:
            dossier_initial = os.path.abspath(os.path.join('data', langue.lower()))
            chemin = filedialog.askopenfilename(
                title="Sélectionnez un fichier texte à attaquer",
                initialdir=dossier_initial,
                filetypes=[("Fichiers Texte", "*.txt"), ("Tous les fichiers", "*.*")]
            )
            if chemin:
                with open(chemin, 'r', encoding='utf-8') as f:
                    return f.read()
                    
        elif "coller" in choix:
            return self.demander_texte_manuel()
            
        elif "Wikipédia" in choix:
            saisie = simpledialog.askstring("Wikipédia", "Entrez le titre ou l'URL de la page :")
            if saisie:
                if "wikipedia.org/wiki/" in saisie:
                    saisie = urllib.parse.unquote(saisie.split("wikipedia.org/wiki/")[-1])
                return obtenir_texte_reference(saisie, lang=langue.lower())
                
        return None

    def demarrer_mcmc(self):
        """Prépare le modèle statistique puis lance l'attaque dans un thread."""
        # Une seule attaque peut modifier les données affichées à la fois.
        if self.en_cours: return
        langue = self.combo_langue.get().lower()
        if not langue: return
        
        texte_brut = self.preparer_texte_cible(langue)
        if not texte_brut:
            return 
            
        # L'ajout d'un texte fourni par l'utilisateur modifie durablement le
        # modèle statistique ; une confirmation évite d'y intégrer un texte
        # dans une langue incorrecte.
        choix_source = self.combo_source.get()
        if "Aléatoire" not in choix_source:
            reponse = messagebox.askyesno(
                "Mise à jour du Modèle Statistique", 
                "Voulez-vous ENREGISTRER les statistiques de ce texte dans la matrice de la langue étudiée ?\n\n"
                "(Répondez NON si ce texte n'est pas dans la bonne langue pour éviter de fausser l'apprentissage)."
            )
            if reponse:
                from wiki_statistiques import calculer_statistiques, calculer_statistiques_ngrams, sauvegarder_statistiques_json
                tp = nettoyer_texte(texte_brut)
                st = calculer_statistiques(tp)
                s_d = calculer_statistiques_ngrams(tp, 2)
                s_t = calculer_statistiques_ngrams(tp, 3)
                titre = f"Texte_Injecte_{random.randint(1000, 9999)}"
                sauvegarder_statistiques_json(st, s_d, s_t, titre, lang=langue)
                messagebox.showinfo("Succès", "Modèle statistique mis à jour avec succès.")
        
        chemin_stats = os.path.join('data', langue, 'stats_reference.json')
        with open(chemin_stats, 'r', encoding='utf-8') as f:
            stats = json.load(f)
            
        texte_propre = nettoyer_texte(texte_brut)
        texte_clair = texte_propre[:2000]
        self.var_texte_original.set(f"{texte_clair[:120]}...")
        
        n_gram = self.var_ngram.get()
        cle_stats = "trigrammes" if n_gram == 3 else "digrammes"
        dico_stats = stats.get(cle_stats, {})
        total_ngrams = max(1, sum(dico_stats.values()))
        
        # Les occurrences sont converties en poids logarithmiques. L'échelle
        # correspond à la formule 1.5 du sujet : r(x, y) = 1 + occurrences
        # observées dans le corpus de référence.
        echelle_ref = 10000.0 if n_gram == 3 else 2500.0
        
        # Le facteur de lissage réduit l'amplitude des écarts de score. La
        # chaîne peut ainsi accepter certaines dégradations et sortir d'un
        # optimum local au lieu de rester bloquée trop tôt.
        facteur_lissage = 6.0
        
        log_stats = {
            k: math.log(1.0 + (v / total_ngrams) * echelle_ref) / facteur_lissage
            for k, v in dico_stats.items() if v > 0
        }
        
        type_attaque = self.combo_attaque.get()
        iterations = int(self.spin_iterations.get())
        
        self.en_cours = True
        self.btn_lancer.state(['disabled'])
        self.x_data.clear()
        self.y_data.clear()
        
        self.txt_rapport.config(state=tk.NORMAL)
        self.txt_rapport.delete(1.0, tk.END)
        self.txt_rapport.insert(tk.END, "Attaque en cours... Veuillez patienter.")
        self.txt_rapport.config(state=tk.DISABLED)
        
        # ``clear`` supprime également les titres, labels et légendes ; ils
        # doivent être recréés avant de tracer les nouvelles données.
        self.ax.clear()
        self.ax.set_title("Évolution du Log-Score (Acceptations et rejets)")
        self.ax.set_xlabel("Itérations")
        self.ax.set_ylabel("Score")
        
        self.ligne_score, = self.ax.plot([], [], 'b-', linewidth=1.2, alpha=0.8)
        
        # Les premières itérations servent à rejoindre une zone représentative
        # de l'espace des clés. Elles ne sont pas utilisées pour le classement.
        burn_in = int(iterations * 0.15)
        self.ax.axvline(x=burn_in, color='r', linestyle='--', label=f"Fin Chauffe ({burn_in})")
        self.ax.legend()
        
        # Les calculs de déchiffrement et de score sont coûteux. Le thread
        # principal reste ainsi disponible pour rafraîchir l'interface.
        thread = threading.Thread(target=self.boucle_mcmc,
                                  args=(texte_clair, type_attaque, iterations, log_stats, n_gram, burn_in))
        thread.daemon = True
        thread.start()

    def boucle_mcmc(self, texte_clair: str, type_attaque: str, iterations: int, log_stats: dict, n_gram: int, burn_in: int):
        """
        Explore l'espace des clés avec l'algorithme de Metropolis-Hastings.

        À chaque itération, une clé voisine est générée puis comparée à la
        clé courante. Les meilleures clés sont toujours acceptées ; les clés
        moins bonnes peuvent l'être selon une probabilité dépendant de
        l'écart de score. Cette étape limite le risque de rester dans un
        optimum local.
        """
        if "Substitution" in type_attaque:
            cle_secrete = substitution.generer_cle()
            cryptogramme = substitution.chiffrer_texte(texte_clair, cle_secrete)
            cle_courante = substitution.generer_cle()
            texte_courant = substitution.dechiffrer_texte(cryptogramme, cle_courante)
        else:
            taille_bloc = 10
            cle_secrete = permutation.generer_cle(taille_bloc)
            cryptogramme = permutation.chiffrer_permutation(texte_clair, cle_secrete)
            cle_courante = permutation.generer_cle(taille_bloc)
            texte_courant = permutation.dechiffrer_permutation(cryptogramme, cle_courante)
            
        # Le score initial sert de référence pour calculer le gain ou la perte
        # associé à chaque proposition de clé.
        score_courant = calculer_log_score(texte_courant, log_stats, n_gram)
        frequences_visites = {}
        scores_cles = {}
        
        for i in range(iterations):
            if "Substitution" in type_attaque:
                cle_voisine = substitution.muter_substitution(cle_courante)
                texte_voisin = substitution.dechiffrer_texte(cryptogramme, cle_voisine)
            else:
                cle_voisine = permutation.muter_permutation(cle_courante)
                texte_voisin = permutation.dechiffrer_permutation(cryptogramme, cle_voisine)
                
            score_voisin = calculer_log_score(texte_voisin, log_stats, n_gram)
            delta = score_voisin - score_courant
            
            # Test de Metropolis-Hastings en logarithmes. Avec U uniforme sur
            # ]0, 1[, la comparaison évite de calculer directement un rapport
            # de scores potentiellement très petit.
            if delta > 0 or math.log(random.uniform(0, 1)) < delta:
                cle_courante = cle_voisine
                score_courant = score_voisin
                texte_courant = texte_voisin
                
            # Après la période de chauffe, les visites servent à estimer les
            # clés les plus probables. Une liste est convertie en tuple pour
            # pouvoir l'utiliser comme clé de dictionnaire.
            if i >= burn_in:
                cle_mem = tuple(cle_courante) if isinstance(cle_courante, list) else cle_courante
                frequences_visites[cle_mem] = frequences_visites.get(cle_mem, 0) + 1
                scores_cles[cle_mem] = score_courant
                
            # Toutes les itérations sont conservées pour représenter les
            # oscillations réelles du score, y compris les rejets.
            self.x_data.append(i)
            self.y_data.append(score_courant)
                
            if i % 100 == 0 or i == iterations - 1:
                # ``after`` planifie la mise à jour dans le thread Tkinter ;
                # les widgets ne doivent pas être manipulés depuis ce thread.
                self.after(0, self.maj_graphique_draw, texte_courant)
        
        # Le classement est établi sur la fréquence des visites après chauffe,
        # tandis que ``scores_cles`` conserve le score associé à chaque clé.
        top_cles = sorted(frequences_visites.items(), key=lambda x: x[1], reverse=True)[:3]
        self.after(0, self.terminer_attaque, top_cles, scores_cles, cle_secrete, type_attaque, cryptogramme, texte_clair)

    def maj_graphique_draw(self, texte: str):
        """Actualise le texte, le score et l'échelle du graphique dans Tkinter."""
        if self.x_data:
            self.var_texte_courant.set(f"[{self.x_data[-1]}] {texte[:120]}...")
        self.ligne_score.set_data(self.x_data, self.y_data)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle() 

    def terminer_attaque(self, top_cles: list, scores_cles: dict, cle_secrete, type_attaque: str, cryptogramme: str, texte_clair: str):
        """Construit le rapport final à partir des clés les plus visitées."""
        self.en_cours = False
        self.btn_lancer.state(['!disabled'])
        
        rapport = f"Clé cible : {cle_secrete}\n"
        rapport += "-"*60 + "\n"
        
        for rang, (cle, visites) in enumerate(top_cles, 1):
            if "Permutation" in type_attaque:
                cle = list(cle)
                texte_dechiffre = permutation.dechiffrer_permutation(cryptogramme, cle)
                cle_mem = tuple(cle)
            else:
                texte_dechiffre = substitution.dechiffrer_texte(cryptogramme, cle)
                cle_mem = cle

            # La première clé du classement constitue le meilleur aperçu à
            # afficher immédiatement à l'utilisateur.
            if rang == 1:
                self.var_texte_courant.set(f"[Meilleure clé #1] {texte_dechiffre[:120]}...")

            exactes = sum(1 for a, b in zip(cle_secrete, cle) if a == b)
            total = len(cle_secrete)
            score_log = scores_cles.get(cle_mem, 0)
            
            rapport += f"#{rang} | Visites : {visites} | Score : {score_log:.2f} | Précision : {exactes}/{total}\n"
            rapport += f"Clé : {cle}\n"
            rapport += f"Décodé : {texte_dechiffre[:120]}...\n\n"
            
        self.txt_rapport.config(state=tk.NORMAL)
        self.txt_rapport.delete(1.0, tk.END)
        self.txt_rapport.insert(tk.END, rapport)
        self.txt_rapport.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = ApplicationMCMC()
    app.mainloop()