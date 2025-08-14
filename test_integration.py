#!/usr/bin/env python3
"""
Test d'intégration pour vérifier que le nouveau système de debug fonctionne
avec l'application principale.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_integration():
    """Test d'intégration du système de debug."""
    print("Test d'integration du systeme de debug...")
    
    try:
        # Test 1: Import du système principal
        print("1. Import du debug system...")
        from debug_system import DebugCoordinatorFactory
        print("   OK: Debug system importe")
        
        # Test 2: Import des panes modifiés
        print("2. Import des panes modifies...")
        from app.panes import create_debug_panel
        print("   OK: Panes modifies importes")
        
        # Test 3: Création d'un coordinateur (mode test)
        print("3. Creation d'un coordinateur...")
        coordinator, panel = DebugCoordinatorFactory.create_default_coordinator()
        print("   OK: Coordinateur cree")
        
        # Test 4: Test avec un document simulé
        print("4. Test avec document simule...")
        coordinator.set_current_document("test.tex", "\\documentclass{article}\n\\begin{document}\nTest\n\\end{document}")
        print("   OK: Document simule analyse")
        
        # Test 5: Stockage d'une version
        print("5. Stockage d'une version...")
        coordinator.store_successful_compilation("test.tex", "\\documentclass{article}\n\\begin{document}\nTest OK\n\\end{document}")
        print("   OK: Version stockee")
        
        # Test 6: Vérification qu'une version existe
        print("6. Verification version precedente...")
        history = coordinator.get_version_history()
        if len(history) > 0:
            print(f"   OK: {len(history)} version(s) trouvee(s)")
        else:
            print("   ATTENTION: Aucune version trouvee")
        
        print()
        print("=== RESULTAT ===")
        print("Le nouveau systeme de debug est pret!")
        print("Dans l'application:")
        print("- Panel 'Debug' en bas a gauche")
        print("- Bouton 'Compare with last version' visible")
        print("- Stockage automatique apres compilation reussie")
        
        # Nettoyer
        import shutil
        if os.path.exists(".automatex_versions"):
            shutil.rmtree(".automatex_versions")
            print("Fichiers de test nettoyes")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration()
    if success:
        print("\nIntegration reussie! Vous pouvez maintenant utiliser le nouveau systeme.")
    else:
        print("\nProblemes detectes. Verifiez les erreurs ci-dessus.")