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
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sys.path.insert(0, os.path.abspath('src'))
import substitution
import permutation
from attaque_mcmc import calculer_log_score
from wiki_statistiques import obtenir_texte_reference, nettoyer_texte

class ApplicationMCMC(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Logiciel de Cryptanalyse MCMC - IUT d'Amiens")
        self.geometry("1100x800")
        self.configure(padx=10, pady=10)
        
        # NOUVEAU : Interception du clic sur la croix rouge
        self.protocol("WM_DELETE_WINDOW", self.fermer_application)
        
        self.en_cours = False
        self.x_data = []
        self.y_data = []
        
        self.creer_widgets()
        self.charger_langues()

    def fermer_application(self):
        """Assure la fermeture complète et immédiate de tous les threads en arrière-plan."""
        self.quit()
        self.destroy()
        os._exit(0) # Force l'arrêt de Python (évite le blocage dans le terminal)

    def creer_widgets(self):
        # --- PANNEAU GAUCHE : CONTRÔLES ---
        frame_gauche = ttk.LabelFrame(self, text="Paramètres de l'attaque", padding=15)
        frame_gauche.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(frame_gauche, text="1. Modèle Statistique :").pack(anchor=tk.W, pady=(0, 5))
        self.combo_langue = ttk.Combobox(frame_gauche, state="readonly")
        self.combo_langue.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(frame_gauche, text="2. Type de chiffrement :").pack(anchor=tk.W, pady=(0, 5))
        self.combo_attaque = ttk.Combobox(frame_gauche, state="readonly", 
                                          values=["Substitution", "Permutation (Blocs de 10)"])
        self.combo_attaque.current(0)
        self.combo_attaque.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(frame_gauche, text="3. Précision Mathématique :").pack(anchor=tk.W, pady=(0, 5))
        self.var_ngram = tk.IntVar(value=2)
        ttk.Radiobutton(frame_gauche, text="Digrammes (N=2)", variable=self.var_ngram, value=2).pack(anchor=tk.W)
        ttk.Radiobutton(frame_gauche, text="Trigrammes (N=3)", variable=self.var_ngram, value=3).pack(anchor=tk.W)
        
        ttk.Label(frame_gauche, text="\n4. Source de la cible :").pack(anchor=tk.W, pady=(0, 5))
        self.combo_source = ttk.Combobox(frame_gauche, state="readonly", 
                                         values=[
                                             "Aléatoire (Base locale)", 
                                             "Parcourir un fichier local (.txt)", 
                                             "Saisir ou coller un texte",
                                             "Saisir URL/Titre Wikipédia"
                                         ])
        self.combo_source.current(0)
        self.combo_source.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(frame_gauche, text="5. Nombre d'itérations :").pack(anchor=tk.W, pady=(0, 5))
        self.spin_iterations = ttk.Spinbox(frame_gauche, from_=1000, to=100000, increment=1000)
        self.spin_iterations.set(15000)
        self.spin_iterations.pack(fill=tk.X, pady=(0, 25))
        
        self.btn_lancer = ttk.Button(frame_gauche, text="▶ LANCER L'ATTAQUE", command=self.demarrer_mcmc)
        self.btn_lancer.pack(fill=tk.X, ipady=10)
        
        # --- PANNEAU DROIT : VISUALISATION ---
        frame_droit = ttk.Frame(self)
        frame_droit.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        frame_original = ttk.LabelFrame(frame_droit, text="Texte Original (Cible propre)", padding=10)
        frame_original.pack(fill=tk.X, pady=(0, 10))
        
        self.var_texte_original = tk.StringVar(value="Le texte formaté apparaîtra ici au lancement...")
        self.lbl_texte_original = ttk.Label(frame_original, textvariable=self.var_texte_original, 
                                            wraplength=750, font=("Consolas", 10), foreground="green")
        self.lbl_texte_original.pack(fill=tk.X)
        
        frame_texte = ttk.LabelFrame(frame_droit, text="Texte Déchiffré (Temps Réel)", padding=10)
        frame_texte.pack(fill=tk.X, pady=(0, 10))
        
        self.var_texte_courant = tk.StringVar(value="En attente du lancement...")
        self.lbl_texte = ttk.Label(frame_texte, textvariable=self.var_texte_courant, 
                                   wraplength=750, font=("Consolas", 10))
        self.lbl_texte.pack(fill=tk.X)
        
        frame_graph = ttk.LabelFrame(frame_droit, text="Suivi de la Chaîne de Markov (Échantillonnage MCMC)", padding=10)
        frame_graph.pack(fill=tk.BOTH, expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(7, 4), dpi=100)
        self.ax.set_title("Convergence du Log-Score vers le plateau de vraisemblance")
        self.ax.set_xlabel("Itérations")
        self.ax.set_ylabel("Score (Log-Vraisemblance)")
        
        self.ligne_score, = self.ax.plot([], [], 'b-', linewidth=1.5, alpha=0.8, label="Score Courant")
        self.ax.legend()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_graph)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def charger_langues(self):
        if os.path.exists('data'):
            langues = [d.upper() for d in os.listdir('data') if os.path.isdir(os.path.join('data', d))]
            if langues:
                self.combo_langue['values'] = langues
                self.combo_langue.current(0)
                return
        messagebox.showwarning("Attention", "Aucune donnée trouvée. Lancez wiki_statistiques.py.")

    def demander_texte_manuel(self):
        dialog = tk.Toplevel(self)
        dialog.title("Saisie manuelle du texte")
        dialog.geometry("600x400")
        dialog.transient(self) 
        dialog.grab_set()

        ttk.Label(dialog, text="Collez ou tapez votre texte ci-dessous :").pack(pady=(10, 5), padx=10, anchor=tk.W)
        
        text_area = tk.Text(dialog, wrap=tk.WORD, font=("Consolas", 10))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        resultat = [""]
        def valider():
            resultat[0] = text_area.get("1.0", tk.END).strip()
            dialog.destroy()
            
        ttk.Button(dialog, text="Valider ce texte", command=valider).pack(pady=10)
        self.wait_window(dialog)
        return resultat[0] if resultat[0] else None

    def preparer_texte_cible(self, langue: str) -> str:
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
        if self.en_cours: return
        langue = self.combo_langue.get().lower()
        if not langue: return
        
        chemin_stats = os.path.join('data', langue, 'stats_reference.json')
        with open(chemin_stats, 'r', encoding='utf-8') as f:
            stats = json.load(f)
            
        n_gram = self.var_ngram.get()
        cle_stats = "trigrammes" if n_gram == 3 else "digrammes"
        log_stats = {k: math.log(v) for k, v in stats.get(cle_stats, {}).items() if v > 0}
        
        texte_brut = self.preparer_texte_cible(langue)
        if not texte_brut:
            return 
            
        texte_propre = nettoyer_texte(texte_brut)
        texte_clair = texte_propre[:2000]
        
        self.var_texte_original.set(f"{texte_clair[:150]}...")
        
        type_attaque = self.combo_attaque.get()
        iterations = int(self.spin_iterations.get())
        
        self.en_cours = True
        self.btn_lancer.state(['disabled'])
        self.x_data.clear()
        self.y_data.clear()
        self.ax.clear()
        self.ax.set_title("Convergence du Log-Score vers le plateau de vraisemblance")
        self.ligne_score, = self.ax.plot([], [], 'b-', linewidth=1, alpha=0.8)
        
        burn_in = int(iterations * 0.15)
        self.ax.axvline(x=burn_in, color='r', linestyle='--', label=f"Fin Chauffe ({burn_in})")
        self.ax.legend()
        
        thread = threading.Thread(target=self.boucle_mcmc, 
                                  args=(texte_clair, type_attaque, iterations, log_stats, n_gram, burn_in))
        thread.daemon = True
        thread.start()

    def boucle_mcmc(self, texte_clair, type_attaque, iterations, log_stats, n_gram, burn_in):
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
            
        score_courant = calculer_log_score(texte_courant, log_stats, n_gram)
        frequences_visites = {}
        
        for i in range(iterations):
            if "Substitution" in type_attaque:
                cle_voisine = substitution.muter_substitution(cle_courante)
                texte_voisin = substitution.dechiffrer_texte(cryptogramme, cle_voisine)
            else:
                cle_voisine = permutation.muter_permutation(cle_courante)
                texte_voisin = permutation.dechiffrer_permutation(cryptogramme, cle_voisine)
                
            score_voisin = calculer_log_score(texte_voisin, log_stats, n_gram)
            delta = score_voisin - score_courant
            
            if delta > 0 or math.log(random.uniform(0, 1)) < delta:
                cle_courante = cle_voisine
                score_courant = score_voisin
                texte_courant = texte_voisin
                
            if i >= burn_in:
                cle_mem = tuple(cle_courante) if isinstance(cle_courante, list) else cle_courante
                frequences_visites[cle_mem] = frequences_visites.get(cle_mem, 0) + 1
                
            if i % 100 == 0 or i == iterations - 1:
                self.after(0, self.maj_graphique, i, score_courant, texte_courant)
                
        top_cles = sorted(frequences_visites.items(), key=lambda x: x[1], reverse=True)[:3]
        self.after(0, self.terminer_attaque, top_cles, cle_secrete, type_attaque, cryptogramme, texte_clair)

    def maj_graphique(self, iteration, score, texte):
        self.var_texte_courant.set(f"[{iteration}] {texte[:150]}...")
        self.x_data.append(iteration)
        self.y_data.append(score)
        
        self.ligne_score.set_data(self.x_data, self.y_data)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle() 

    def terminer_attaque(self, top_cles, cle_secrete, type_attaque, cryptogramme, texte_clair):
        self.en_cours = False
        self.btn_lancer.state(['!disabled'])
        self.var_texte_courant.set("Attaque terminée ! Consultez le rapport popup pour voir la précision.")
        
        rapport = f"Clé secrète cible : {cle_secrete}\n\n"
        rapport += "TOP 3 DES CLÉS LES PLUS VISITÉES :\n" + "-"*40 + "\n"
        
        for rang, (cle, visites) in enumerate(top_cles, 1):
            if "Permutation" in type_attaque:
                cle = list(cle)
                texte_dechiffre = permutation.dechiffrer_permutation(cryptogramme, cle)
            else:
                texte_dechiffre = substitution.dechiffrer_texte(cryptogramme, cle)

            exactes = sum(1 for a, b in zip(cle_secrete, cle) if a == b)
            total = len(cle_secrete)
            
            rapport += f"#{rang} | Visites : {visites} | Précision : {exactes}/{total}\n"
            rapport += f"Clé : {cle}\n"
            rapport += f"Texte original : {texte_clair[:80]}...\n"
            rapport += f"Texte trouvé   : {texte_dechiffre[:80]}...\n\n"
            
        messagebox.showinfo("Rapport d'Analyse MCMC", rapport)

if __name__ == "__main__":
    app = ApplicationMCMC()
    app.mainloop()