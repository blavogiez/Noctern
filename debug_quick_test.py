#!/usr/bin/env python3
"""
Test rapide pour identifier le problème avec le bouton.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test 1: Import et création
print("=== TEST 1: Import et création ===")
try:
    from app.panes import create_debug_panel
    print("✓ Import réussi")
    
    # Simuler un parent pour le test
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale
    frame = tk.Frame(root)
    
    def test_goto(line):
        print(f"Navigation test vers ligne {line}")
    
    # Créer le debug panel
    coordinator, panel = create_debug_panel(frame, on_goto_line=test_goto)
    print(f"✓ Coordinator créé: {coordinator is not None}")
    print(f"✓ Panel créé: {panel is not None}")
    
    if coordinator:
        # Test avec un document simulé
        coordinator.set_current_document("test.tex", "\\documentclass{article}\n\\begin{document}\nTest\n\\end{document}")
        
        # Stocker une version pour activer le bouton
        coordinator.store_successful_compilation("test.tex", "\\documentclass{article}\n\\begin{document}\nVersion OK\n\\end{document}")
        
        print("✓ Document et version stockés")
    
    root.destroy()
    
except Exception as e:
    print(f"✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Test de callback direct
print("\n=== TEST 2: Test callback direct ===")
try:
    from debug_system.debug_coordinator import DebugCoordinator
    from debug_system.storage.file_version_storage import FileVersionStorage
    from debug_system.diff.text_diff_generator import LaTeXDiffGenerator
    from debug_system.detection.compilation_detector import CompilationErrorDetector
    
    # Créer un coordinateur minimal
    storage = FileVersionStorage("test_debug")
    diff_gen = LaTeXDiffGenerator() 
    detector = CompilationErrorDetector()
    
    coordinator = DebugCoordinator(storage, diff_gen, detector, None, None)
    
    # Test du callback
    coordinator.set_current_document("test.tex", "\\documentclass{article}\n\\begin{document}\nNew version\n\\end{document}")
    coordinator.store_successful_compilation("test.tex", "\\documentclass{article}\n\\begin{document}\nOld version\n\\end{document}")
    
    print("Testing show_diff_with_last_version...")
    coordinator.show_diff_with_last_version()
    
    # Nettoyer
    import shutil
    if os.path.exists("test_debug"):
        shutil.rmtree("test_debug")
    
    print("✓ Test callback terminé")
    
except Exception as e:
    print(f"✗ Erreur callback: {e}")
    import traceback
    traceback.print_exc()

print("\n=== RÉSUMÉ ===")
print("Si les tests passent, le problème vient de l'intégration dans AutomaTeX")
print("Si ils échouent, le problème vient du système lui-même")
print("Vérifiez les messages DEBUG dans la console d'AutomaTeX")