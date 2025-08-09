"""
Module simplifié pour la navigation des placeholders $element$.
Navigation simple avec Tab vers le prochain placeholder, peu importe où il est.
"""

import tkinter as tk
import re
from utils import debug_console


class PlaceholderManager:
    """Gestionnaire ultra-simple pour naviguer entre les $element$."""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.current_search_pos = "1.0"
        
    def navigate_next(self):
        """Trouve et navigue vers le prochain $element$ après la position actuelle."""
        # Cherche le prochain pattern $...$ à partir de la position actuelle
        pattern = r'\$[^$]+\$'
        
        # Récupère tout le texte depuis la position actuelle
        text_from_current = self.text_widget.get(self.current_search_pos, tk.END)
        
        match = re.search(pattern, text_from_current)
        if not match:
            # Pas trouvé, repart du début
            self.current_search_pos = "1.0"
            text_from_start = self.text_widget.get("1.0", tk.END)
            match = re.search(pattern, text_from_start)
            
            if not match:
                return False  # Aucun placeholder dans tout le texte
        
        # Calcule les positions exactes
        start_offset = match.start()
        end_offset = match.end()
        
        start_pos = f"{self.current_search_pos}+{start_offset}c"
        end_pos = f"{self.current_search_pos}+{end_offset}c"
        
        # Sélectionne le placeholder
        self.text_widget.tag_remove(tk.SEL, "1.0", tk.END)
        self.text_widget.tag_add(tk.SEL, start_pos, end_pos)
        self.text_widget.mark_set(tk.INSERT, start_pos)
        self.text_widget.see(start_pos)
        
        # Met à jour la position pour la prochaine recherche
        self.current_search_pos = end_pos
        
        debug_console.log(f"Navigué vers placeholder: {match.group()}", level='INFO')
        return True
    
    def reset(self):
        """Remet la recherche au début."""
        self.current_search_pos = "1.0"


def handle_placeholder_navigation(event):
    """Gère la navigation par Tab vers le prochain $element$."""
    if not isinstance(event.widget, tk.Text):
        return
        
    text_widget = event.widget
    
    # Crée le manager s'il n'existe pas
    if not hasattr(text_widget, 'placeholder_manager'):
        text_widget.placeholder_manager = PlaceholderManager(text_widget)
        
    manager = text_widget.placeholder_manager
    
    if manager.navigate_next():
        return "break"  # Arrête la propagation du Tab
        
    return None