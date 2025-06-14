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
    
def remove_redundant_overlap(start: str, completion: str) -> str:
    # Normalisation simple (minuscules, suppression des espaces multiples)
    import re
    start_words = re.sub(r'\s+', ' ', start.strip().lower()).split()
    completion_words = re.sub(r'\s+', ' ', completion.strip().lower()).split()

    max_overlap = 0
    for i in range(1, min(len(start_words), len(completion_words)) + 1):
        if start_words[-i:] == completion_words[:i]:
            max_overlap = i

    if max_overlap > 0:
        overlap_text = ' '.join(completion.split()[:max_overlap])
        return completion[len(overlap_text):].lstrip()
    return completion


@app.post("/complete")
def complete_code(req: CodeRequest):
    full_text = req.code.strip()

    # Séparer en lignes
    lines = full_text.splitlines()

    # Récupérer les 10 dernières lignes (ou moins)
    last_30_lines = lines[-30:] if len(lines) >= 30 else lines
    contexte_anterieur = "\n".join(last_30_lines)

    # Trouver le dernier point dans ce contexte
    last_dot_index = contexte_anterieur.rfind(".")
    if last_dot_index == -1:
        phrase_en_cours = contexte_anterieur.strip()
        contexte_anterieur = ""  # pas de phrase avant
    else:
        phrase_en_cours = contexte_anterieur[last_dot_index + 1 :].strip()
        contexte_anterieur = contexte_anterieur[:last_dot_index + 1].strip()  # tout avant le dernier point, inclus

    print(f"Contexte antérieur :\n{contexte_anterieur}")
    print(f"Phrase en cours :\n{phrase_en_cours}")

    prompt = (
    "Complète uniquement la phrase en cours, sans reformuler le contexte ni inclure de balises ou de code. Garde la même langue."
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
            completion_raw = response.json().get("response", "").strip()

            # Nettoyer les guillemets si présents
            if completion_raw.startswith('"') and completion_raw.endswith('"'):
                completion_raw = completion_raw[1:-1].strip()

            # Supprimer doublons
            completion_clean = remove_redundant_overlap(phrase_en_cours, completion_raw)

            return {"completion": completion_clean}
        else:
            return {"completion": f"❌ Erreur LLM : statut {response.status_code}"}
    except Exception as e:
        return {"completion": f"❌ Erreur : {str(e)}"}