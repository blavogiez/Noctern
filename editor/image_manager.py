import os
import re
from tkinter import messagebox
from utils import debug_console

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
    image_pattern = re.compile(r"\\includegraphics(?:\\\\[.*?\\\\])?\{(.*?)")
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
