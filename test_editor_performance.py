#!/usr/bin/env python3
"""Performance tests for optimized editor refresh system."""

import sys
import os
import time
import tkinter as tk
from tkinter import font as tkFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def generate_large_latex_document(lines=20000):
    """Generate a large LaTeX document for performance testing."""
    content = [
        "\\documentclass{article}",
        "\\usepackage{amsmath}",
        "\\usepackage{graphicx}",
        "\\begin{document}",
        "\\title{Large Performance Test Document}",
        "\\maketitle"
    ]
    
    # Add many sections with different structures
    for i in range(1, lines // 25):
        section_content = [
            f"\\section{{Section {i}}}",
            f"This is section {i} with various LaTeX constructs.",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            f"\\textbf{{Bold text in section {i}}} and \\textit{{italic text}}.",
            "% This is a comment that should be highlighted",
            f"Here are some numbers: {i}, {i * 1.5}, {i * 2.75}",
            "\\begin{itemize}",
            f"\\item First item with \\command{{parameter {i}}}",
            f"\\item Second item with more text and {{{i}}} braces",
            f"\\item Third item with [optional] and (parentheses) {i}",
            "\\end{itemize}",
            "\\begin{equation}",
            f"E_{{{i}}} = mc^2 + \\alpha_{{{i}}} \\cdot \\beta^{{{i}}}",
            "\\end{equation}",
            f"\\subsection{{Subsection {i}.1}}",
            "More content with various LaTeX elements:",
            "\\begin{align}",
            f"x &= a + b_{{{i}}} \\\\",
            f"y &= c \\cdot d_{{{i}}} + \\gamma",
            "\\end{align}",
            "",
            f"\\paragraph{{Paragraph {i}}} Additional text content here.",
            f"Reference to equation \\eqref{{eq:{i}}} and figure \\ref{{fig:{i}}}.",
            "",
        ]
        content.extend(section_content)
    
    content.append("\\end{document}")
    return "\n".join(content)

def test_optimized_editor_performance():
    """Test the optimized editor performance system."""
    
    print("Testing optimized editor performance system...\n")
    
    # Create root window
    root = tk.Tk()
    root.withdraw()
    
    try:
        from app.performance_optimizer import (
            schedule_optimized_update, get_optimizer_stats, 
            clear_optimizer_cache, UpdateType
        )
        from editor.tab import EditorTab, LineNumbers
        
        # Test different file sizes
        test_cases = [
            (1000, "Small file"),
            (5000, "Large file"), 
            (15000, "Huge file")
        ]
        
        results = {}
        
        for line_count, description in test_cases:
            print(f"Testing {description} ({line_count} lines)...")
            
            # Generate test content
            content = generate_large_latex_document(line_count)
            
            # Create editor
            editor = tk.Text(root)
            editor.insert("1.0", content)
            
            # Create mock tab
            test_font = tkFont.Font(family="Consolas", size=12)
            mock_tab = MockEditorTab(test_font)
            editor.master = mock_tab
            
            # Test different update types
            update_results = {}
            
            # Test syntax highlighting performance
            start_time = time.perf_counter()
            schedule_optimized_update(editor, {UpdateType.SYNTAX}, force=True)
            root.update()  # Process pending updates
            time.sleep(0.5)  # Wait for updates to complete
            root.update()
            syntax_time = time.perf_counter() - start_time
            update_results['syntax'] = syntax_time
            
            # Test line numbers performance
            line_numbers = LineNumbers(root, editor, test_font)
            start_time = time.perf_counter()
            line_numbers.redraw()
            line_numbers_time = time.perf_counter() - start_time
            update_results['line_numbers'] = line_numbers_time
            
            # Test status update performance
            start_time = time.perf_counter()
            schedule_optimized_update(editor, {UpdateType.STATUS}, force=True)
            root.update()
            time.sleep(0.1)
            root.update()
            status_time = time.perf_counter() - start_time
            update_results['status'] = status_time
            
            # Test combined update performance
            start_time = time.perf_counter()
            schedule_optimized_update(editor, {UpdateType.ALL}, force=True)
            root.update()
            time.sleep(0.5)
            root.update()
            combined_time = time.perf_counter() - start_time
            update_results['combined'] = combined_time
            
            results[description] = update_results
            
            # Print results
            print(f"  Syntax highlighting: {syntax_time*1000:.2f}ms")
            print(f"  Line numbers: {line_numbers_time*1000:.2f}ms")
            print(f"  Status update: {status_time*1000:.2f}ms")
            print(f"  Combined update: {combined_time*1000:.2f}ms")
            print()
            
            # Clean up
            line_numbers.destroy()
        
        # Test cache effectiveness
        print("Testing cache effectiveness...")
        
        # Create identical content
        content = generate_large_latex_document(2000)
        editor1 = tk.Text(root)
        editor1.insert("1.0", content)
        editor1.master = MockEditorTab(test_font)
        
        editor2 = tk.Text(root)  
        editor2.insert("1.0", content)
        editor2.master = MockEditorTab(test_font)
        
        # First update (cache miss)
        start_time = time.perf_counter()
        schedule_optimized_update(editor1, {UpdateType.SYNTAX}, force=True)
        root.update()
        time.sleep(0.3)
        root.update()
        cache_miss_time = time.perf_counter() - start_time
        
        # Second update with identical content (should hit cache)
        start_time = time.perf_counter()
        schedule_optimized_update(editor2, {UpdateType.SYNTAX}, force=True)
        root.update()
        time.sleep(0.3)
        root.update()
        cache_hit_time = time.perf_counter() - start_time
        
        if cache_hit_time > 0:
            cache_speedup = cache_miss_time / cache_hit_time
            print(f"Cache miss: {cache_miss_time*1000:.2f}ms")
            print(f"Cache hit: {cache_hit_time*1000:.2f}ms")
            print(f"Cache speedup: {cache_speedup:.1f}x")
        else:
            print("Cache performance too fast to measure accurately!")
        
        # Get optimizer statistics
        stats = get_optimizer_stats()
        print(f"\nOptimizer statistics: {stats}")
        
        # Performance validation
        print("\n=== PERFORMANCE VALIDATION ===")
        
        # Check if large files perform reasonably
        large_file_time = results["Large file"]["combined"]
        huge_file_time = results["Huge file"]["combined"]
        
        print(f"Large file (5K lines): {large_file_time*1000:.2f}ms")
        print(f"Huge file (15K lines): {huge_file_time*1000:.2f}ms")
        
        # Validate performance benchmarks
        assert large_file_time < 2.0, f"Large file updates too slow: {large_file_time:.3f}s"
        assert huge_file_time < 5.0, f"Huge file updates too slow: {huge_file_time:.3f}s"
        
        # Check scaling is reasonable
        if large_file_time > 0.01:  # Only check if measurable
            scaling_ratio = huge_file_time / large_file_time
            print(f"Scaling ratio (huge/large): {scaling_ratio:.1f}x")
            assert scaling_ratio < 10, f"Poor scaling performance: {scaling_ratio:.1f}x"
        
        print("\n✓ All performance tests passed!")
        print("Optimized editor refresh system is working effectively.")
        
    except ImportError as e:
        print(f"Could not import optimization modules: {e}")
        print("Performance optimization system may not be available.")
        return False
    except Exception as e:
        print(f"Performance test failed: {e}")
        return False
    finally:
        try:
            root.destroy()
        except:
            pass
    
    return True

class MockEditorTab:
    """Mock editor tab for testing."""
    def __init__(self, font):
        self.editor_font = font
        self.line_numbers = None

def test_line_numbers_optimization():
    """Test line numbers optimization specifically."""
    print("Testing line numbers optimization...")
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        # Create large content
        content = generate_large_latex_document(10000)
        editor = tk.Text(root, height=30, width=80)
        editor.insert("1.0", content)
        editor.pack()
        
        test_font = tkFont.Font(family="Consolas", size=12)
        
        # Test optimized line numbers
        from editor.tab import LineNumbers
        
        line_numbers = LineNumbers(root, editor, test_font)
        line_numbers.pack(side="left", fill="y")
        
        # Force update to get real measurements
        root.update()
        
        # Measure redraw performance
        start_time = time.perf_counter()
        for _ in range(5):  # Multiple redraws to get average
            line_numbers.redraw()
        avg_redraw_time = (time.perf_counter() - start_time) / 5
        
        print(f"Average line numbers redraw time: {avg_redraw_time*1000:.2f}ms")
        
        # Test viewport optimization
        start_time = time.perf_counter()
        line_numbers.force_redraw()
        force_redraw_time = time.perf_counter() - start_time
        
        print(f"Force redraw time: {force_redraw_time*1000:.2f}ms")
        
        # Validate performance
        assert avg_redraw_time < 0.1, f"Line numbers redraw too slow: {avg_redraw_time:.3f}s"
        print("✓ Line numbers optimization working correctly!")
        
        line_numbers.destroy()
        
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    print("AutomaTeX Editor Performance Tests")
    print("=" * 50)
    
    try:
        # Test optimized refresh system
        if not test_optimized_editor_performance():
            sys.exit(1)
        
        print()
        
        # Test line numbers specifically  
        test_line_numbers_optimization()
        
        print("\n🎉 All editor performance tests completed successfully!")
        print("The optimized refresh system is working as expected.")
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during testing: {e}")
        sys.exit(1)