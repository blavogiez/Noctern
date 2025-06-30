## The Story Behind AutomaTeX

I discovered LaTeX a few months ago. My experience has been a mix of fascination and frustration: it's a powerful language for creating beautiful documents, but its verbosity and steep learning curve can be daunting. I found myself spending more time searching for syntax and structuring my files than actually writing.

AutomaTeX was born from this duality. It is a modern LaTeX editor designed to preserve the power of the language while sanding down its rough edges. It achieves this through a suite of intelligent tools that run entirely on your local machine, ensuring your work remains private and free of charge. It's not here to replace your knowledge of LaTeX, but to augment it, letting you focus on your content, not the boilerplate.

## Project Scope & Philosophy

First and foremost, AutomaTeX is a personal project. I built it to solve the problems I was facing myself, and I'm sharing it publicly primarily as a portfolio piece to showcase my skills in software development.

This means the project is shaped by my own needs and learning process. It is not intended to compete with mature, feature-complete editors like VS Code with the LaTeX Workshop extension. I don't think this project is very amazing ; I am a first year student and no big developer ; just a local LLMs and automation enjoyer !

Instead, it's an exploration of how a lightweight, dedicated tool can simplify a specific workflow. I hope that by sharing it, others might find it useful or learn something from the code. 

## What It Can Do

-   **AI-Powered Writing Tools**: Seamlessly complete your sentences or generate entire paragraphs from a simple prompt. Specialized modes are available for both prose and raw LaTeX code.
-   **Smart Image Pasting**: Copy an image to your clipboard and paste it directly into the editor. AutomaTeX automatically saves it to a logical `figures/section/subsection/` directory and inserts the corresponding LaTeX code for you.
-   **Local-First AI**: All AI features are powered by a local LLM (via Ollama). Your data never leaves your machine. It's fast, private, and completely free.
-   **One-Click Compilation**: Compile your document and view the resulting PDF with a single click. Errors are captured in a clean, scrollable log window.
-   **Multi-File Management**: Work on multiple documents at once with a clean, tab-based interface.
-   **Intelligent File Management**: AutomaTeX detects when you remove an image reference from your document and prompts you to delete the associated file, keeping your project directory clean.
-   **Document Translation**: Translate your entire `.tex` document into another language using locally-run, high-quality translation models.
-   **Clutter-Free Interface**: A modern, responsive UI with light and dark themes, syntax highlighting, and a document outline that helps you navigate complex projects.

---

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed on your system:

1.  **Python 3.8+**: Make sure Python is installed and accessible from your terminal.
2.  **A LaTeX Distribution**:
    *   **Windows**: [MiKTeX](https://miktex.org/download)
    *   **macOS**: [MacTeX](https://www.tug.org/mactex/)
    *   **Linux**: [TeX Live](https://www.tug.org/texlive/) (`sudo apt-get install texlive-full` on Debian/Ubuntu).
3.  **Ollama**: For all AI features, you need a running Ollama instance. [Download it here](https://ollama.com/).
4.  **(Optional) chktex**: For advanced document linting.
    *   On Linux: `sudo apt-get install chktex`
    *   On macOS: `brew install chktex`

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/AutomaTeX.git
    cd AutomaTeX
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```
    *(This will install `Pillow`, `requests`, `sv_ttk`, and `argostranslate`)*

3.  **Download AI Models:**
    *   **For Text Generation (Ollama):** Pull the models you wish to use. We recommend starting with Mistral and CodeLlama.
        ```bash
        ollama pull mistral
        ollama pull codellama
        ```
    *   **For Translation (Argos Translate):** The application will prompt you to download language packs on first use.

4.  **Run the application:**
    ```bash
    python main.py
    ```

---

## User Guide

| Feature                  | Action                                     | Description                                                                                                                              |
| ------------------------ | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **AI Completion**        | `Ctrl` + `Shift` + `C`                     | Completes the current sentence or phrase you are writing.                                                                                |
| **AI Generation**        | `Ctrl` + `Shift` + `G`                     | Opens a dialog to generate text from a detailed prompt. Includes a "LaTeX Mode" to generate raw, valid LaTeX code.                     |
| **AI Rephrase**          | Select Text + `Ctrl` + `R`                 | Opens a dialog to rephrase the selected text based on a given instruction (e.g., "make it more formal", "shorten it").                  |
| **Paste Image**          | `Ctrl` + `Shift` + `V`                     | Pastes an image from the clipboard, saves it to `figures/section/subsection/fig_N.png`, and inserts the LaTeX `figure` environment.      |
| **Compile Document**     | `Compile` Button                           | Compiles the `.tex` file using `pdflatex` and opens the resulting PDF in the integrated SumatraPDF viewer (or system default).            |
| **Translate Document**   | `Translate` Button                         | Translates the current document, saving it as a new file (e.g., `fr_document.tex`). Prompts to download languages as needed.              |
| **Check Document**       | `Tools` > `Check Document`                 | Runs `chktex` on the current file to find common LaTeX errors and stylistic issues, displaying the output in a new window.                |
| **Configure Prompts**    | `Settings` > `Edit LLM Prompts`            | Customize the underlying prompts used for AI generation and completion. Changes are saved per-document.                                  |
| **Set Keywords**         | `Settings` > `Set LLM Keywords`            | Provide a list of keywords to give the AI context about your document's topic, improving the relevance of generated content.             |
| **Toggle Theme**         | `Theme` Button                             | Instantly switch between a polished light and dark mode.                                                                                 |
| **Zoom**                 | `Ctrl` + `+` / `Ctrl` + `-`                | Increase or decrease the editor's font size.                                                                                             |

---

## Personal Notes & Lessons Learned

This project was as much a lesson in software design as it was in programming. Here are some of my key takeaways.

### On Simplicity and Performance

Early in development, I was convinced that AutomaTeX needed a state-of-the-art, real-time error-checking and syntax-highlighting engine. I spent five full days building a complex system that analyzed the text on every keystroke. The result was a crippling input lag that made the editor unusable, especially with files over a few hundred lines. After failing to fix the performance bottleneck, I had to revert all of that work.

The current system, which uses a scheduled, delayed update mechanism (`schedule_heavy_updates`), is a direct result of this failure. It's a pragmatic compromise: feedback is nearly instant but not strictly real-time, which preserves a perfectly smooth typing experience. It was a painful but valuable lesson in prioritizing user experience over technical purity.

### On User-Centric AI

Building the AI features taught me that the "magic" isn't just in the model's output; it's in how that output is presented to the user. The interactive UI for AI text—which allows you to accept, discard, or rephrase a suggestion with a single keypress—was a critical addition. It transforms the AI from a black box into a collaborative tool, keeping the user firmly in control of their document.

### On Project Structure

As the application grew, I learned the importance of separating concerns. Initially, much of the logic was tangled together. Refactoring the code into distinct modules (`editor_logic`, `llm_service`, `interface`, etc.) was a turning point. It made the codebase easier to reason about, debug, and extend. The current structure isn't perfect, but it laid a foundation that allowed the project to scale without collapsing under its own complexity.

## Future Roadmap

Given that this is a personal portfolio project, development will continue as I learn new things and have new ideas. Some areas I'm interested in exploring next include:

-   **Advanced Project Management**: A proper file tree and better support for multi-file projects (`\input{}` and `\include{}`).
-   **Language Server Protocol (LSP) Integration**: For more robust, real-time syntax and error checking without sacrificing performance.
-   **Vim / Emacs Keybindings**: To cater to power users.
-   **Git Integration**: Directly manage version control from within the editor.

---

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.