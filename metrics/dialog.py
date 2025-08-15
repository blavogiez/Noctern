import tkinter as tk
from tkinter import ttk
from metrics import manager

def open_metrics_dialog(parent):
    """Open window displaying token usage metrics."""
    dialog = tk.Toplevel(parent)
    dialog.title("Métriques d'utilisation de l'IA")
    dialog.geometry("600x400")
    dialog.transient(parent)
    dialog.grab_set()

    # Create treeview for displaying data
    tree = ttk.Treeview(dialog, columns=("date", "input", "output", "total"), show="headings")
    tree.heading("date", text="Date")
    tree.heading("input", text="Tokens d'entrée")
    tree.heading("output",text="Tokens de sortie")
    tree.heading("total", text="Total")

    tree.column("date", anchor=tk.W, width=120)
    tree.column("input", anchor=tk.E, width=120)
    tree.column("output", anchor=tk.E, width=120)
    tree.column("total", anchor=tk.E, width=120)

    tree.pack(expand=True, fill="both", padx=10, pady=10)

    # Load and display data
    metrics = manager.load_metrics()
    total_input = 0
    total_output = 0

    # Sort date keys
    sorted_dates = sorted(metrics.keys())

    for date_str in sorted_dates:
        data = metrics[date_str]
        input_tokens = data.get("input", 0)
        output_tokens = data.get("output", 0)
        total_tokens = input_tokens + output_tokens
        
        tree.insert("", tk.END, values=(date_str, input_tokens, output_tokens, total_tokens))

        total_input += input_tokens
        total_output += output_tokens

    # Total row
    total_all = total_input + total_output
    tree.insert("", tk.END, values=("Total", total_input, total_output, total_all), tags=("total_row",))

    # Style for total row
    tree.tag_configure("total_row", font=("", 10, "bold"))

    # Close button
    close_button = ttk.Button(dialog, text="Fermer", command=dialog.destroy)
    close_button.pack(pady=10)

    dialog.wait_window()
