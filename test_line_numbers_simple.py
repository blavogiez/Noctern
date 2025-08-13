import tkinter as tk
from editor.tab import EditorTab

# Create a root window
root = tk.Tk()

# Create an editor tab
tab = EditorTab(root, file_path=None, schedule_heavy_updates_callback=None)

# Add some text
tab.editor.insert("1.0", "Line 1\nLine 2\nLine 3\n")

# Force an update
tab.line_numbers.redraw()

print("Line count:", tab.line_numbers._last_total_lines)

# Add more text
tab.editor.insert("4.0", "Line 4\nLine 5\n")

# Force an update
tab.line_numbers.redraw()

print("Line count after adding more text:", tab.line_numbers._last_total_lines)

# Clean up
root.destroy()

print("Test completed successfully!")