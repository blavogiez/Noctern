"""
Tests for the pre-compiler module.
"""

import pytest
from unittest.mock import MagicMock
from pre_compiler.checker import Checker

@pytest.fixture
def checker():
    """Provides a Checker instance for testing."""
    return Checker()

def test_checker_initialization():
    """Test that the Checker initializes correctly."""
    checker = Checker()
    assert checker is not None
    assert hasattr(checker, 'graphics_ext')
    assert hasattr(checker, 'tex_ext')

def test_check_empty_document(checker):
    """Test checking an empty document returns no errors."""
    text = ""
    errors = checker.check(text)
    assert errors == []

def test_check_document_with_no_errors(checker):
    """Test checking a valid document returns no errors."""
    text = r"""
\documentclass{article}
\begin{document}
Hello World!
\end{document}
"""
    errors = checker.check(text)
    assert errors == []

def test_check_mismatched_braces(checker):
    """Test that mismatched braces are detected."""
    text = r"""
\documentclass{article}
\begin{document}
Hello World!
\end{document
"""
    errors = checker.check(text)
    assert len(errors) > 0
    assert any("Mismatched braces" in error["error"] for error in errors)

def test_check_mismatched_brackets(checker):
    """Test that mismatched brackets are detected."""
    text = r"""
\documentclass{article}
\begin{document}
\section[Hello World!
Content here.
\end{document}
"""
    errors = checker.check(text)
    assert len(errors) > 0
    assert any("Mismatched brackets" in error["error"] for error in errors)

def test_check_missing_input_file(checker):
    """Test that missing input files are detected."""
    text = r"""
\documentclass{article}
\begin{document}
\input{nonexistent_file}
\end{document}
"""
    errors = checker.check(text)
    assert len(errors) > 0
    assert any("Missing TeX file: nonexistent_file" in error["error"] for error in errors)

def test_check_missing_graphics_file(checker):
    """Test that missing graphics files are detected."""
    text = r"""
\documentclass{article}
\begin{document}
\includegraphics{missing_image.png}
\end{document}
"""
    errors = checker.check(text)
    assert len(errors) > 0
    assert any("Missing image: missing_image.png" in error["error"] for error in errors)

def test_check_with_file_path(checker, tmp_path):
    """Test checking with a file path for relative path resolution."""
    # Create a temporary file
    doc_file = tmp_path / "document.tex"
    doc_content = r"""
\documentclass{article}
\begin{document}
\input{missing_file}
\end{document}
"""
    doc_file.write_text(doc_content)
    
    errors = checker.check(doc_content, str(doc_file))
    assert len(errors) > 0
    assert any("Missing TeX file: missing_file" in error["error"] for error in errors)