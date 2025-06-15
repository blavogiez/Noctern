import tkinter as tk
from tkinter import messagebox, filedialog
import requests
import subprocess
import os
import webbrowser
import re

# Fonction pour nettoyer le chevauchement redondant
def remove_redundant_overlap(start: str, completion: str) -> str:
    # Nettoyage doux pour la détection de chevauchement uniquement
    start_words = start.split()
    completion_words = completion.split()
    
    clean_completion = ""
    for word_index in range (len(completion_words)) :
        if (word_index < len(start_words) - 1) :
            if (start_words[word_index] == completion_words[word_index]) :
                # Word is the same, don't add it as already present
                continue 
        else :
            clean_completion += completion_words[word_index] + " "
    
    return clean_completion

# Fonction de compilation LaTeX
def compiler_latex():
    code = editor.get("1.0", tk.END)

    os.makedirs("output", exist_ok=True)
    tex_path = os.path.join("output", "main.tex")
    
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "main.tex"],
            cwd="output",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )

        if result.returncode == 0:
            messagebox.showinfo("✅ Succès", "Compilation LaTeX réussie.")
            pdf_path = os.path.abspath("output/main.pdf")
            webbrowser.open_new(pdf_path)
        else:
            log = result.stdout.decode("utf-8", errors="ignore")
            messagebox.showerror("❌ Erreur LaTeX", "Erreur de compilation. Voir les logs.")
            log_window = tk.Toplevel(root)
            log_window.title("Log de Compilation")
            tk.Text(log_window, wrap="word", height=30, width=100).insert("1.0", log).pack()

    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")

# Fonction de complétion IA
def complete_sentence():
    full_text = editor.get("1.0", tk.END).strip()

    lines = full_text.splitlines()
    last_30_lines = lines[-30:] if len(lines) >= 30 else lines
    contexte_anterieur = "\n".join(last_30_lines)

    last_dot_index = contexte_anterieur.rfind(".")
    if last_dot_index == -1:
        phrase_en_cours = contexte_anterieur.strip()
        contexte_anterieur = ""
    else:
        phrase_en_cours = contexte_anterieur[last_dot_index + 1:].strip()
        contexte_anterieur = contexte_anterieur[:last_dot_index + 1].strip()

    prompt = (
        "Complète uniquement la phrase en cours, sans reformuler le contexte ni inclure de balises ou de code. Garde la même langue. "
        "Le début doit strictement être identique au début de la phrase actuelle."
        "Réponds uniquement avec une phrase naturelle, fluide et cohérente. "
        "Ne commence pas une nouvelle idée ou paragraphe : reste dans la continuité logique du texte.\n\n"
        f"Contexte (30 lignes précédentes) :\n\"{contexte_anterieur}\"\n\n"
        f"Début de la phrase à compléter :\n\"{phrase_en_cours}\"\n\n"
        "Complétion attendue (courte et naturelle, pas de ponctuation finale si elle est déjà commencée) :"
    )

    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "llama2",
            "prompt": prompt,
            "stream": False
        })

        if response.status_code == 200:
            completion_raw = response.json().get("response", "").strip().strip('"')
            cleaned_completion = remove_redundant_overlap(phrase_en_cours, completion_raw)
            editor.insert(tk.INSERT, cleaned_completion)
        else:
            messagebox.showerror("Erreur LLM", f"Statut : {response.status_code}")
    except Exception as e:
        messagebox.showerror("Erreur connexion", str(e))

# ---- Interface graphique
root = tk.Tk()
root.title("AutomaTeX")

editor = tk.Text(root, wrap="word", font=("Courier New", 12))
editor.pack(fill="both", expand=True)

# Exemple LaTeX par défaut
try:
    with open("res/auguste_renoir.tex", "r", encoding="utf-8") as f:
        content = f.read()
        editor.insert("1.0", content)
except Exception as e:
    messagebox.showerror("Erreur", f"Impossible de charger le fichier Auguste Renoir : {e}")


# Bouton de compilation
btn_compile = tk.Button(root, text="🛠️ Compiler avec pdflatex", command=compiler_latex)
btn_compile.pack(fill="x")

# Raccourci clavier pour auto-complétion IA
root.bind_all("<Control-Shift-C>", lambda event: complete_sentence())

root.mainloop()
