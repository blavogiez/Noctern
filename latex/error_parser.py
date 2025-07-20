"""
This module provides functions to parse LaTeX log files and extract relevant
error messages, warnings, and other important information in a structured and
human-readable format.
"""


import os

def parse_log_file(log_content: str) -> str:
    """
    Parses the content of a LaTeX .log file to extract a summary of errors.

    This function iterates through the log file line by line, identifies key
    error messages, and formats them into a concise summary. It avoids using
    regular expressions for simplicity and performance, relying instead on
    string matching for common LaTeX error patterns.

    Args:
        log_content: A string containing the full content of the .log file.

    Returns:
        A formatted string summarizing the errors found in the log. If no
        significant errors are found, it may return a generic message.
    """
    if not log_content:
        return "Log content is empty. Nothing to parse."

    lines = log_content.splitlines()
    error_summary = []
    capturing = False
    line_number = 0

    for i, line in enumerate(lines):
        # --- Error Detection ---
        # Standard LaTeX errors start with "! ".
        if line.startswith("! "):
            capturing = True
            error_summary.append(f"Error: {line[2:]}")
            # Try to find the line number where the error occurred.
            # LaTeX often reports this in the lines immediately preceding the error.
            for j in range(max(0, i - 5), i):
                if "l." in lines[j]:
                    try:
                        # Extract line number, e.g., from "l.123 ...".
                        num_str = lines[j].split("l.")[1].split(" ")[0]
                        line_number = int(num_str)
                        error_summary[-1] += f" (at line {line_number})"
                        break
                    except (ValueError, IndexError):
                        pass  # Ignore if parsing fails.

        # --- Undefined Control Sequence ---
        # A common and critical error.
        elif "Undefined control sequence." in line and capturing:
            error_summary.append(f"  -> Cause: {line.strip()}")

        # --- Missing Packages or Files ---
        # Errors related to missing .sty (style) or .cls (class) files.
        elif line.startswith("LaTeX Error: File") and ".sty' not found" in line:
            error_summary.append(f"Missing Package: {line.split('`')[1]}")
        elif line.startswith("LaTeX Error: File") and ".cls' not found" in line:
            error_summary.append(f"Missing Class: {line.split('`')[1]}")

        # --- Bad Box Warnings ---
        # Overfull/underfull hbox/vbox warnings are common but less critical.
        # We can choose to include them if needed, but they are often noisy.
        elif "Overfull \\hbox" in line or "Underfull \\vbox" in line:
            if "badness" in line: # Filter for significant badness levels if desired.
                error_summary.append(f"Warning: {line.strip()}")

        # --- Stop Capturing ---
        # Errors often end with a line starting with 'Here is how much of TeX's memory you used'.
        # Or when a new section of the log begins.
        elif capturing and (line.startswith("Here is how much") or line.startswith("Total time")):
            capturing = False
            error_summary.append("-" * 20) # Separator for clarity.

    if not error_summary:
        return "No critical errors found in the log file."

    # Join the collected summary lines into a single string.
    return "\n".join(error_summary)

def read_and_parse_log(log_file_path: str) -> str:
    """
    Reads a .log file from the specified path and parses it for errors.

    This is a convenience wrapper around `parse_log_file`.

    Args:
        log_file_path: The absolute path to the LaTeX .log file.

    Returns:
        A formatted string with the error summary, or an error message
        if the file cannot be read.
    """
    if not os.path.exists(log_file_path):
        return f"Log file not found at: {log_file_path}"
    try:
        with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return parse_log_file(content)
    except Exception as e:
        return f"An error occurred while reading the log file: {e}"

