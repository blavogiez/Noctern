import tkinter as tk
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
    si une ligne contient une commande de section (comme \section) et en
    extrait le titre.

    Args:
        line (str): La ligne de texte à analyser.
        command (str): La commande à rechercher (ex: \"\\section\").

    Returns:
        str ou None: Le titre trouvé, ou None si la ligne ne correspond pas.
    """
    # Étape 1: Vérifier si la ligne commence bien par la commande.
    if not line.startswith(command):
        return None

    # Étape 2: Supprimer la commande pour ne garder que la suite.
    # Exemple: \"\\section{Titre}\" devient "{Titre}".
    line_after_command = line[len(command):]

    # Étape 3: Gérer les commandes étoilées (ex: \"\\section*\").
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
                # Pour un \"\\subsection\" (niveau 2), le parent est le dernier \"\\section\" (niveau 1).
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

                # Si on a trouvé une \"\\section\", on oublie les anciennes \"\\subsection\".
                if level == 1:
                    if 2 in parent_item_at_level:
                        del parent_item_at_level[2]
                    if 3 in parent_item_at_level:
                        del parent_item_at_level[3]
                # Si on a trouvé une \"\\subsection\", on oublie les anciennes \"\\subsubsection\".
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
