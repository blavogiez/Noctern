# AutomaTeX Development Guidelines (GEMINI.md)

This document outlines the core principles and best practices for developing and maintaining the AutomaTeX application. Adhering to these guidelines will ensure the codebase remains clean, maintainable, and easy for all contributors to work with.

---

## 1. Core Principles

-   **Clarity Over Cleverness:** Write code that is easy to understand. A straightforward implementation is always preferable to a complex one that is difficult to read, even if it's slightly less performant.
-   **User-Centric Development:** Every feature, refactor, or bug fix should ultimately serve to improve the user's experience. Keep the end-user—the LaTeX author—in mind at all times.
-   **Consistency is Key:** The codebase should look and feel like it was written by a single person. Follow the established conventions in existing files for naming, formatting, and architectural patterns.

---

## 2. Code Quality & Style

-   **Follow PEP 8:** All Python code should adhere to the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/). Use a linter like `flake8` or an autoformatter like `black` to enforce this.
-   **Type Hinting:** Use modern Python type hints for all function signatures and variable declarations (`def my_function(name: str) -> bool:`). This improves code clarity and allows for static analysis.
-   **Descriptive Naming:** Variable and function names should be descriptive and unambiguous. Avoid single-letter variables (except in simple loops) and cryptic abbreviations.
    -   **Good:** `def get_active_editor_tab()`
    -   **Bad:** `def get_tab()`
-   **Pure Functions:** Whenever possible, write functions that are "pure"—meaning they do not have side effects and will always produce the same output for the same input. This makes them easier to reason about and test.

---

## 3. Commenting & Documentation

-   **Comment the "Why," Not the "What":** Your code should be self-documenting; the "what" should be clear from the function and variable names. Use comments to explain *why* a particular implementation choice was made, especially if the logic is complex or non-obvious.

    ```python
    # Good: Explains the reasoning behind a design choice.
    # We use a forward pass to ensure the hierarchy is correctly captured,
    # as a backward pass could misinterpret the section scope.
    for line in lines:
        ...
    ```

-   **High-Quality Docstrings:** Every module, class, and public function must have a concise, well-structured docstring that explains its purpose, arguments, and return value. Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstrings.

    ```python
    def resolve_image_path(tex_file_path: str, image_path_in_tex: str) -> str:
        """Resolves a relative image path to an absolute filesystem path.

        Args:
            tex_file_path: The absolute path to the .tex file.
            image_path_in_tex: The image path as specified in an \includegraphics command.

        Returns:
            The resolved absolute path to the image file.
        """
        ...
    ```

---

## 4. Refactoring

-   **The Boy Scout Rule:** Leave the code cleaner than you found it. If you are working in a file and see a small opportunity for improvement (e.g., clarifying a variable name, extracting a function), take it.
-   **Refactor with a Safety Net:** Before undertaking a significant refactoring, ensure that the logic is covered by unit tests. This allows you to make changes with confidence, knowing that you haven't broken existing functionality.
-   **Don't Be Afraid to Restructure:** As the application grows, do not hesitate to refactor the architecture. This includes splitting modules, creating new packages, and abstracting components to better separate concerns. Refer to the `ppt/modifAutomatex.txt` plan for architectural goals.

---

## 5. File & Module Structure

-   **Keep Files Focused and Small:** A single file should have a single, clear responsibility. If a file exceeds **300-400 lines**, it is a strong indicator that it is doing too much and should be broken down into smaller, more focused modules.
    -   For example, `interface.py` should be split into separate modules for each part of the UI (e.g., `menubar.py`, `statusbar.py`, `main_window.py`).
-   **Clear Separation of Concerns:** Maintain a strict separation between different parts of the application:
    -   **UI Logic (Tkinter):** Should only be responsible for displaying data and capturing user input. It should not contain any business logic.
    -   **Core Logic (`editor_logic`, etc.):** Should be completely independent of the UI. It should not import `tkinter` or have any knowledge of UI widgets.
    -   **LLM Logic:** Should be isolated in its own module(s), making it easy to modify or even replace the LLM backend without affecting the rest of the application.

---

## 6. LLM Integration

-   **Abstract the LLM Client:** All interactions with the LLM should go through a dedicated client module. This client should expose a simple, high-level API (e.g., `client.generate_text(...)`) and hide the underlying details of API calls.
-   **Manage Prompts Centrally:** Store all LLM prompts in a dedicated location (e.g., a `prompts/` directory or a JSON file). This makes them easy to find, edit, and manage, and prevents them from being scattered throughout the codebase.
-   **Provide Context:** A key to high-quality LLM output is high-quality input. When calling the LLM, provide as much relevant context as possible, such as the document's preamble, relevant section titles, or even related snippets of text.
