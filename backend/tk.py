import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
from pdf2image import convert_from_path
import requests
import subprocess
import os
import webbrowser

### LaTeX logics

## Fonction de compilation LaTeX
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
            afficher_pdf("output/main.pdf")
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

## Fonction pour afficher un PDF converti en image
def afficher_pdf(pdf_path):
    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=1)
        if images:
            img = images[0]
            img = img.resize((600, int(600 * img.height / img.width)), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            pdf_preview.config(image=photo)
            pdf_preview.image = photo
    except Exception as e:
        messagebox.showerror("Erreur d'affichage PDF", str(e))
        
### LLM Text Logic (Context, completion, generation...)

# Getting the context from as many lines as we wish (backward or forward)
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

    print("\n".join(context_lines))
    return "\n".join(context_lines)

# Sentence completion
def complete_sentence():
    contexte = get_contexte(nb_lines_backwards=30, nb_lines_forwards=0)

    last_dot_index = contexte.rfind(".")
    if last_dot_index == -1:
        phrase_en_cours = contexte.strip()
        contexte_anterieur = ""
    else:
        phrase_en_cours = contexte[last_dot_index + 1:].strip()
        contexte_anterieur = contexte[:last_dot_index + 1].strip()

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
        
# Merging the two lines together as to not repeat the same start
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
        
# Text generation from prompt box
def generer_texte_depuis_prompt():
    user_rq = simpledialog.askstring("Prompt IA", "Entrez une instruction ou un prompt :")
    if not user_rq :
        return  # Annulé
    
    prompt = f"Répond dans la langue du prompt, de façon claire et concise : \n{user_rq}"
    
    print(prompt)
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "llama2",
            "prompt": prompt,
            "stream": False
        })

        if response.status_code == 200:
            result = response.json().get("response", "").strip()
            editor.insert(tk.INSERT, result)
        else:
            messagebox.showerror("Erreur LLM", f"Statut : {response.status_code}")
    except Exception as e:
        messagebox.showerror("Erreur connexion", str(e))

# ---- Interface graphique
root = tk.Tk()
root.title("AutomaTeX")

# Diviser la fenêtre principale horizontalement
main_frame = tk.PanedWindow(root, orient=tk.HORIZONTAL)
main_frame.pack(fill="both", expand=True)

# Éditeur LaTeX à gauche
editor = tk.Text(main_frame, wrap="word", font=("Courier New", 12))
main_frame.add(editor)

# Prévisualisation PDF à droite
pdf_frame = tk.Frame(main_frame, width=400, bg="white")
pdf_preview = tk.Label(pdf_frame, bg="white")
pdf_preview.pack(fill="both", expand=True)
main_frame.add(pdf_frame)

# Charger un exemple LaTeX
try:
    with open("res/auguste_renoir.tex", "r", encoding="utf-8") as f:
        content = f.read()
        editor.insert("1.0", content)
except Exception as e:
    messagebox.showerror("Erreur", f"Impossible de charger le fichier Auguste Renoir : {e}")

# Bouton de compilation
btn_compile = tk.Button(root, text="🛠️ Compiler avec pdflatex", command=compiler_latex)
btn_compile.pack(fill="x")

# Bindings
root.bind_all("<Control-Shift-G>", lambda event: generer_texte_depuis_prompt())
root.bind_all("<Control-Shift-C>", lambda event: complete_sentence())

root.mainloop()
