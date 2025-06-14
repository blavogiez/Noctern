from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

# Autoriser le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ pour dev uniquement
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str

@app.post("/complete")
def complete_code(req: CodeRequest):
    # Texte complet reçu
    full_text = req.code.strip()

    # Extraire la phrase en cours depuis le dernier point (ou tout le texte s'il n'y a pas de point)
    last_dot_index = full_text.rfind(".")
    if last_dot_index == -1:
        phrase_en_cours = full_text
    else:
        phrase_en_cours = full_text[last_dot_index+1:].strip()

    # Préparer prompt avec la phrase en cours uniquement
    prompt = (
        "Complète uniquement la phrase entre guillemets, sans répéter ni inclure de code LaTeX ou autre texte. "
        "Il ne doit y avoir aucun code LaTeX, juste une phrase normale :\n\n"
        f"\"{phrase_en_cours}\"\n\n"
        "Complétion courte et naturelle :"
    )

    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        })

        if response.status_code == 200:
            completion_raw = response.json().get("response", "").strip()

            # Enlever si la complétion renvoie aussi la phrase_en_cours
            if completion_raw.startswith(phrase_en_cours):
                completion_clean = completion_raw[len(phrase_en_cours):].strip()
            else:
                completion_clean = completion_raw

            return {"completion": completion_clean}
        else:
            return {"completion": f"❌ Erreur LLM : statut {response.status_code}"}
    except Exception as e:
        return {"completion": f"❌ Erreur : {str(e)}"}
