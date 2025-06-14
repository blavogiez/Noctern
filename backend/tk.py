import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import os
import webbrowser

def compiler_latex():
    code = editor.get("1.0", tk.END)

    # Créer un répertoire temporaire de travail
    os.makedirs("output", exist_ok=True)
    tex_path = os.path.join("output", "main.tex")
    
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(code)

    # Lancer la compilation avec pdflatex
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
            # Ouvrir le PDF avec le lecteur par défaut
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

# ---- Interface graphique
root = tk.Tk()
root.title("Éditeur LaTeX avec Compilation")

editor = tk.Text(root, wrap="word", font=("Courier New", 12))
editor.pack(fill="both", expand=True)

# Exemple LaTeX par défaut
editor.insert("1.0", r"""\documentclass{article}
\begin{document}
Bonjour \LaTeX !
\end{document}
""")

btn_compile = tk.Button(root, text="🛠️ Compiler avec pdflatex", command=compiler_latex)
btn_compile.pack(fill="x")

root.mainloop()
