"""Parse LaTeX log files and extract error messages and warnings."""

import os
import re

def parse_log_file(log_content: str) -> str:
    """Parse LaTeX log file content to extract error summary."""
    if not log_content:
        return "Log content is empty. Nothing to parse."

    lines = log_content.splitlines()
    error_summary = []
    
    line_num_regex = re.compile(r'l\.(\d+)')

    for i, line in enumerate(lines):
        # Priority 1: Specific critical errors
        if "! LaTeX Error: File" in line:
            match = re.search(r"`([^']+\.(sty|cls))' not found", line)
            if match:
                file_type = "Package" if match.group(2) == "sty" else "Class"
                error_summary.append(f"Missing {file_type}: {match.group(1)}")
                continue

        # Priority 2: General errors
        if line.startswith("! "):
            error_message = f"Error: {line[2:].strip()}"
            
            # Search for line number and cause in next lines
            for j in range(i + 1, min(i + 4, len(lines))):
                line_match = line_num_regex.search(lines[j])
                if line_match:
                    if "(at line" not in error_message:
                        error_message += f" (at line {line_match.group(1)})";
                    
                    # Next non-empty line after line number is often the cause
                    if "Undefined control sequence" in error_message:
                        for k in range(j + 1, min(j + 3, len(lines))):
                            cause_line = lines[k].strip()
                            if cause_line:
                                error_message += f"\n  -> Cause: {cause_line}"
                                break  # Found cause, stop searching
                    break  # Found line number, stop searching
            
            error_summary.append(error_message)
            continue

        # Priority 3: Warnings
        if "Overfull \\hbox" in line or "Underfull \\vbox" in line:
            error_summary.append(f"Warning: {line.strip()}")
            continue

    if not error_summary:
        return "No critical errors found in the log file."
        
    return "\n".join(error_summary)

def read_and_parse_log(log_file_path: str) -> str:
    """Read log file from specified path and parse for errors."""
    if not os.path.exists(log_file_path):
        return f"Log file not found at: {log_file_path}"
    try:
        with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return parse_log_file(content)
    except Exception as e:
        return f"An error occurred while reading the log file: {e}"