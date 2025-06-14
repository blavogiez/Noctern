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
    prompt = f"Complète intelligemment ce code LaTeX :\n\n{req.code.strip()}\n\nSuite probable :"

    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        })

        if response.status_code == 200:
            return {"completion": response.json().get("response", "").strip()}
        else:
            return {"completion": f"❌ Erreur LLM : statut {response.status_code}"}
    except Exception as e:
        return {"completion": f"❌ Erreur : {str(e)}"}
