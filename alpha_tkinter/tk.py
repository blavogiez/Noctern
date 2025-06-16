import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter.font import Font
from PIL import Image, ImageTk
from pdf2image import convert_from_path
import requests
import subprocess
import os
import webbrowser
import platform

### --- LaTeX COMPILATION LOGIC --- ###

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

        prompt = f"""Tu es un modèle de génération de texte. Voici un prompt utilisateur :
"{prompt_user}"

Voici le contexte autour du curseur :
"{contexte}"

N'inclus absolument pas de texte autre que la réponse. Donne juste la réponse, sans autre message.
Réponds de manière concise et naturelle, en respectant strictement la langue du prompt et du contexte.
"""

        try:
            response = requests.post("http://localhost:11434/api/generate", json={
                "model": "llama2",
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


### --- INTERFACE MODERNE --- ###

def setup_interface():
    root = tk.Tk()
    root.title("🧠 AutomaTeX")
    root.geometry("1200x700")
    root.configure(bg="#f5f5f5")

    style = ttk.Style()
    style.theme_use("clam")

    font_editor = Font(family="Fira Code", size=12)

    top_frame = ttk.Frame(root, padding=5)
    top_frame.pack(fill="x")

    btn_compile = ttk.Button(top_frame, text="🛠️ Compiler LaTeX", command=compiler_latex)
    btn_compile.pack(side="left", padx=5)

    btn_completion = ttk.Button(top_frame, text="✨ Compléter (Ctrl+Shift+C)", command=complete_sentence)
    btn_completion.pack(side="left", padx=5)

    btn_prompt = ttk.Button(top_frame, text="🎯 Génération IA (Ctrl+Shift+G)", command=generer_texte_depuis_prompt)
    btn_prompt.pack(side="left", padx=5)

    main_frame = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashrelief="raised", bg="#e0e0e0")
    main_frame.pack(fill="both", expand=True)

    editor_frame = ttk.Frame(main_frame)
    global editor
    editor = tk.Text(editor_frame, wrap="word", font=font_editor, undo=True, bg="#ffffff", fg="#333333")
    editor.pack(fill="both", expand=True, padx=2, pady=2)
    main_frame.add(editor_frame, stretch="always")

    pdf_frame = ttk.Frame(main_frame)
    global pdf_preview
    pdf_preview = tk.Label(pdf_frame, background="white")
    pdf_preview.pack(fill="both", expand=True)
    main_frame.add(pdf_frame, width=450)

    try:
        with open("res/res.txt", "r", encoding="utf-8") as f:
            content = f.read()
            editor.insert("1.0", content)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de charger le fichier exemple : {e}")

    root.bind_all("<Control-Shift-G>", lambda event: generer_texte_depuis_prompt())
    root.bind_all("<Control-Shift-C>", lambda event: complete_sentence())

    return root


### --- MAIN EXECUTION --- ###
if __name__ == "__main__":
    root = setup_interface()
    root.mainloop()
