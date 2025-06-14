# main.py
from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import tempfile
import os

# Si tu veux utiliser OpenAI :
import openai

# Tu peux remplacer cette fonction par un appel à un LLM local si besoin

class CodeInput(BaseModel):
    code: str

# Compilation LaTeX avec pdflatex
def compile_latex(data: CodeInput):
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = os.path.join(tmpdir, "main.tex")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(data.code)

        try:
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=True,
                text=True
            )
            return {"result": "✅ Compilation réussie"}
        except subprocess.CalledProcessError as e:
            log_path = os.path.join(tmpdir, "main.log")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as log:
                    return {"error": log.read()[-1500:]}  # dernières lignes du log
            return {"error": e.stderr or "❌ Erreur de compilation inconnue"}

# Correction avec LLM
def resolve_error(data: CodeInput):
    prompt = (
        "Corrige ce code LaTeX s'il contient des erreurs. "
        "Retourne uniquement la version corrigée sans explication :\n\n"
        f"{data.code}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # ou "gpt-3.5-turbo"
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        corrected = response.choices[0].message.content.strip()
        return {"suggestion": corrected}
    except Exception as e:
        return {"suggestion": f"❌ Erreur lors de l'appel à l'IA : {e}"}
