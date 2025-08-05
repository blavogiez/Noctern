import re

def extract_section_structure(content, position_index):
    """
    Extracts the current section, subsection, and subsubsection titles based on a given character position.

    This function is used to determine the logical location within a LaTeX document
    (e.g., which section an image is being pasted into). It scans backwards from the
    specified position to find the most recent sectioning commands in a hierarchical manner.

    Args:
        content (str): The full text content of the LaTeX document.
        position_index (int): The character index within the content to start the search from.

    Returns:
        tuple: A tuple containing the current section, subsection, and subsubsection titles.
               Defaults to "default" if no specific section is found.
    """
    # Get the content up to the cursor and split into lines
    content_before_cursor = content[:position_index]
    lines = content_before_cursor.split('\n')
    
    # Initialize titles to "default"
    current_section = "default"
    current_subsection = "default"
    current_subsubsection = "default"

    # Regex to capture titles, handling optional arguments and stars
    section_regex = re.compile(r"\\section\*?(?:\\[^\\]*\])?{([^}]+)}")
    subsection_regex = re.compile(r"\\subsection\*?(?:\\[^\\]*\])?{([^}]+)}")
    subsubsection_regex = re.compile(r"\\subsubsection\*?(?:\\[^\\]*\])?{([^}]+)}")

    # Iterate backwards through the lines to find the most recent section commands
    for line in reversed(lines):
        # Once a section is found, we don't need to look for sections in earlier lines
        if current_section == "default":
            match = section_regex.search(line)
            if match:
                current_section = match.group(1).strip()

        # Once a subsection is found, we don't need to look for subsections in earlier lines
        if current_subsection == "default":
            match = subsection_regex.search(line)
            if match:
                current_subsection = match.group(1).strip()

        # Once a subsubsection is found, we don't need to look for them in earlier lines
        if current_subsubsection == "default":
            match = subsubsection_regex.search(line)
            if match:
                current_subsubsection = match.group(1).strip()

    # Hierarchical reset: if a \section is found, reset deeper levels found *before* it.
    # This logic is complex when iterating backwards. A forward pass is more reliable.
    # Let's re-do this with a forward pass for reliability.

    # Reset titles
    current_section, current_subsection, current_subsubsection = "default", "default", "default"

    for line in lines:
        # Match \section
        match = section_regex.search(line)
        if match:
            current_section = match.group(1).strip()
            # When a new section starts, reset subsection and subsubsection
            current_subsection = "default"
            current_subsubsection = "default"
            continue # Continue to next line

        # Match \subsection
        match = subsection_regex.search(line)
        if match:
            current_subsection = match.group(1).strip()
            # When a new subsection starts, reset subsubsection
            current_subsubsection = "default"
            continue # Continue to next line
            
        # Match \subsubsection
        match = subsubsection_regex.search(line)
        if match:
            current_subsubsection = match.group(1).strip()

    return current_section, current_subsection, current_subsubsection
