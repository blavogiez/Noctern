# Analyse Automatisée du Projet AutomaTeX

**Objectif de ce document :** Ce document est une analyse générée automatiquement du projet AutomaTeX. Il me sert de référence technique pour comprendre l'architecture, les conventions et les points clés du code. L'objectif est de garantir que mes interventions futures soient pertinentes, cohérentes et basées sur la structure existante, afin d'éviter toute "hallucination" ou modification inappropriée.

---

## 1. Analyse Globale

### But de l'Application
AutomaTeX est un éditeur de texte spécialisé pour le langage LaTeX. Il intègre des fonctionnalités avancées visant à automatiser et assister la rédaction, notamment :
- Un éditeur de texte avec gestion d'onglets.
- Un compilateur LaTeX intégré avec visionneuse PDF.
- Des outils d'analyse et de "nettoyage" de code LaTeX.
- Une intégration poussée avec un modèle de langage (LLM) pour la génération, la complétion et la reformulation de texte.
- La gestion de thèmes, de snippets et de paramètres personnalisables.

### Technologie
- **Langage :** Python 3.
- **Interface Graphique (GUI) :** `tkinter` avec le framework `ttkbootstrap` pour le style.
- **Dépendances notables :** `argostranslate` pour la traduction (bien que non trouvé lors du dernier lancement).

---

## 2. Structure du Projet

L'application est organisée en modules fonctionnels distincts, ce qui indique une architecture modulaire claire.

-   **`main.py`**: Point d'entrée de l'application. Responsable de l'initialisation globale et du lancement de la boucle GUI.

-   **`app/`**: Cœur de l'interface utilisateur et de la logique applicative.
    -   `main_window.py`: Configure la fenêtre principale (`root`).
    -   `topbar.py`: Crée la barre de menu supérieure.
    -   `actions.py`: Contient les fonctions appelées par les éléments de l'UI (menus, boutons).
    -   `state.py`: **Crucial.** Gère l'état global de l'application (ex: onglet courant, paramètres, etc.).
    -   `config.py`, `settings_window.py`: Gèrent la configuration et la fenêtre des préférences.
    -   `file_operations.py`, `tab_operations.py`: Logique de gestion des fichiers et des onglets.
    -   `statusbar.py`, `theme.py`, `zoom.py`: Gèrent des parties spécifiques de l'UI.

-   **`editor/`**: Composants liés à l'éditeur de texte lui-même.
    -   `tab.py`: Définit la classe pour un onglet d'édition.
    -   `logic.py`: Logique de l'éditeur (ex: gestion du texte).
    -   `snippets.py`: Gestion des extraits de code (snippets).
    -   `image_paste.py`: Logique pour coller des images.

-   **`latex/`**: Tout ce qui concerne la compilation et la gestion LaTeX.
    -   `compiler.py`: Gère la compilation des documents `.tex` en PDF.
    -   `error_parser.py`: Analyse les logs d'erreurs de LaTeX.
    -   `translator.py`: Gère la traduction de documents.

-   **`llm/`**: Module très important gérant l'intégration avec le modèle de langage.
    -   `service.py`: Point d'entrée pour les services LLM (complétion, génération).
    -   `api_client.py`: Gère les appels à l'API du LLM.
    -   `prompts.py`, `prompt_manager.py`: Gèrent les prompts utilisés pour interagir avec le LLM.
    -   `history.py`, `keyword_history.py`: Gèrent l'historique des interactions.
    -   `dialogs/`: Contient les fenêtres de dialogue spécifiques aux fonctionnalités LLM.

-   **`utils/`**: Fonctions utilitaires transverses.
    -   `debug_console.py`: **Important.** Fournit une console de débogage pour logger des informations.
    -   `screen.py`, `animations.py`: Utilitaires pour l'UI.

-   **`data/` et `resources/`**: Contiennent les données statiques comme les prompts par défaut, les snippets, et les icônes.

-   **`docs/`**: Documentation du projet.

---

## 3. Points Clés et Conventions

-   **Gestion de l'état centralisée :** Le module `app.state` est la source de vérité pour l'état de l'application. Toute modification doit passer par ou consulter ce module pour éviter les incohérences.
-   **Découplage UI / Logique :** La logique métier (ex: `latex.compiler`) est bien séparée de l'interface (`app.actions`). Les actions de l'UI appellent des fonctions dans les modules de logique.
-   **Logging :** Pour le débogage, je dois utiliser la console fournie par `utils.debug_console.log()` plutôt que des `print()` standards.
-   **Configuration multiple :** Les paramètres sont gérés via `settings.conf` et les prompts LLM via `.env_prompts.json` (utilisateur) et `data/default_prompts.json` (défaut).
-   **Modularité forte :** Chaque fonctionnalité majeure (éditeur, LaTeX, LLM) a son propre répertoire. Les modifications doivent respecter cette séparation.

---

## 4. Directives pour les Modifications Futures

1.  **Avant toute modification de l'état,** je consulterai `app/state.py` pour comprendre comment l'état est géré.
2.  **Pour ajouter une action à l'UI,** je l'implémenterai dans le module logique approprié (ex: `editor/logic.py`) et je l'appellerai depuis `app/actions.py`. Le lien dans l'UI se fera dans `app/topbar.py` ou un autre fichier de l'interface.
3.  **Pour toute interaction avec le LLM,** je passerai par `llm/service.py` et je consulterai `llm/prompts.py` pour comprendre comment les prompts sont structurés.
4.  **Pour tout affichage d'information ou de débogage,** j'utiliserai `utils.debug_console.log()`.
5.  **Pour les modifications de l'interface,** je respecterai le style défini par `ttkbootstrap` et je m'inspirerai du code existant dans le répertoire `app/`.
6.  **En cas de doute sur une fonctionnalité,** je lirai le contenu des fichiers du module correspondant avant d'agir.

Ce document me servira de guide de référence pour toutes mes futures interactions avec ce projet.
