"""
This module defines the dialog for the autostyle feature, allowing the user
to select a styling intensity using a slider.
"""
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import simpledialog
from llm import state as llm_state

class StyleIntensityDialog(simpledialog.Dialog):
    """A dialog to ask for styling intensity using a slider."""

    def __init__(self, parent, title=None):
        self.intensity = llm_state.last_style_intensity
        super().__init__(parent, title)

    def body(self, master):
        """Creates the dialog body with a slider and a value label."""
        container = ttk.Frame(master)
        
        self.value_label = ttk.Label(container, text=f"Intensity: {self.intensity}/10", font=("Helvetica", 10))
        self.value_label.pack(pady=(5, 0))

        self.slider = ttk.Scale(
            container,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            command=self._on_slider_move
        )
        self.slider.set(self.intensity)
        # Allow the slider to be focused to receive keyboard events
        self.slider.focus_set()
        self.slider.pack(pady=10, padx=10, fill='x', expand=True)
        
        container.pack(padx=20, pady=10)
        return self.slider # Set initial focus

    def _on_slider_move(self, value):
        """Updates the label as the slider moves."""
        self.intensity = int(float(value))
        self.value_label.config(text=f"Intensity: {self.intensity}/10")

    def apply(self):
        """
        This is called when the user clicks OK or presses Enter.
        We update the global state with the final chosen value.
        """
        llm_state.last_style_intensity = self.intensity
        # The result of the dialog is the value of self.intensity
        self.result = self.intensity
