import streamlit as st
import streamlit.components.v1 as components

with open("../frontend/index.html", "r", encoding="utf-8") as f:
    html = f.read()

st.subheader("🧠 Éditeur LaTeX")
components.html(html, height=500)

latex_code = st.text_area("Contenu LaTeX récupéré", "", key="latex_code")

if st.button("📄 Compiler en PDF"):
    with open("../output/main.tex", "w", encoding="utf-8") as f:
        f.write(latex_code)

    import subprocess, os
    os.makedirs("output", exist_ok=True)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"], cwd="output")

    with open("../output/main.pdf", "rb") as f:
        st.download_button("📥 Télécharger PDF", f, file_name="document.pdf", mime="application/pdf")
