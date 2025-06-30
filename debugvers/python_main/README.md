# Application Requirements

## Operating System

- Windows only

## Required Dependencies

### 1. Ollama (Local command-line LLMs)

To use local language models via Ollama:

- After installing Ollama, add the `ollama.exe` executable to your system's **PATH** environment variable.
- To download a model, run the following command in your terminal: `ollama pull <model_name>`

- Notes:
- Model generation is highly GPU-intensive.
- A dedicated graphics card is strongly recommended.
- Integrated graphics (such as APU-based solutions) are unlikely to be sufficient.

---

### 2. chktex (LaTeX command-line troubleshooting)

To analyze and debug LaTeX documents from the command line:

- Installing **MiKTeX** is recommended, as it automatically handles missing TeX packages.
- Make sure `chktex` is available in your system's **PATH**.

---

### 3. Argos Translate (Offline AI-based translation)

- This tool is CPU-intensive.
- Install Argos Translate to enable offline translation functionality.

---

## Important Notes

- If a dependency is missing, the application will not crash.
- However, any function or button that relies on a missing dependency will simply not work.

