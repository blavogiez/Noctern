"""
This module defines a custom ttk.Notebook widget with closable tabs and enhanced styling.
"""

import ttkbootstrap as ttk
from tkinter import font

class ClosableNotebook(ttk.Notebook):
    """A ttk.Notebook with a close button and enhanced visual feedback on each tab."""

    __initialized = False

    def __init__(self, *args, **kwargs):
        if not self.__initialized:
            self.__initialize_custom_style()
            self.__initialized = True

        kwargs["style"] = "Closable.TNotebook"
        super().__init__(*args, **kwargs)

        self._active = None

        self.bind("<ButtonPress-1>", self._on_close_press, True)
        self.bind("<ButtonRelease-1>", self._on_close_release)

    def _on_close_press(self, event):
        """Called when the button is pressed."""
        element = self.identify(event.x, event.y)

        if "close" in element:
            index = self.index(f"@{event.x},{event.y}")
            self.state(['pressed'])
            self._active = index
            return "break"

    def _on_close_release(self, event):
        """Called when the button is released."""
        if not self.instate(['pressed']):
            return

        element = self.identify(event.x, event.y)
        if "close" not in element:
            # user moved the mouse off of the close button
            return

        index = self.index(f"@{event.x},{event.y}")

        if self._active == index:
            self.forget(index)
            self.event_generate("<<NotebookTabClosed>>")

        self.state(["!pressed"])
        self._active = None

    def __initialize_custom_style(self):
        style = ttk.Style()

        # Define fonts for normal and selected (italic) tabs
        default_font = font.nametofont("TkDefaultFont")
        self.fonts = {
            "normal": default_font,
            "italic": font.Font(family=default_font.actual("family"), size=default_font.actual("size"), slant="italic")
        }

        self.images = (
            ttk.PhotoImage("img_close", data='''
                R0lGODlhCAAIAMIBAAAAADs7O4+Pj9nZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
                '''),
            ttk.PhotoImage("img_closeactive", data='''
                R0lGODlhCAAIAMIEAAAAAP/SAP/bNNnZ2cbGxsbGxsbGxsbGxiH5BAEKAAQALAAA
                AAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU5kEJADs=
                '''),
            ttk.PhotoImage("img_closepressed", data='''
                R0lGODlhCAAIAMIEAAAAAOUqKv9mZtnZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
            ''')
        )

        style.element_create("close", "image", "img_close",
                            ("active", "img_closeactive"),
                            ("pressed", "img_closepressed"),
                            sticky="e")
        
        style.layout("Closable.TNotebook.Tab", [
            ("Closable.TNotebook.tab", {
                "sticky": "nswe",
                "children": [
                    ("Closable.TNotebook.padding", {
                        "side": "top",
                        "sticky": "nswe",
                        "children": [
                            ("Closable.TNotebook.focus", {
                                "side": "top",
                                "sticky": "nswe",
                                "children": [
                                    ("Closable.TNotebook.label", {"side": "left", "sticky": ''}),
                                    ("close", {"side": "right", "sticky": 'e'}),
                                ]
                            })
                        ]
                    })
                ]
            })
        ])
        
        # Configure the tab style with the normal font by default
        style.configure("Closable.TNotebook.Tab", font=self.fonts["normal"])
        
        # Map styles for different states (selected, active/hover)
        # These colors are subtle and should work with both light and dark themes.
        # You might need to get these from the theme for perfect integration.
        hover_bg_light = "#E0E0E0"
        selected_bg_light = "#F0F0F0"
        hover_bg_dark = "#3E3E3E"
        selected_bg_dark = "#4A4A4A"

        try:
            # Determine colors based on the current theme's background
            theme_bg = str(style.lookup('TNotebook', 'background'))
            is_dark = sum(int(theme_bg[i:i+2], 16) for i in (1, 3, 5)) < 382
            hover_color = hover_bg_dark if is_dark else hover_bg_light
            selected_color = selected_bg_dark if is_dark else selected_bg_light
        except Exception:
            hover_color = hover_bg_dark
            selected_color = selected_bg_dark

        style.map("Closable.TNotebook.Tab",
            font=[("selected", self.fonts["italic"])],
            background=[("active", hover_color), ("selected", selected_color)],
            expand=[("selected", (0, 0, 0, 0))]
        )
        
        style.configure("Closable.TNotebook", tabposition="nw")
