#### AutomaTeX, a LaTeX editor powered by AI Tools
#### Baptiste Lavogiez, June 2025

#### https://github.com/blavogiez/AutomaTeX

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.font import Font
import requests
import subprocess
import os
import webbrowser
import platform
import threading
import re

fichier_actuel = None  # ⬅️ Pour suivre le fichier ouvert

### --- Editor logic --- ###

## -- Navigating through TeX sections -- ##

def update_outline():
    tree.delete(*tree.get_children())
    lines = editor.get("1.0", tk.END).split("\n")
    parents = {0: ""}
    for i, line in enumerate(lines):
        for level, cmd in enumerate(["section", "subsection", "subsubsection"], 1):
            match = re.match(rf"\\{cmd}{{(.*?)}}", line.strip())
            if match:
                title = match.group(1)
                node_id = tree.insert(parents[level - 1], "end", text=title, values=(i + 1,))
                parents[level] = node_id
                # Supprimer les descendants si on remonte dans la hiérarchie
                for deeper in range(level + 1, 4):
                    if deeper in parents:
                        del parents[deeper]
                break
            
def aller_a_section(event):
    selected = tree.selection()
    if selected:
        ligne = tree.item(selected[0], "values")[0]
        editor.mark_set("insert", f"{ligne}.0")
        editor.see(f"{ligne}.0")
        editor.focus()


## -- Syntax highlighting -- ##

def highlight_syntax(event=None):
    content = editor.get("1.0", tk.END)
    editor.tag_remove("latex_command", "1.0", tk.END)
    editor.tag_remove("latex_brace", "1.0", tk.END)
    editor.tag_remove("latex_comment", "1.0", tk.END)

    for match in re.finditer(r"\\[a-zA-Z@]+", content):
        start = f"1.0 + {match.start()} chars"
        end = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_command", start, end)

    for match in re.finditer(r"[{}]", content):
        start = f"1.0 + {match.start()} chars"
        end = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_brace", start, end)

    for match in re.finditer(r"%[^\n]*", content):
        start = f"1.0 + {match.start()} chars"
        end = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_comment", start, end)


### --- LaTeX COMPILATION LOGIC --- ###
        
## -- Subprocess command to check syntax errors (chktex)
        
def verifier_chktex():
    global fichier_actuel
    code = editor.get("1.0", tk.END)

    # Fichier temporaire si aucun fichier actuel
    if fichier_actuel:
        tex_path = fichier_actuel
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(code)
    else:
        os.makedirs("output", exist_ok=True)
        tex_path = os.path.join("output", "temp_chktex.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(code)

    try:
        result = subprocess.run(
            ["chktex", "-q", "-l", "-v0-2", tex_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8"
        )

        output = result.stdout.strip()
        if not output:
            messagebox.showinfo("✅ chkTeX", "Aucune erreur critique trouvée.")
        else:
            fenetre = tk.Toplevel(root)
            fenetre.title("chkTeX - Erreurs critiques")
            text_box = tk.Text(fenetre, wrap="word", height=25, width=100)
            text_box.insert("1.0", output)
            text_box.config(state="disabled")
            text_box.pack(padx=10, pady=10)
    except FileNotFoundError:
        messagebox.showerror("Erreur", "chktex n’est pas installé ou introuvable dans le PATH.")
    except Exception as e:
        messagebox.showerror("Erreur chkTeX", str(e))


## -- Subprocess command to compile -- ##
        
def compiler_latex():
    global fichier_actuel
    code = editor.get("1.0", tk.END)

    if fichier_actuel:
        dossier_source = os.path.dirname(fichier_actuel)
        nom_fichier = os.path.basename(fichier_actuel)
        with open(fichier_actuel, "w", encoding="utf-8") as f:
            f.write(code)
    else:
        dossier_source = "output"
        os.makedirs(dossier_source, exist_ok=True)
        fichier_actuel = os.path.join(dossier_source, "main.tex")
        nom_fichier = "main.tex"
        with open(fichier_actuel, "w", encoding="utf-8") as f:
            f.write(code)

    try:
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", nom_fichier],
            cwd=dossier_source,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )

        pdf_path = os.path.join(dossier_source, nom_fichier.replace(".tex", ".pdf"))

        if result.returncode == 0:
            messagebox.showinfo("✅ Succès", "Compilation LaTeX réussie.")
            afficher_pdf(pdf_path)
        else:
            log = result.stdout.decode("utf-8", errors="ignore")
            messagebox.showerror("❌ Erreur LaTeX", "Erreur de compilation. Voir les logs.")
            log_window = tk.Toplevel(root)
            log_window.title("Log de Compilation")
            log_text = tk.Text(log_window, wrap="word", height=30, width=100)
            log_text.insert("1.0", log)
            log_text.pack()
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")

## -- Opening the PDF if generated (likely using SumatraPDF) -- ##
        
def afficher_pdf(pdf_path):
    try:
        if not os.path.exists(pdf_path):
            messagebox.showerror("Erreur", f"Le fichier PDF est introuvable :\n{pdf_path}")
            return

        lecteur_pdf = r"pdf_reader/SumatraPDF.exe"
        if not os.path.exists(lecteur_pdf):
            messagebox.showerror("Erreur", f"Lecteur PDF introuvable :\n{lecteur_pdf}")
            return

        subprocess.Popen([lecteur_pdf, pdf_path])
    except Exception as e:
        messagebox.showerror("Erreur ouverture PDF", str(e))

## -- When opening PDF File, resize the two windows on an equal size -- ##
        
### --- FONCTIONS FICHIER --- ###

def ouvrir_fichier():
    global fichier_actuel
    filepath = filedialog.askopenfilename(
        title="Ouvrir un fichier",
        filetypes=[("Fichiers LaTeX", "*.tex"), ("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
    )
    if filepath:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                contenu = f.read()
                editor.delete("1.0", tk.END)
                editor.insert("1.0", contenu)
                highlight_syntax()
                update_outline()
            fichier_actuel = filepath
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d’ouvrir le fichier : {e}")

def enregistrer_fichier():
    global fichier_actuel
    if fichier_actuel:
        try:
            contenu = editor.get("1.0", tk.END)
            with open(fichier_actuel, "w", encoding="utf-8") as f:
                f.write(contenu)
            messagebox.showinfo("Succès", f"Fichier enregistré :\n{fichier_actuel}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l’enregistrement : {e}")
    else:
        fichier_actuel = filedialog.asksaveasfilename(
            defaultextension=".tex",
            filetypes=[("Fichiers LaTeX", "*.tex"), ("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
            title="Enregistrer le fichier"
        )
        if fichier_actuel:
            enregistrer_fichier()


### --- LLM TEXT LOGIC --- ###

def get_contexte(nb_lines_backwards=5, nb_lines_forwards=5):
    cursor_index = editor.index(tk.INSERT)
    line_index = int(cursor_index.split(".")[0])
    total_lines = int(editor.index("end-1c").split(".")[0])

    start_line = max(1, line_index - nb_lines_backwards)
    end_line = min(total_lines, line_index + nb_lines_forwards)

    context_lines = []
    for i in range(start_line, end_line + 1):
        line_text = editor.get(f"{i}.0", f"{i}.end")
        context_lines.append(line_text)

    return "\n".join(context_lines)

def complete_sentence():
    def run_completion():
        try:
            contexte = get_contexte(nb_lines_backwards=30, nb_lines_forwards=0)

            last_dot_index = contexte.rfind(".")
            if last_dot_index == -1:
                phrase_en_cours = contexte.strip()
                contexte_anterieur = ""
            else:
                phrase_en_cours = contexte[last_dot_index + 1:].strip()
                contexte_anterieur = contexte[:last_dot_index + 1].strip()

            prompt = (
                "Complète uniquement la phrase en cours, sans reformuler le contexte ni inclure de balises ou de code. "
                "Garde la même langue. Le début doit strictement être identique au début de la phrase actuelle. "
                "Réponds uniquement avec une phrase naturelle, fluide et cohérente. "
                "Ne commence pas une nouvelle idée ou paragraphe : reste dans la continuité logique du texte.\n\n"
                f"Contexte (30 lignes précédentes) :\n\"{contexte_anterieur}\"\n\n"
                f"Début de la phrase à compléter :\n\"{phrase_en_cours}\"\n\n"
                "Complétion attendue (courte et naturelle, pas de ponctuation finale si elle est déjà commencée) :"
            )

            response = requests.post("http://localhost:11434/api/generate", json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            })

            if response.status_code == 200:
                completion_raw = response.json().get("response", "").strip().strip('"')
                cleaned_completion = remove_redundant_overlap(phrase_en_cours, completion_raw)
                editor.after(0, lambda: editor.insert(tk.INSERT, cleaned_completion))
            else:
                editor.after(0, lambda: messagebox.showerror("Erreur LLM", f"Statut : {response.status_code}"))
        except Exception as e:
            editor.after(0, lambda: messagebox.showerror("Erreur connexion", str(e)))
        finally:
            editor.after(0, lambda: progress_bar.pack_forget())
            editor.after(0, lambda: progress_bar.stop())

    progress_bar.pack(pady=2)
    progress_bar.start(10)

    threading.Thread(target=run_completion, daemon=True).start()

def remove_redundant_overlap(start: str, completion: str) -> str:
    start_words = start.split()
    completion_words = completion.split()

    clean_completion = ""
    for word_index in range(len(completion_words)):
        if word_index < len(start_words) - 1:
            if start_words[word_index] == completion_words[word_index]:
                continue
        clean_completion += completion_words[word_index] + " "
    
    return clean_completion.strip()

def generer_texte_depuis_prompt():
    fenetre = tk.Toplevel(root)
    fenetre.title("Génération IA personnalisée")

    tk.Label(fenetre, text="Prompt :").grid(row=0, column=0, sticky="w")
    entry_prompt = tk.Entry(fenetre, width=60)
    entry_prompt.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(fenetre, text="Lignes avant :").grid(row=1, column=0, sticky="w")
    entry_back = tk.Entry(fenetre, width=10)
    entry_back.insert(0, "5")
    entry_back.grid(row=1, column=1, sticky="w")

    tk.Label(fenetre, text="Lignes après :").grid(row=2, column=0, sticky="w")
    entry_forward = tk.Entry(fenetre, width=10)
    entry_forward.insert(0, "0")
    entry_forward.grid(row=2, column=1, sticky="w")

    def envoyer_prompt():
        prompt_user = entry_prompt.get().strip()
        try:
            nb_back = int(entry_back.get())
            nb_forward = int(entry_forward.get())
        except ValueError:
            messagebox.showerror("Erreur", "Les champs de lignes doivent être des entiers.")
            return

        if not prompt_user:
            messagebox.showwarning("Attention", "Le prompt est vide.")
            return

        contexte = get_contexte(nb_back, nb_forward)

        prompt = f"""Tu es un assistant d'écriture intelligent. Un utilisateur t’a donné une consigne pour générer du texte à insérer dans un document.

        Contrainte principale : réponds uniquement avec la génération demandée, sans préambule, signature, explication ou reformulation de la consigne.

        Langue : exclusivement en français, registre soutenu mais naturel. Le ton doit rester cohérent avec le contexte fourni.

        Prompt utilisateur :
        "{prompt_user}"

        Contexte autour du curseur :
        \"\"\"{contexte}\"\"\"

        Instructions :
        - Ne modifie pas le contexte.
        - Génère uniquement le texte correspondant à la consigne.
        - Respecte la continuité logique et thématique du texte.
        - Ta réponse doit s’insérer de manière fluide dans le contenu existant.

        Texte à insérer :
        """


        try:
            response = requests.post("http://localhost:11434/api/generate", json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            })

            if response.status_code == 200:
                result = response.json().get("response").strip()
                editor.insert(tk.INSERT, result)
                fenetre.destroy()
            else:
                messagebox.showerror("Erreur LLM", f"Statut : {response.status_code}")
        except Exception as e:
            messagebox.showerror("Erreur connexion", str(e))

    tk.Button(fenetre, text="Générer", command=envoyer_prompt).grid(row=3, column=0, columnspan=2, pady=10)
    entry_prompt.focus()
    
### --- INTERFACE --- ###

def setup_interface():
    global editor, root, tree, progress_bar
    root = tk.Tk()
    root.title("AutomaTeX v1.0")
    root.geometry("1920x1080")
    root.configure(bg="#f5f5f5")
    root.iconbitmap("res/automatex.ico")  # ← Assure-toi que automatex.ico est dans le même dossier

    style = ttk.Style()
    style.theme_use("clam")

    font_editor = Font(family="Consolas", size=12)

    # --- Top Buttons ---
    top_frame = ttk.Frame(root, padding=5)
    top_frame.pack(fill="x")

    ttk.Button(top_frame, text="🛠 Compiler", command=compiler_latex).pack(side="left", padx=5)
    ttk.Button(top_frame, text="✨ Compléter (Ctrl+Shift+C)", command=complete_sentence).pack(side="left", padx=5)
    ttk.Button(top_frame, text="🎯 Génération texte (Ctrl+Shift+G)", command=generer_texte_depuis_prompt).pack(side="left", padx=5)
    ttk.Button(top_frame, text="📋 Debug syntaxe (Ctrl+Shift+D)", command=verifier_chktex).pack(side="left", padx=5)
    ttk.Button(top_frame, text="🌓 Thème", command=lambda: appliquer_theme("sombre" if current_theme == "clair" else "clair")).pack(side="right", padx=5)

    # --- Main Pane ---
    main_frame = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief="raised", bg="#e0e0e0")
    main_frame.pack(fill="both", expand=True)

    # --- Left Tree Navigation ---
    tree_frame = ttk.Frame(main_frame)
    tree = ttk.Treeview(tree_frame, show="tree")
    tree.pack(fill="both", expand=True)
    tree.bind("<<TreeviewSelect>>", aller_a_section)
    main_frame.add(tree_frame, width=250)

    # --- Text Editor ---
    editor_frame = ttk.Frame(main_frame)
    editor = tk.Text(editor_frame, wrap="word", font=font_editor, undo=True, bg="#ffffff", fg="#333333")
    editor.pack(fill="both", expand=True, padx=2, pady=2)
    main_frame.add(editor_frame, stretch="always")

    # --- Line numbers
    
    # --- Syntax Highlighting Tags ---
    editor.tag_configure("latex_command", foreground="#005cc5", font=font_editor)
    editor.tag_configure("latex_brace", foreground="#d73a49", font=font_editor)
    editor.tag_configure("latex_comment", foreground="#6a737d", font=font_editor.copy().configure(slant="italic"))

    # --- GPU Usage ---
    global progress_bar
    progress_bar = ttk.Progressbar(root, mode="indeterminate", length=200)
    progress_bar.pack(pady=2)
    progress_bar.pack_forget()  # On la cache par défaut
    
    status_bar = ttk.Label(root, text="⏳ Initialisation GPU...", anchor="w", relief="sunken", padding=4)
    status_bar.pack(side="bottom", fill="x")

    def update_gpu_status():
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu", "--format=csv,noheader,nounits"],
                encoding="utf-8"
            ).strip()

            name, temp, usage = output.split(", ")
            status_text = f"🎮 GPU: {name}   🌡 {temp}°C   📊 {usage}% utilisé"
        except Exception as e:
            status_text = f"⚠️ GPU non détecté ({str(e)})"

        status_bar.config(text=status_text)
        root.after(333, update_gpu_status)  # met à jour toutes les 1/3 secondes

    update_gpu_status()
    
    # --- Events ---
    #editor.bind("<KeyRelease>", lambda e: (highlight_syntax(), update_outline()))

    root.bind_all("<Control-Shift-G>", lambda event: generer_texte_depuis_prompt())
    root.bind_all("<Control-Shift-C>", lambda event: complete_sentence())
    root.bind_all("<Control-Shift-D>", lambda event: verifier_chktex())
    root.bind_all("<Control-o>", lambda event: ouvrir_fichier())
    root.bind_all("<Control-s>", lambda event: enregistrer_fichier())
    
    appliquer_theme("sombre")  # ou "sombre" si tu veux le mode dark par défaut
    
    # Update widgets (syntax, treeview)
        # Timer pour limiter les updates lourds
    update_timer = {"id": None}

    def delayed_update(_=None):
        if update_timer["id"] is not None:
            root.after_cancel(update_timer["id"])
        update_timer["id"] = root.after(2000, lambda: (highlight_syntax(), update_outline()))

    # Déclenche uniquement sur des touches significatives
    def on_key_release(event):
        if event.keysym in ["Return", "space", "Tab", "BackSpace"]:
            delayed_update()
        elif event.char in "{}[]();,.":  # ponctuation clé
            delayed_update()
    editor.bind("<KeyRelease>", on_key_release)
    return root

current_theme = "clair"

def appliquer_theme(theme):
    global current_theme
    current_theme = theme

    style = ttk.Style()
    style.theme_use("clam")

    if theme == "clair":
        root.configure(bg="#f5f5f5")
        bg_color = "#ffffff"
        fg_color = "#000000"
        tree_bg = "#ffffff"
        tree_fg = "#000000"
        sel_bg = "#cce6ff"
        sel_fg = "#000000"
        editor_bg = "#ffffff"
        editor_fg = "#000000"
        comment_color = "#6a737d"
    elif theme == "sombre":
        root.configure(bg="#1e1e1e")
        bg_color = "#2e2e2e"
        fg_color = "#ffffff"
        tree_bg = "#2e2e2e"
        tree_fg = "#ffffff"
        sel_bg = "#44475a"
        sel_fg = "#ffffff"
        editor_bg = "#1e1e1e"
        editor_fg = "#f8f8f2"
        comment_color = "#6272a4"
    else:
        return

    # Appliquer les couleurs au Text (éditeur)
    editor.configure(bg=editor_bg, fg=editor_fg, insertbackground=fg_color, selectbackground=sel_bg, selectforeground=sel_fg)

    # Mettre à jour les tags de syntaxe
    font_editor = Font(family="Consolas", size=12)
    editor.tag_configure("latex_command", foreground="#8be9fd", font=font_editor)
    editor.tag_configure("latex_brace", foreground="#ff79c6", font=font_editor)
    editor.tag_configure("latex_comment", foreground=comment_color, font=font_editor.copy().configure(slant="italic"))

    # Appliquer le style Treeview
    style.configure("Treeview",
                    background=tree_bg,
                    foreground=tree_fg,
                    fieldbackground=tree_bg)
    style.map("Treeview",
              background=[('selected', sel_bg)],
              foreground=[('selected', sel_fg)])

    # Appliquer le style global aux boutons, labels, etc.
    style.configure("TFrame", background=bg_color)
    style.configure("TLabel", background=bg_color, foreground=fg_color)
    style.configure("TButton", background=bg_color, foreground=fg_color)
    style.configure("Horizontal.TProgressbar", troughcolor=bg_color, background=sel_bg)

    # Rafraîchir la barre d’état si elle existe
    for widget in root.winfo_children():
        if isinstance(widget, ttk.Label):
            widget.configure(background=bg_color, foreground=fg_color)


### --- MAIN --- ###

if __name__ == "__main__":
    root = setup_interface()
    root.mainloop()
