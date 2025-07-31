import tkinter as tk
import re
import os
from tkinter import messagebox
from PIL import ImageGrab
from editor.tab import EditorTab
from utils import debug_console

# Global variable to hold the reference to the outline treeview widget.
# This allows different parts of the editor logic to interact with the outline.
outline_tree = None

def initialize_editor_logic(tree_widget):
    """
    Initializes the editor logic by setting the global reference to the outline treeview widget.

    This function is called during application startup to link the editor's
    backend logic with the UI component responsible for displaying the document outline.

    Args:
        tree_widget (ttk.Treeview): The Treeview widget used for the document outline.
    """
    global outline_tree
    outline_tree = tree_widget
    debug_console.log("Editor logic initialized with outline tree reference.", level='INFO')

def _get_title_from_line(line, command):
    """
    Essaie d'extraire un titre de section LaTeX à partir d'une ligne.

    Cette fonction est conçue pour être très simple et lisible. Elle vérifie
    si une ligne contient une commande de section (comme \\section) et en
    extrait le titre.

    Args:
        line (str): La ligne de texte à analyser.
        command (str): La commande à rechercher (ex: "\\section").

    Returns:
        str ou None: Le titre trouvé, ou None si la ligne ne correspond pas.
    """
    # Étape 1: Vérifier si la ligne commence bien par la commande.
    if not line.startswith(command):
        return None

    # Étape 2: Supprimer la commande pour ne garder que la suite.
    # Exemple: "\\section{Titre}" devient "{Titre}".
    line_after_command = line[len(command):]

    # Étape 3: Gérer les commandes étoilées (ex: \\section*).
    # Si la ligne commence par une étoile, on la supprime.
    if line_after_command.startswith('*'):
        line_after_command = line_after_command[1:]
    
    # Étape 4: Supprimer les espaces blancs au début.
    line_after_command = line_after_command.lstrip()

    # Étape 5: Gérer les arguments optionnels (ex: [Titre court]).
    # Si on trouve un crochet ouvrant, on supprime tout jusqu'au crochet fermant.
    if line_after_command.startswith('['):
        end_bracket_index = line_after_command.find(']')
        # Si on ne trouve pas de crochet fermant, la commande est mal formée.
        if end_bracket_index == -1:
            return None
        # On ne garde que ce qui se trouve APRES le crochet fermant.
        line_after_command = line_after_command[end_bracket_index + 1:]

    # Étape 6: Supprimer à nouveau les espaces blancs.
    line_after_command = line_after_command.lstrip()

    # Étape 7: Le titre doit maintenant commencer par une accolade ouvrante '{'.
    if not line_after_command.startswith('{'):
        return None

    # Étape 8: Trouver l'accolade fermante '}'.
    end_brace_index = line_after_command.find('}')
    if end_brace_index == -1:
        return None # Accolade fermante non trouvée.

    # Étape 9: Extraire le texte entre les deux accolades.
    title = line_after_command[1:end_brace_index]
    
    # Étape 10: Renvoyer le titre en supprimant les espaces au début et à la fin.
    return title.strip()

def update_outline_tree(editor):
    """
    Met à jour la Treeview avec la structure des sections du document.
    Cette version utilise des fonctions de chaînes de caractères simples pour
    être facile à comprendre par un développeur junior.
    """
    if not outline_tree or not editor:
        return

    # On vide complètement l'arbre avant de le reconstruire.
    outline_tree.delete(*outline_tree.get_children())
    
    content = editor.get("1.0", tk.END)
    lines = content.split("\n")
    
    # Ce dictionnaire mémorise le dernier élément créé pour chaque niveau.
    # ex: {1: "id_de_la_derniere_section", 2: "id_de_la_derniere_subsection"}
    # Le niveau 0 est la racine de l'arbre (invisible).
    parent_item_at_level = {0: ""} 

    # On parcourt chaque ligne du document.
    for line_index, line_text in enumerate(lines):
        clean_line = line_text.strip()

        # On définit les commandes à chercher et leur niveau hiérarchique.
        commands_to_check = {
            "\\section": 1,
            "\\subsection": 2,
            "\\subsubsection": 3
        }

        # On teste chaque type de commande pour la ligne actuelle.
        for command, level in commands_to_check.items():
            
            # On utilise notre fonction d'aide pour extraire le titre.
            title = _get_title_from_line(clean_line, command)

            # Si on a trouvé un titre :
            if title:
                # Le parent de notre élément est l'élément du niveau juste au-dessus.
                # Pour un \\subsection (niveau 2), le parent est le dernier \\section (niveau 1).
                parent_level = level - 1
                parent_id = parent_item_at_level.get(parent_level, "")

                # Le numéro de ligne pour la navigation (l'index commence à 0).
                line_number_for_goto = line_index + 1

                # On ajoute l'élément à l'arbre.
                new_item_id = outline_tree.insert(
                    parent_id, 
                    "end", 
                    text=title, 
                    values=(line_number_for_goto,)
                )

                # On mémorise ce nouvel élément comme étant le dernier pour son niveau.
                parent_item_at_level[level] = new_item_id

                # Si on a trouvé une \\section, on oublie les anciennes \\subsection.
                if level == 1:
                    if 2 in parent_item_at_level:
                        del parent_item_at_level[2]
                    if 3 in parent_item_at_level:
                        del parent_item_at_level[3]
                # Si on a trouvé une \\subsection, on oublie les anciennes \\subsubsection.
                elif level == 2:
                    if 3 in parent_item_at_level:
                        del parent_item_at_level[3]

                # On a trouvé la commande pour cette ligne, on passe à la ligne suivante.
                break


def go_to_section(get_current_tab_callback, event):
    """
    Scrolls the editor to the line corresponding to the selected section in the outline tree.

    This function is typically triggered by a user selecting an item in the outline treeview.
    It extracts the line number associated with the selected section and moves the editor's
    view to that line, placing the cursor at the beginning of the line.

    Args:
        get_current_tab_callback (function): A callback to get the current active tab.
        event (tk.Event): The event object that triggered this function (e.g., TreeviewSelect).
    """
    current_tab = get_current_tab_callback()
    if not current_tab or not hasattr(current_tab, 'editor'):
        debug_console.log("Editor not available for section navigation.", level='WARNING')
        return
    
    editor = current_tab.editor
    selected_items = outline_tree.selection() # Get the currently selected items in the treeview.
    if selected_items:
        # Retrieve the values associated with the first selected item.
        # The line number is stored as the first value.
        values = outline_tree.item(selected_items[0], "values")
        if values:
            line_number = values[0] # Extract the line number.
            debug_console.log(f"Navigating editor to line {line_number} for selected section.", level='ACTION')
            try:
                # Scroll the view so the target line is at the top.
                editor.yview(f"{line_number}.0")
                # Set the insertion cursor to the beginning of the target line.
                editor.mark_set("insert", f"{line_number}.0")
                editor.focus() # Set focus back to the editor.
            except tk.TclError as e:
                debug_console.log(f"Error navigating to section: {e}", level='ERROR')
                pass # Ignore errors if the line number is invalid or out of range.

def apply_syntax_highlighting(editor):
    """
    Applies syntax highlighting to LaTeX commands, braces, and comments within the editor.
    Also checks for and highlights references to missing image files.

    This function iterates through the editor's content, applying specific Tkinter text tags
    to different LaTeX elements for visual distinction. It also performs a check for
    \includegraphics commands and verifies if the referenced image files exist on the filesystem.
    Missing image references are highlighted, and an error indicator is embedded.

    Args:
        editor (tk.Text): The Tkinter Text widget to apply highlighting to.
    """
    if not editor:
        debug_console.log("Editor not available for syntax highlighting.", level='WARNING')
        return

    debug_console.log("Applying syntax highlighting and checking for missing image files.", level='DEBUG')

    current_tab = editor.master
    # Ensure the editor's master is an EditorTab instance to access its properties.
    if isinstance(current_tab, EditorTab):
        # Destroy and clear any previously embedded error labels to prevent accumulation.
        for label in current_tab.error_labels:
            label.destroy()
        current_tab.error_labels.clear()

    # Remove all existing syntax highlighting tags to ensure a clean re-application.
    editor.tag_remove("latex_command", "1.0", tk.END)
    editor.tag_remove("latex_brace", "1.0", tk.END)
    editor.tag_remove("latex_comment", "1.0", tk.END)
    editor.tag_remove("image_error", "1.0", tk.END) 

    content = editor.get("1.0", tk.END) # Get the entire content for parsing.

    # --- 1. Standard LaTeX Syntax Highlighting ---
    # Highlight LaTeX commands (e.g., \command, \@command).
    for match in re.finditer(r"\\[a-zA-Z@]+", content):
        start_index = f"1.0 + {match.start()} chars"
        end_index = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_command", start_index, end_index)

    # Highlight LaTeX braces ({}).
    for match in re.finditer(r"[{}]", content):
        start_index = f"1.0 + {match.start()} chars"
        end_index = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_brace", start_index, end_index)

    # Highlight LaTeX comments (lines starting with %).
    for match in re.finditer(r"%[^\n]*", content):
        start_index = f"1.0 + {match.start()} chars"
        end_index = f"1.0 + {match.end()} chars"
        editor.tag_add("latex_comment", start_index, end_index)

    # --- 2. Check for Missing \includegraphics Files ---
    if isinstance(current_tab, EditorTab):
        # Regex to find \includegraphics commands and capture the image path.
        image_inclusion_pattern = re.compile(r"\\includegraphics(?:\[.*?\])?\{(.*?)\"")
        missing_image_count = 0
        for match in image_inclusion_pattern.finditer(content):
            relative_image_path = match.group(1) # Extract the path as written in the LaTeX document.
            # Resolve the relative path to an absolute path on the filesystem.
            absolute_image_path = _resolve_image_path(current_tab.file_path, relative_image_path)

            # Check if the resolved image file actually exists.
            if not os.path.exists(absolute_image_path):
                missing_image_count += 1
                
                # Highlight the missing image path in the editor.
                path_start_index = f"1.0 + {match.start(1)} chars"
                path_end_index = f"1.0 + {match.end(1)} chars"
                editor.tag_add("image_error", path_start_index, path_end_index)

                # Create and embed a visual error indicator (label) at the end of the line.
                line_index = editor.index(path_start_index).split('.')[0]
                error_label = tk.Label(
                    editor,
                    text=" ⚠ Fichier introuvable", # "File not found" in French.
                    font=("Segoe UI", 8),
                    bg="#FFF0F0", # Light red background for the label.
                    fg="#D00000", # Dark red text for the label.
                    padx=2
                )
                # Add the label to the tab's list for proper cleanup when the tab is closed.
                current_tab.error_labels.append(error_label);
                # Embed the label widget directly into the text editor at the end of the line.
                editor.window_create(f"{line_index}.end", window=error_label, align="top")
        if missing_image_count > 0:
            debug_console.log(f"Detected {missing_image_count} missing image reference(s) in the document.", level='WARNING')


def extract_section_structure(content, position_index):
    """
    Extracts the current section, subsection, and subsubsection titles based on a given character position.

    This function is used to determine the logical location within a LaTeX document
    (e.g., which section an image is being pasted into). It scans backwards from the
    specified position to find the most recent sectioning commands in a hierarchical manner.

    Args:
        content (str): The full text content of the LaTeX document.
        position_index (int): The character index within the content to start the search from.

    Returns:
        tuple: A tuple containing the current section, subsection, and subsubsection titles.
               Defaults to "default" if no specific section is found.
    """
    # Get the content up to the cursor and split into lines
    content_before_cursor = content[:position_index]
    lines = content_before_cursor.split('\n')
    
    # Initialize titles to "default"
    current_section = "default"
    current_subsection = "default"
    current_subsubsection = "default"

    # Regex to capture titles, handling optional arguments and stars
    section_regex = re.compile(r"\\section\*?(?:\\[[^\]]*\])?{([^}]+)}")
    subsection_regex = re.compile(r"\\subsection\*?(?:\\[[^\]]*\])?{([^}]+)}")
    subsubsection_regex = re.compile(r"\\subsubsection\*?(?:\\[[^\]]*\])?{([^}]+)}")

    # Iterate backwards through the lines to find the most recent section commands
    for line in reversed(lines):
        # Once a section is found, we don't need to look for sections in earlier lines
        if current_section == "default":
            match = section_regex.search(line)
            if match:
                current_section = match.group(1).strip()

        # Once a subsection is found, we don't need to look for subsections in earlier lines
        if current_subsection == "default":
            match = subsection_regex.search(line)
            if match:
                current_subsection = match.group(1).strip()

        # Once a subsubsection is found, we don't need to look for them in earlier lines
        if current_subsubsection == "default":
            match = subsubsection_regex.search(line)
            if match:
                current_subsubsection = match.group(1).strip()

    # Hierarchical reset: if a \section is found, reset deeper levels found *before* it.
    # This logic is complex when iterating backwards. A forward pass is more reliable.
    # Let's re-do this with a forward pass for reliability.

    # Reset titles
    current_section, current_subsection, current_subsubsection = "default", "default", "default"

    for line in lines:
        # Match \section
        match = section_regex.search(line)
        if match:
            current_section = match.group(1).strip()
            # When a new section starts, reset subsection and subsubsection
            current_subsection = "default"
            current_subsubsection = "default"
            continue # Continue to next line

        # Match \subsection
        match = subsection_regex.search(line)
        if match:
            current_subsection = match.group(1).strip()
            # When a new subsection starts, reset subsubsection
            current_subsubsection = "default"
            continue # Continue to next line
            
        # Match \subsubsection
        match = subsubsection_regex.search(line)
        if match:
            current_subsubsection = match.group(1).strip()

    return current_section, current_subsection, current_subsubsection

# --- Intelligent Image Deletion Logic ---

def _parse_for_images(content):
    """
    Parses the given document content to find all \includegraphics paths.

    This helper function uses a regular expression to extract all file paths
    referenced within \includegraphics commands in a LaTeX document.

    Args:
        content (str): The full text content of the LaTeX document.

    Returns:
        set: A set of unique image file paths found in the content.
    """
    # Regular expression to find \includegraphics commands and capture the path within braces.
    image_pattern = re.compile(r"\\includegraphics(?:\[.*?\])?\{(.*?)\}")
    found_paths = image_pattern.findall(content)
    return set(found_paths) # Return a set to ensure uniqueness of paths.

def _resolve_image_path(tex_file_path, image_path_in_tex):
    """
    Resolves a relative image path found in a .tex file to an absolute filesystem path.

    This function takes the path of the .tex file and the image path as written
    in the LaTeX document (which can be relative) and converts it into an absolute
    path that can be used to locate the file on the system.

    Args:
        tex_file_path (str): The absolute path to the .tex file.
        image_path_in_tex (str): The image path as specified in the \includegraphics command.

    Returns:
        str: The absolute path to the image file.
    """
    if not tex_file_path:
        # If the .tex file path is not available, assume current working directory as base.
        base_directory = os.getcwd()
    else:
        # Otherwise, the base directory is where the .tex file is located.
        base_directory = os.path.dirname(tex_file_path)
    # Normalize the path to handle '..' and resolve to an absolute path.
    # Also, replace forward slashes with backslashes for OS compatibility if needed.
    normalized_path = os.path.normpath(image_path_in_tex.replace("/", os.sep))
    absolute_path = os.path.join(base_directory, normalized_path)
    return absolute_path

def _cleanup_empty_dirs(path, base_figures_dir):
    """
    Recursively deletes empty directories upwards from the given path, stopping at the base 'figures' directory.

    This function is called after an image file has been deleted. It checks if the parent
    directories have become empty and, if so, deletes them recursively until a non-empty
    directory or the specified base 'figures' directory is reached.

    Args:
        path (str): The starting path (typically the directory of the deleted image).
        base_figures_dir (str): The root 'figures' directory, beyond which cleanup should not proceed.
    """
    current_path = os.path.normpath(path)
    base_figures_dir = os.path.normpath(base_figures_dir)

    # Loop upwards as long as the current path is within the base_figures_dir and is a directory.
    while current_path.startswith(base_figures_dir) and os.path.isdir(current_path) and current_path != base_figures_dir:
        if not os.listdir(current_path):
            try:
                os.rmdir(current_path)
                debug_console.log(f"Removed empty directory: {current_path}", level='INFO')
                current_path = os.path.dirname(current_path)
            except OSError as e:
                debug_console.log(f"Failed to remove directory '{current_path}': {e}", level='ERROR')
                break # Stop if an error occurs.
        else:
            break # Stop if the directory is not empty.

def _prompt_for_image_deletion(image_path_to_delete, tex_file_path):
    """
    Displays a confirmation dialog to the user for deleting an image file.

    If the user confirms, the image file is deleted from the filesystem, and
    subsequently, any empty parent directories within the 'figures' structure
    are also cleaned up.

    Args:
        image_path_to_delete (str): The absolute path of the image file to potentially delete.
        tex_file_path (str): The absolute path to the .tex file from which the image was referenced.
    """
    if not os.path.exists(image_path_to_delete):
        debug_console.log(f"Image file '{image_path_to_delete}' does not exist, skipping deletion prompt.", level='INFO')
        return
    
    base_directory = os.path.dirname(tex_file_path) if tex_file_path else os.getcwd()
    display_path = os.path.relpath(image_path_to_delete, base_directory)
    debug_console.log(f"Prompting user for deletion of image file: {display_path}", level='ACTION')
    
    response = messagebox.askyesno(
        "Delete Associated Image File?",
        f"The reference to the following image file has been removed from your document:\n\n'{display_path}'\n\nDo you want to permanently delete the file itself?",
        icon='warning'
    )
    if response:
        debug_console.log(f"User confirmed deletion of file: {image_path_to_delete}", level='ACTION')
        try:
            image_dir = os.path.dirname(image_path_to_delete)
            os.remove(image_path_to_delete)
            debug_console.log(f"Image file successfully deleted: {image_path_to_delete}", level='SUCCESS')
            
            # Define the base 'figures' directory to stop cleanup
            base_figures_dir = os.path.join(base_directory, 'figures')
            _cleanup_empty_dirs(image_dir, base_figures_dir)
        except OSError as e:
            messagebox.showerror("Deletion Error", f"Could not delete the file:\n{e}")
            debug_console.log(f"Error deleting file '{image_path_to_delete}': {e}", level='ERROR')
    else:
        debug_console.log(f"User chose not to delete file: {image_path_to_delete}", level='INFO')


def check_for_deleted_images(current_tab):
    """
    Compares the current editor content with the last saved content to identify deleted image references.

    If image references are found to be deleted from the document, the user is prompted
    to confirm whether the corresponding image files should also be deleted from the filesystem.
    This function is typically called before saving a document.

    Args:
        current_tab (EditorTab): The current active editor tab containing the document.
    """
    debug_console.log("Initiating check for deleted image references on document save.", level='INFO')
    if not current_tab or not current_tab.is_dirty():
        debug_console.log("Skipping image deletion check: No active tab or document is not dirty.", level='DEBUG')
        return
    
    last_saved_content = current_tab.last_saved_content
    if not last_saved_content or last_saved_content.strip() == "":
        debug_console.log("Skipping image deletion check: Last saved content is empty.", level='DEBUG')
        return
    
    old_image_paths = _parse_for_images(last_saved_content)
    current_document_content = current_tab.get_content()
    new_image_paths = _parse_for_images(current_document_content)
    
    deleted_image_paths_relative = old_image_paths - new_image_paths
    
    if deleted_image_paths_relative:
        debug_console.log(f"Found {len(deleted_image_paths_relative)} deleted image reference(s). Prompting user for file deletion.", level='DEBUG')
        for relative_path in deleted_image_paths_relative:
            absolute_path_to_delete = _resolve_image_path(current_tab.file_path, relative_path)
            _prompt_for_image_deletion(absolute_path_to_delete, current_tab.file_path)
