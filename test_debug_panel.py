#!/usr/bin/env python3
"""
Test simple du debug panel pour vérifier que le bouton apparaît.
"""

import tkinter as tk
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_debug_panel():
    """Test de l'interface du debug panel."""
    
    # Créer une fenêtre de test
    root = tk.Tk()
    root.title("Test Debug Panel")
    root.geometry("400x300")
    
    try:
        from debug_system.ui.debug_panel import UltraFastDebugPanel
        
        def on_goto_line(line_num):
            print(f"Navigation vers ligne: {line_num}")
        
        def on_show_diff():
            print("Diff demandé!")
        
        # Créer le debug panel
        debug_panel = UltraFastDebugPanel(
            root,
            on_goto_line=on_goto_line,
            on_show_diff=on_show_diff
        )
        debug_panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Simuler qu'il y a une version précédente
        debug_panel.update_errors([], has_last_version=True)
        
        print("Debug panel créé avec succès!")
        print("Vous devriez voir:")
        print("- Titre: 'Debug'")
        print("- Bouton: 'Compare with last version' (activé)")
        print("- Status: 'Debug available - click Compare button'")
        
        # Afficher la fenêtre
        root.mainloop()
        
    except Exception as e:
        print(f"Erreur lors de la création du debug panel: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_debug_panel()