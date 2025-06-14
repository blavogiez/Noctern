import gradio as gr
import requests

# Charger le contenu HTML de Monaco Editor depuis le fichier
with open("../frontend/editor.html", encoding="utf-8") as f:
    monaco_html = f.read()

# Appelle l’API FastAPI en local
def completer_phrase(_):
    try:
        # JS : récupérer le contenu avec window.getEditorContent()
        editor_content = gr.get_js("getEditorContent")()
        editor_iframe = gr.HTML('<iframe src="http://localhost:8888/editor.html" width="100%" height="600px" frameborder="0"></iframe>')
        response = requests.post("http://localhost:8000/complete", json={"code": editor_content})
        if response.status_code == 200:
            completion = response.json().get("completion", "").strip()
            gr.eval_js(f"insertCompletion({repr(completion)})")
            return "✅ Complétion insérée"
        else:
            return f"❌ Erreur LLM : statut {response.status_code}"
    except Exception as e:
        return f"❌ Erreur : {e}"

with gr.Blocks(title="AutomaTeX - Gradio + Monaco") as demo:
    gr.Markdown("## ✍️ AutomaTeX (Ctrl+Shift+C pour compléter une phrase)")
    gr.HTML(monaco_html)
    complete_btn = gr.Button("🔮 Compléter", elem_id="btn-complete", visible=False)
    output = gr.Textbox(label="État", lines=1)

    complete_btn.click(fn=completer_phrase, inputs=[], outputs=output)

if __name__ == "__main__":
    demo.launch(inbrowser=True)
