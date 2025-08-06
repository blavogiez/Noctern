import os
import re
from tkinter import messagebox
from utils import debug_console
import threading
import time
import hashlib
import glob

# --- Intelligent Image Deletion Logic ---

# Global variables to track image changes in real-time
_tracked_tabs = {}  # {tab_id: {'images': set(), 'last_content_hash': str, 'last_check_time': float, 'tab_ref': tab}}
_check_interval = 0.3  # Check more frequently - every 300ms
_monitoring_active = True
_pending_deletions = set()  # Avoid duplicate prompts
_monitor_thread = None
_last_manual_check = 0  # Track manual checks to avoid conflicts

def _parse_for_images(content):
    """
    Parses the given document content to find all \includegraphics paths.
    Enhanced to handle various edge cases and malformed LaTeX.
    """
    if not content:
        return set()
    
    # Multiple regex patterns to catch different formats
    patterns = [
        # Standard format with optional parameters
        r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{([^}]+)\}",
        # Format with spaces around braces
        r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{\s*([^}]+?)\s*\}",
        # Multiline format
        r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{\s*([^}]+?)\s*\}",
    ]
    
    found_paths = set()
    
    for pattern in patterns:
        image_pattern = re.compile(pattern, re.MULTILINE | re.DOTALL)
        matches = image_pattern.findall(content)
        for match in matches:
            cleaned_path = match.strip()
            if cleaned_path:  # Only add non-empty paths
                found_paths.add(cleaned_path)
    
    debug_console.log(f"Images found in content: {found_paths}", level='DEBUG')
    return found_paths

def _get_content_hash(content):
    """
    Returns a hash of the content to detect changes more reliably
    """
    if not content:
        return ""
    return hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()

def _find_orphaned_images(tex_file_path, current_images):
    """
    AJOUT SIMPLE : Trouve les images orphelines en comparant les fichiers existants 
    dans figures/ avec les références actuelles
    """
    if not tex_file_path:
        return set()
    
    base_dir = os.path.dirname(tex_file_path)
    figures_dir = os.path.join(base_dir, 'figures')
    
    if not os.path.exists(figures_dir):
        return set()
    
    # Extensions d'images courantes
    extensions = ['*.png', '*.jpg', '*.jpeg', '*.pdf', '*.eps', '*.svg']
    existing_files = set()
    
    try:
        for ext in extensions:
            pattern = os.path.join(figures_dir, '**', ext)
            for file_path in glob.glob(pattern, recursive=True):
                # Convertir en chemin relatif depuis le répertoire du .tex
                rel_path = os.path.relpath(file_path, base_dir)
                rel_path = rel_path.replace(os.sep, '/')  # Format LaTeX
                existing_files.add(rel_path)
        
        # Retourner les fichiers qui existent mais ne sont plus référencés
        orphaned = existing_files - current_images
        if orphaned:
            debug_console.log(f"Found {len(orphaned)} orphaned images: {orphaned}", level='INFO')
        return orphaned
        
    except Exception as e:
        debug_console.log(f"Error finding orphaned images: {e}", level='ERROR')
        return set()

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
    
    # Clean the image path more thoroughly
    clean_image_path = image_path_in_tex.strip().replace('\n', '').replace('\r', '')
    
    # Handle different path separators
    normalized_path = os.path.normpath(clean_image_path.replace("/", os.sep).replace("\\", os.sep))
    absolute_path = os.path.join(base_directory, normalized_path)
    
    debug_console.log(f"Path resolved: '{image_path_in_tex}' -> '{absolute_path}'", level='DEBUG')
    
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
        try:
            if not os.listdir(current_path):
                os.rmdir(current_path)
                debug_console.log(f"Removed empty directory: {current_path}", level='INFO')
                current_path = os.path.dirname(current_path)
            else:
                break # Stop if the directory is not empty.
        except OSError as e:
            debug_console.log(f"Failed to remove directory '{current_path}': {e}", level='ERROR')
            break # Stop if an error occurs.

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
    try:
        display_path = os.path.relpath(image_path_to_delete, base_directory)
    except ValueError:
        # Handle case where paths are on different drives (Windows)
        display_path = image_path_to_delete
        
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

def _monitor_changes():
    """
    Background thread that continuously monitors for image reference changes
    Enhanced with better error handling and more frequent checks
    """
    global _monitoring_active, _tracked_tabs, _pending_deletions
    
    debug_console.log("Image monitoring thread started", level='INFO')
    
    while _monitoring_active:
        try:
            current_time = time.time()
            tabs_to_remove = []
            
            # Create a copy of the dictionary to avoid modification during iteration
            tabs_snapshot = dict(_tracked_tabs)
            
            for tab_id, tab_data in tabs_snapshot.items():
                try:
                    tab_ref = tab_data['tab_ref']
                    
                    # Check if tab still exists and has required methods
                    if not hasattr(tab_ref, 'get_content') or not callable(getattr(tab_ref, 'get_content')):
                        tabs_to_remove.append(tab_id)
                        continue
                    
                    # Check for changes more frequently
                    if current_time - tab_data.get('last_check_time', 0) >= _check_interval:
                        _check_tab_for_deletions(tab_id, tab_ref, tab_data)
                        tab_data['last_check_time'] = current_time
                        
                except Exception as e:
                    debug_console.log(f"Error monitoring tab {tab_id}: {e}", level='ERROR')
                    tabs_to_remove.append(tab_id)
            
            # Clean up closed tabs
            for tab_id in tabs_to_remove:
                if tab_id in _tracked_tabs:
                    debug_console.log(f"Removing dead tab {tab_id} from monitoring", level='DEBUG')
                    del _tracked_tabs[tab_id]
            
            time.sleep(0.1)  # Very short pause for responsiveness
            
        except Exception as e:
            debug_console.log(f"Critical error in monitoring thread: {e}", level='ERROR')
            time.sleep(0.5)
    
    debug_console.log("Image monitoring thread stopped", level='INFO')

def _check_tab_for_deletions(tab_id, tab_ref, tab_data):
    """
    Checks if images have been deleted in a tab with enhanced detection
    """
    global _pending_deletions
    
    try:
        # Get current content
        current_content = tab_ref.get_content()
        if current_content is None:
            return
            
        # Check if content actually changed using hash
        current_hash = _get_content_hash(current_content)
        last_hash = tab_data.get('last_content_hash', '')
        
        if current_hash == last_hash:
            return  # No changes detected
            
        # Content changed, check for image differences
        current_images = _parse_for_images(current_content)
        previous_images = tab_data.get('images', set())
        
        deleted_images = previous_images - current_images
        added_images = current_images - previous_images
        
        if deleted_images:
            debug_console.log(f"Deleted images detected in tab {tab_id}: {deleted_images}", level='INFO')
            
            # Process each deleted image
            for image_path in deleted_images:
                image_key = f"{tab_id}:{image_path}"
                if image_key not in _pending_deletions:
                    _pending_deletions.add(image_key)
                    # Schedule deletion prompt in main thread
                    try:
                        if hasattr(tab_ref, 'master') and tab_ref.master:
                            tab_ref.master.after(0, lambda img=image_path, tab=tab_ref, key=image_key: _handle_image_deletion(img, tab, key))
                        elif hasattr(tab_ref, 'winfo_toplevel'):
                            root = tab_ref.winfo_toplevel()
                            root.after(0, lambda img=image_path, tab=tab_ref, key=image_key: _handle_image_deletion(img, tab, key))
                    except Exception as e:
                        debug_console.log(f"Could not schedule image deletion prompt: {e}", level='ERROR')
                        _handle_image_deletion(image_path, tab_ref, image_key)
        
        if added_images:
            debug_console.log(f"New images detected in tab {tab_id}: {added_images}", level='DEBUG')
        
        # Update tracking data
        tab_data['images'] = current_images
        tab_data['last_content_hash'] = current_hash
            
    except Exception as e:
        debug_console.log(f"Error checking tab {tab_id} for deletions: {e}", level='ERROR')

def _handle_image_deletion(image_path, tab_ref, pending_key):
    """
    Handles image deletion (in the main thread)
    """
    global _pending_deletions
    
    try:
        # Remove from pending to allow future prompts
        if pending_key in _pending_deletions:
            _pending_deletions.remove(pending_key)
            
        absolute_path = _resolve_image_path(tab_ref.file_path, image_path)
        _prompt_for_image_deletion(absolute_path, tab_ref.file_path)
        
    except Exception as e:
        debug_console.log(f"Error handling image deletion for '{image_path}': {e}", level='ERROR')

def start_image_monitoring(current_tab):
    """
    Starts monitoring an editor tab for image reference changes
    
    Args:
        current_tab (EditorTab): The editor tab to monitor
    """
    global _tracked_tabs, _monitor_thread, _monitoring_active
    
    if not current_tab:
        debug_console.log("Cannot start monitoring: no tab provided", level='WARNING')
        return
        
    try:
        tab_id = id(current_tab)
        content = current_tab.get_content()
        if content is None:
            content = ""
            
        current_images = _parse_for_images(content)
        content_hash = _get_content_hash(content)
        
        _tracked_tabs[tab_id] = {
            'images': current_images,
            'last_content_hash': content_hash,
            'last_check_time': time.time(),
            'tab_ref': current_tab
        }
        
        debug_console.log(f"Started monitoring tab {tab_id} with {len(current_images)} images", level='INFO')
        
        # Start monitoring thread if not already active
        if not _monitor_thread or not _monitor_thread.is_alive():
            _monitoring_active = True
            _monitor_thread = threading.Thread(target=_monitor_changes, daemon=True)
            _monitor_thread.start()
            
    except Exception as e:
        debug_console.log(f"Error starting image monitoring: {e}", level='ERROR')

def stop_image_monitoring(current_tab):
    """
    Stops monitoring an editor tab
    
    Args:
        current_tab (EditorTab): The editor tab to stop monitoring
    """
    global _tracked_tabs
    
    if current_tab:
        tab_id = id(current_tab)
        if tab_id in _tracked_tabs:
            del _tracked_tabs[tab_id]
            debug_console.log(f"Stopped monitoring tab {tab_id}", level='INFO')

def force_check_current_tab(current_tab):
    """
    Forces an immediate check of the current tab for image deletions
    
    Args:
        current_tab (EditorTab): The current active editor tab
    """
    global _tracked_tabs, _last_manual_check
    
    if not current_tab:
        return
    
    try:
        current_time = time.time()
        _last_manual_check = current_time
        
        tab_id = id(current_tab)
        if tab_id not in _tracked_tabs:
            start_image_monitoring(current_tab)
        else:
            tab_data = _tracked_tabs[tab_id]
            _check_tab_for_deletions(tab_id, current_tab, tab_data)
            
    except Exception as e:
        debug_console.log(f"Error in force check: {e}", level='ERROR')

def shutdown_image_monitoring():
    """
    Properly shuts down the image monitoring system
    """
    global _monitoring_active, _monitor_thread, _tracked_tabs, _pending_deletions
    
    debug_console.log("Shutting down image monitoring system", level='INFO')
    
    _monitoring_active = False
    if _monitor_thread and _monitor_thread.is_alive():
        _monitor_thread.join(timeout=3)
    
    _tracked_tabs.clear()
    _pending_deletions.clear()
    debug_console.log("Image monitoring system shut down", level='INFO')

def check_for_deleted_images(current_tab):
    """
    Legacy function - now just ensures monitoring is active
    AJOUT SIMPLE : Vérifie aussi les images orphelines au premier appel
    
    Args:
        current_tab (EditorTab): The current active editor tab containing the document.
    """
    debug_console.log("Check for deleted images called - ensuring monitoring is active", level='INFO')
    
    if not current_tab:
        debug_console.log("Skipping image deletion check: No active tab", level='DEBUG')
        return
    
    try:
        # Just ensure monitoring is active - real-time monitoring handles detection
        tab_id = id(current_tab)
        if tab_id not in _tracked_tabs:
            start_image_monitoring(current_tab)
        else:
            debug_console.log("Tab already being monitored - real-time detection active", level='DEBUG')
        
        # AJOUT SIMPLE : Vérifier les orphelins une seule fois par fichier
        if hasattr(current_tab, 'file_path') and current_tab.file_path:
            # Utiliser un attribut du tab pour éviter de refaire la vérification
            if not hasattr(current_tab, '_orphan_check_done'):
                current_tab._orphan_check_done = True
                
                content = current_tab.get_content()
                if content is not None:
                    current_images = _parse_for_images(content)
                    orphaned = _find_orphaned_images(current_tab.file_path, current_images)
                    
                    for orphan_path in orphaned:
                        absolute_path = _resolve_image_path(current_tab.file_path, orphan_path)
                        if os.path.exists(absolute_path):
                            _prompt_for_image_deletion(absolute_path, current_tab.file_path)
            
    except Exception as e:
        debug_console.log(f"Error in check_for_deleted_images: {e}", level='ERROR')