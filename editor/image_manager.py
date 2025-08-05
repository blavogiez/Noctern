import os
import re
from tkinter import messagebox
from utils import debug_console

# --- Intelligent Image Deletion Logic ---

def _parse_for_images(content):
    """
    Parses the given document content to find all \includegraphics paths.
    """
    # Regex corrigée pour capturer les chemins d'images dans \includegraphics
    # Supporte les options entre [] et capture le chemin entre {}
    image_pattern = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    found_paths = image_pattern.findall(content)
    
    # Debug : afficher les chemins trouvés
    debug_console.log(f"Images trouvées dans le contenu : {found_paths}", level='DEBUG')
    
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
    
    # Nettoyer le chemin d'image (supprimer les espaces en début/fin)
    clean_image_path = image_path_in_tex.strip()
    
    # Normalize the path to handle '..' and resolve to an absolute path.
    # Also, replace forward slashes with backslashes for OS compatibility if needed.
    normalized_path = os.path.normpath(clean_image_path.replace("/", os.sep))
    absolute_path = os.path.join(base_directory, normalized_path)
    
    debug_console.log(f"Chemin résolu : {image_path_in_tex} -> {absolute_path}", level='DEBUG')
    
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
                debug_console.log(f"Dossier vide supprimé : {current_path}", level='INFO')
                current_path = os.path.dirname(current_path)
            except OSError as e:
                debug_console.log(f"Échec de suppression du dossier '{current_path}': {e}", level='ERROR')
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
        debug_console.log(f"Le fichier image '{image_path_to_delete}' n'existe pas, suppression ignorée.", level='INFO')
        return
    
    base_directory = os.path.dirname(tex_file_path) if tex_file_path else os.getcwd()
    display_path = os.path.relpath(image_path_to_delete, base_directory)
    debug_console.log(f"Demande de confirmation pour supprimer l'image : {display_path}", level='ACTION')
    
    response = messagebox.askyesno(
        "Supprimer le fichier image associé ?",
        f"La référence à l'image suivante a été supprimée de votre document :\n\n'{display_path}'\n\nVoulez-vous supprimer définitivement le fichier lui-même ?",
        icon='warning'
    )
    if response:
        debug_console.log(f"Utilisateur a confirmé la suppression du fichier : {image_path_to_delete}", level='ACTION')
        try:
            image_dir = os.path.dirname(image_path_to_delete)
            os.remove(image_path_to_delete)
            debug_console.log(f"Fichier image supprimé avec succès : {image_path_to_delete}", level='SUCCESS')
            
            # Define the base 'figures' directory to stop cleanup
            base_figures_dir = os.path.join(base_directory, 'figures')
            _cleanup_empty_dirs(image_dir, base_figures_dir)
        except OSError as e:
            messagebox.showerror("Erreur de suppression", f"Impossible de supprimer le fichier :\n{e}")
            debug_console.log(f"Erreur lors de la suppression du fichier '{image_path_to_delete}': {e}", level='ERROR')
    else:
        debug_console.log(f"Utilisateur a choisi de ne pas supprimer le fichier : {image_path_to_delete}", level='INFO')


def check_for_deleted_images(current_tab):
    """
    Compares the current editor content with the last saved content to identify deleted image references.

    If image references are found to be deleted from the document, the user is prompted
    to confirm whether the corresponding image files should also be deleted from the filesystem.
    This function is typically called before saving a document.

    Args:
        current_tab (EditorTab): The current active editor tab containing the document.
    """
    debug_console.log("Vérification des références d'images supprimées lors de la sauvegarde.", level='INFO')
    if not current_tab or not current_tab.is_dirty():
        debug_console.log("Vérification ignorée : Pas d'onglet actif ou document non modifié.", level='DEBUG')
        return
    
    last_saved_content = current_tab.last_saved_content
    if not last_saved_content or last_saved_content.strip() == "":
        debug_console.log("Vérification ignorée : Contenu précédemment sauvegardé vide.", level='DEBUG')
        return
    
    old_image_paths = _parse_for_images(last_saved_content)
    current_document_content = current_tab.get_content()
    new_image_paths = _parse_for_images(current_document_content)
    
    debug_console.log(f"Anciens chemins d'images : {old_image_paths}", level='DEBUG')
    debug_console.log(f"Nouveaux chemins d'images : {new_image_paths}", level='DEBUG')

    deleted_image_paths_relative = old_image_paths - new_image_paths
    
    if deleted_image_paths_relative:
        debug_console.log(f"Trouvé {len(deleted_image_paths_relative)} référence(s) d'image supprimée(s). Demande de confirmation pour suppression des fichiers.", level='DEBUG')
        for relative_path in deleted_image_paths_relative:
            absolute_path_to_delete = _resolve_image_path(current_tab.file_path, relative_path)
            _prompt_for_image_deletion(absolute_path_to_delete, current_tab.file_path)
    else:
        debug_console.log("Aucune différence détectée dans les chemins d'images.", level='INFO')


# Fonction de test pour vérifier la regex
def test_image_parsing():
    """
    Fonction de test pour vérifier que la regex fonctionne correctement
    """
    test_content = """
\\begin{figure}[h!]
    \\centering
    \\includegraphics[width=0.8\\textwidth]{figures/mexico_city/general_escobedo/default/fig_11.png}
    \\caption{Caption here}
    \\label{fig:mexico_city_general_escobedo_11}
\\end{figure}

\\includegraphics{simple_image.jpg}
\\includegraphics[scale=0.5]{another/path/image.pdf}
    """
    
    images = _parse_for_images(test_content)
    print("Images trouvées :", images)
    return images

# Décommentez pour tester
# if __name__ == "__main__":
#     test_image_parsing()