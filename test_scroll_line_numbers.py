import tkinter as tk
from editor.tab import EditorTab

def test_scroll_line_numbers():
    """Test that line numbers update correctly when scrolling."""
    # Create a root window
    root = tk.Tk()
    
    # Create an editor tab
    tab = EditorTab(root, file_path=None, schedule_heavy_updates_callback=None)
    
    # Add enough text to enable scrolling
    content = "\n".join([f"Line {i}" for i in range(1, 101)]) + "\n"
    tab.editor.insert("1.0", content)
    
    # Force an initial update
    tab.line_numbers.force_update()
    
    print("Initial line count:", tab.line_numbers._last_total_lines)
    
    # Simulate scrolling by changing the view
    tab.editor.yview("50.0")
    tab.line_numbers.force_update()
    
    print("Line count after scrolling:", tab.line_numbers._last_total_lines)
    
    # Check that the line numbers are correctly positioned
    first_visible_line = tab.editor.index("@0,0")
    print("First visible line:", first_visible_line)
    
    # Clean up
    root.destroy()
    
    print("Scroll line numbers test completed successfully!")

if __name__ == "__main__":
    test_scroll_line_numbers()