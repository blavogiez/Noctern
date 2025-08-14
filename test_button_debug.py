#!/usr/bin/env python3
"""
Test pour débugger le problème de bouton non cliquable.
"""

import sys
import os
import tkinter as tk
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_button_directly():
    """Test direct du bouton sans passer par l'application."""
    print("Test direct du bouton debug...")
    
    # Créer fenêtre de test
    root = tk.Tk()
    root.title("Test Button Debug")
    root.geometry("500x300")
    
    try:
        from debug_system.ui.debug_panel import UltraFastDebugPanel
        
        def test_goto_line(line):
            print(f"TEST: Navigation vers ligne {line}")
        
        def test_show_diff():
            print("TEST: Diff demandé - SUCCÈS!")
            tk.messagebox.showinfo("Test", "Le bouton fonctionne!")
        
        # Créer le panel directement
        panel = UltraFastDebugPanel(
            root,
            on_goto_line=test_goto_line,
            on_show_diff=test_show_diff
        )
        panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Forcer l'état avec version disponible
        panel.update_errors([], has_last_version=True)
        
        # Ajouter des informations de debug
        info_label = tk.Label(root, text="Cliquez sur le bouton 'Compare with last version'", 
                             font=("Arial", 12, "bold"), fg="blue")
        info_label.pack(side="bottom", pady=10)
        
        print("Interface créée. Testez le bouton manuellement.")
        print("Si le bouton ne réagit pas, il y a un problème de binding.")
        
        root.mainloop()
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ajouter messagebox pour les tests
    import tkinter.messagebox
    test_button_directly()