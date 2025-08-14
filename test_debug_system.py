#!/usr/bin/env python3
"""
Script de test pour le nouveau système de debug ultra-rapide.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_version_storage():
    """Test du système de stockage des versions."""
    print("Test du stockage des versions...")
    
    from debug_system.storage.file_version_storage import FileVersionStorage
    from datetime import datetime
    
    storage = FileVersionStorage("test_versions")
    
    # Stocker une version
    version_id = storage.store_version(
        "test.tex",
        "\\documentclass{article}\n\\begin{document}\nHello World\n\\end{document}",
        datetime.now(),
        True
    )
    
    print(f"Version stockee: {version_id}")
    
    # Récupérer la dernière version
    last_version = storage.get_last_successful_version("test.tex")
    if last_version:
        print(f"Derniere version recuperee: {last_version['id'][:12]}...")
    else:
        print("Impossible de recuperer la version")
        return False
    
    return True

def test_diff_generator():
    """Test du générateur de diff."""
    print("Test du generateur de diff...")
    
    from debug_system.diff.text_diff_generator import LaTeXDiffGenerator
    
    generator = LaTeXDiffGenerator()
    
    old_content = """\\documentclass{article}
\\begin{document}
\\section{Introduction}
Hello World
\\end{document}"""
    
    new_content = """\\documentclass{article}
\\begin{document}
\\section{Introduction}
\\section{New Section}
Hello World Updated
\\end{document}"""
    
    diff_lines = generator.generate_diff(old_content, new_content)
    stats = generator.get_diff_statistics(diff_lines)
    critical = generator.find_critical_changes(diff_lines)
    
    print(f"Diff genere: {stats['total_lines']} lignes, {len(critical)} changements critiques")
    
    return len(diff_lines) > 0

def test_error_detector():
    """Test du détecteur d'erreurs."""
    print("Test du detecteur d'erreurs...")
    
    from debug_system.detection.compilation_detector import CompilationErrorDetector
    
    detector = CompilationErrorDetector()
    
    # Contenu avec erreurs
    content_with_errors = """\\documentclass{article}
\\begin{document}
\\section{Test
\\begin{itemize}
\\item Test
\\end{itemize}
\\includegraphics{nonexistent.png}
\\end{document"""
    
    errors = detector.detect_errors(content_with_errors, "test.tex")
    
    print(f"Detecteur d'erreurs: {len(errors)} erreurs trouvees")
    for error in errors[:3]:  # Afficher les 3 premières
        print(f"  - L{error.line_number}: {error.error_message}")
    
    return len(errors) > 0

def test_coordinator():
    """Test du coordinateur principal."""
    print("Test du coordinateur...")
    
    try:
        from debug_system import DebugCoordinatorFactory
        
        # Créer un coordinateur en mode test (sans GUI)
        coordinator, _ = DebugCoordinatorFactory.create_default_coordinator()
        
        # Test avec un document simple
        content = """\\documentclass{article}
\\begin{document}
\\section{Test}
Hello World
\\end{document}"""
        
        coordinator.set_current_document("test.tex", content)
        
        # Simuler une compilation réussie
        coordinator.store_successful_compilation("test.tex", content)
        
        # Test du résumé diff (devrait être vide car même contenu)
        summary = coordinator.get_quick_diff_summary()
        
        if summary:
            print(f"Coordinateur fonctionnel: {summary['total_lines']} lignes analysees")
        else:
            print("Coordinateur fonctionnel: aucune difference (normal)")
        
        return True
        
    except Exception as e:
        print(f"Erreur dans le coordinateur: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("Test du systeme de debug ultra-rapide AutomaTeX")
    print("=" * 50)
    
    tests = [
        ("Stockage des versions", test_version_storage),
        ("Générateur de diff", test_diff_generator), 
        ("Détecteur d'erreurs", test_error_detector),
        ("Coordinateur", test_coordinator)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"{name}: REUSSI")
            else:
                print(f"{name}: ECHOUE")
        except Exception as e:
            print(f"{name}: ERREUR - {e}")
        print()
    
    print("=" * 50)
    print(f"Resultats: {passed}/{total} tests reussis")
    
    if passed == total:
        print("Tous les tests sont passes! Le systeme de debug est operationnel.")
    else:
        print("Certains tests ont echoue. Verifiez les erreurs ci-dessus.")
    
    # Nettoyer
    import shutil
    if os.path.exists("test_versions"):
        shutil.rmtree("test_versions")
        print("Fichiers de test nettoyes")

if __name__ == "__main__":
    main()