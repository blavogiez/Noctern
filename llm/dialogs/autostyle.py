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
        """Creates the dialog body with a slider, labels, and improved layout."""
        container = ttk.Frame(master, padding=10)
        container.pack(fill='both', expand=True)

        # --- Title and Description ---
        title_label = ttk.Label(container, text="Style Intensity", font=("Helvetica", 12, "bold"))
        title_label.pack(pady=(0, 5))
        
        description_label = ttk.Label(
            container, 
            text="Choose the intensity of the styling. A low value means minor changes, while a high value allows for significant reformatting.",
            wraplength=300, 
            justify=tk.LEFT
        )
        description_label.pack(pady=(0, 15))

        # --- Slider and Value Display ---
        slider_frame = ttk.Frame(container)
        slider_frame.pack(fill='x', expand=True, pady=5)

        # Define the label first to ensure it exists for the callback
        self.value_label = ttk.Label(slider_frame, text=f"{self.intensity}", font=("Helvetica", 10, "bold"), width=2)

        self.slider = ttk.Scale(
            slider_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            command=self._on_slider_move
        )
        self.slider.set(self.intensity)
        
        self.slider.pack(side=tk.LEFT, fill='x', expand=True, padx=(5, 10))
        self.value_label.pack(side=tk.RIGHT)

        self.slider.focus_set()
        
        return self.slider # Set initial focus

    def _on_slider_move(self, value):
        """Updates the label as the slider moves."""
        self.intensity = int(float(value))
        self.value_label.config(text=f"{self.intensity}")

    def apply(self):
        """
        This is called when the user clicks OK or presses Enter.
        We update the global state with the final chosen value.
        """
        llm_state.last_style_intensity = self.intensity
        # The result of the dialog is the value of self.intensity
        self.result = self.intensity
