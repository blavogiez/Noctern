#!/usr/bin/env python3
"""
Test rapide pour identifier le problème avec le bouton.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test 1: Import and creation
print("=== TEST 1: Import et création ===")
try:
    from app.panes import create_debug_panel
    print("✓ Import réussi")
    
    # Simuler un parent pour le test
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Hide main window
    frame = tk.Frame(root)
    
    def test_goto(line):
        print(f"Navigation test vers ligne {line}")
    
    # Create debug panel
    coordinator, panel = create_debug_panel(frame, on_goto_line=test_goto)
    print(f"✓ Coordinator créé: {coordinator is not None}")
    print(f"✓ Panel créé: {panel is not None}")
    
    if coordinator:
        # Test with simulated document
        coordinator.set_current_document("test.tex", "\\documentclass{article}\n\\begin{document}\nTest\n\\end{document}")
        
        # Store version to enable button
        coordinator.store_successful_compilation("test.tex", "\\documentclass{article}\n\\begin{document}\nVersion OK\n\\end{document}")
        
        print("✓ Document and version stored")
    
    root.destroy()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Direct callback test
print("\n=== TEST 2: Direct callback test ===")
try:
    from debug_system.debug_coordinator import DebugCoordinator
    from debug_system.storage.file_version_storage import FileVersionStorage
    from debug_system.diff.text_diff_generator import LaTeXDiffGenerator
    from debug_system.detection.compilation_detector import CompilationErrorDetector
    
    # Create minimal coordinator
    storage = FileVersionStorage("test_debug")
    diff_gen = LaTeXDiffGenerator() 
    detector = CompilationErrorDetector()
    
    coordinator = DebugCoordinator(storage, diff_gen, detector, None, None)
    
    # Test callback
    coordinator.set_current_document("test.tex", "\\documentclass{article}\n\\begin{document}\nNew version\n\\end{document}")
    coordinator.store_successful_compilation("test.tex", "\\documentclass{article}\n\\begin{document}\nOld version\n\\end{document}")
    
    print("Testing show_diff_with_last_version...")
    coordinator.show_diff_with_last_version()
    
    # Clean up
    import shutil
    if os.path.exists("test_debug"):
        shutil.rmtree("test_debug")
    
    print("✓ Callback test completed")
    
except Exception as e:
    print(f"✗ Callback error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== SUMMARY ===")
print("If tests pass, the problem is with AutomaTeX integration")
print("If they fail, the problem is with the system itself")
print("Check DEBUG messages in AutomaTeX console")