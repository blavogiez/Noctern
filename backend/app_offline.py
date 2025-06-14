import gradio as gr
import subprocess
import tempfile
import os
import requests

# ----------- FONCTIONS PRINCIPALES -----------

def compiler_latex(code):
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "main.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_path],
                cwd=tmpdir, check=True, timeout=10, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            return "✅ Compilation réussie"
        except subprocess.CalledProcessError:
            log_path = os.path.join(tmpdir, "main.log")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="ignore") as log_file:
                    last_lines = log_file.readlines()[-20:]
                    return "❌ Erreurs de compilation :\n\n" + "".join(last_lines)
            return "❌ Erreur de compilation inconnue."

def corriger_par_llm(code):
    prompt = f"Corrige ce code LaTeX s'il y a une erreur :\n\n{code}\n\nRetourne uniquement le code corrigé."

    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        })

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            return f"❌ Erreur LLM : statut {response.status_code}"
    except Exception as e:
        return f"❌ Erreur lors de la requête à Ollama : {e}"

# ----------- INTERFACE GRADIO -----------

with gr.Blocks(title="AutomaTeX - Editeur IA") as demo:
    gr.Markdown("## 🧠 AutomaTeX : Éditeur LaTeX avec IA locale")

    code_input = gr.Textbox(
        lines=20,
        label="Code LaTeX",
        value="\\documentclass{article}\n\\begin{document}\nBonjour\n\\end{document}"
    )

    output = gr.Textbox(label="Résultat ou Correction IA", lines=15)

    with gr.Row():
        btn_compile = gr.Button("📄 Compiler")
        btn_corriger = gr.Button("💡 Corriger avec IA")

    btn_compile.click(fn=compiler_latex, inputs=code_input, outputs=output)
    btn_corriger.click(fn=corriger_par_llm, inputs=code_input, outputs=output)

# Lance l'app localement
if __name__ == "__main__":
    demo.launch(inbrowser=True, server_name="127.0.0.1", server_port=7860)
