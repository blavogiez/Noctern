"""Tests for the LaTeX log file error parser."""

import pytest
from latex import error_parser

# --- Test Data ---

# A sample log with a common "Undefined control sequence" error.
LOG_WITH_UNDEFINED_SEQUENCE = """
This is a LaTeX log file.
Some information here.
...
(./document.tex
! Undefined control sequence.
l.25 \mycomand
               
The control sequence at the end of the top line
of your error message was never \def'ed.
...
Here is how much of TeX's memory you used
"""

# A sample log with a missing package error.
LOG_WITH_MISSING_PACKAGE = """
This is another part of the log.
...
! LaTeX Error: File `nonexistentpackage.sty' not found.

Type X to quit or <RETURN> to proceed,
or enter new name. (Default extension: sty)
...
"""

# A sample log with a typical "Overfull hbox" warning.
LOG_WITH_BAD_BOX = """
Some text processing.
...
Overfull \hbox (10.5pt too wide) in paragraph at lines 42--45
[]\OT1/cmr/m/n/10 Hello, this is a very long line that will cause an overfull hbox warning in our document.
...
"""

# A clean log file with no errors.
LOG_WITHOUT_ERRORS = """
This is the log file of a successful compilation.
(./document.tex)
No errors.
...
Output written on document.pdf (1 page, 12345 bytes).
Transcript written on document.log.
"""

# --- Test Cases ---

def test_parse_undefined_control_sequence():
    """
    Tests if the parser correctly identifies an 'Undefined control sequence' error
    and extracts the line number.
    """
    # Act
    summary = error_parser.parse_log_file(LOG_WITH_UNDEFINED_SEQUENCE)
    
    # Assert
    assert "Error: Undefined control sequence." in summary
    assert "(at line 25)" in summary
    assert "Cause: The control sequence at the end of the top line" in summary

def test_parse_missing_package():
    """
    Tests if the parser correctly identifies a missing .sty file error.
    """
    # Act
    summary = error_parser.parse_log_file(LOG_WITH_MISSING_PACKAGE)
    
    # Assert
    assert "Missing Package: nonexistentpackage.sty" in summary

def test_parse_bad_box_warning():
    """
    Tests if the parser correctly identifies an 'Overfull hbox' warning.
    """
    # Act
    summary = error_parser.parse_log_file(LOG_WITH_BAD_BOX)
    
    # Assert
    assert "Warning: Overfull \\hbox" in summary

def test_parse_clean_log():
    """
    Tests that the parser returns the correct message for a log with no errors.
    """
    # Act
    summary = error_parser.parse_log_file(LOG_WITHOUT_ERRORS)
    
    # Assert
    assert summary == "No critical errors found in the log file."

def test_parse_empty_log():
    """
    Tests that the parser handles empty log content gracefully.
    """
    # Act
    summary = error_parser.parse_log_file("")
    
    # Assert
    assert summary == "Log content is empty. Nothing to parse."

def test_parse_log_with_multiple_errors():
    """
    Tests if the parser can find multiple different issues in a single log.
    """
    # Arrange
    combined_log = LOG_WITH_UNDEFINED_SEQUENCE + "\n" + LOG_WITH_MISSING_PACKAGE
    
    # Act
    summary = error_parser.parse_log_file(combined_log)
    
    # Assert
    assert "Error: Undefined control sequence." in summary
    assert "Missing Package: nonexistentpackage.sty" in summary