"""
This module defines a custom ttk.Notebook widget with closable tabs and enhanced styling.
"""

import ttkbootstrap as ttk
from tkinter import font
from PIL import Image, ImageDraw, ImageTk
import io

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
            # Handle mouse movement off close button
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

        self._create_close_images()

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
                                    ("Closable.TNotebook.label", {"side": "left", "sticky": 'w'}),
                                    ("close", {"side": "right", "sticky": 'ns'}),
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
        # Colors will be applied by the theme manager
        style.map("Closable.TNotebook.Tab",
            font=[("selected", self.fonts["italic"])],
            expand=[("selected", (0, 0, 0, 0))]
        )
        
        style.configure("Closable.TNotebook", tabposition="nw")

    def _create_close_images(self, color="#666666"):
        """Create close button images with the specified color."""
        size = 8
        
        # Create normal close image
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line([(1, 1), (size-2, size-2)], fill=color, width=1)
        draw.line([(1, size-2), (size-2, 1)], fill=color, width=1)
        
        # Convert to PhotoImage
        self.images = []
        self.images.append(ImageTk.PhotoImage(img, name="img_close"))
        
        # Active (hover) - slightly brighter
        active_color = self._brighten_color(color, 0.3)
        img_active = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw_active = ImageDraw.Draw(img_active)
        draw_active.line([(1, 1), (size-2, size-2)], fill=active_color, width=2)
        draw_active.line([(1, size-2), (size-2, 1)], fill=active_color, width=2)
        self.images.append(ImageTk.PhotoImage(img_active, name="img_closeactive"))
        
        # Pressed - red
        img_pressed = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw_pressed = ImageDraw.Draw(img_pressed)
        draw_pressed.line([(1, 1), (size-2, size-2)], fill="#FF4444", width=2)
        draw_pressed.line([(1, size-2), (size-2, 1)], fill="#FF4444", width=2)
        self.images.append(ImageTk.PhotoImage(img_pressed, name="img_closepressed"))

    def _brighten_color(self, hex_color, factor):
        """Brighten a hex color by a factor (0.0 to 1.0)."""
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def update_fonts(self):
        """Update fonts when theme changes."""
        style = ttk.Style()
        default_font = font.nametofont("TkDefaultFont")
        self.fonts = {
            "normal": default_font,
            "italic": font.Font(family=default_font.actual("family"), size=default_font.actual("size"), slant="italic")
        }
        style.configure("Closable.TNotebook.Tab", font=self.fonts["normal"])
        style.map("Closable.TNotebook.Tab",
            font=[("selected", self.fonts["italic"])],
            expand=[("selected", (0, 0, 0, 0))]
        )

    def update_close_button_color(self, color="#666666"):
        """Update close button color for theme changes."""
        try:
            self._create_close_images(color)
        except Exception:
            pass  # Fallback to current images if creation fails
