import tkinter as tk
from tkinter import messagebox
import time

try:
    import webview
    _WEBVIEW_AVAILABLE = True
except ImportError:
    _WEBVIEW_AVAILABLE = False
    print("Warning: pywebview module not found. Ace Editor integration will be disabled.")

_get_current_tab_func = None
_schedule_heavy_updates_callback = None
_apply_theme_callback = None
_root = None
_perform_heavy_updates_cb = None
_status_message_func = None

_tabs_dict = None # NEW: To hold a reference to the tabs dictionary
_active_editor_content = {}

html_ace_editor = """
<!DOCTYPE html>
<html>
<head>
    <title>Ace Editor</title>
    <style>
        html, body, #editor {
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        #editor {
            width: 100vw;
            height: 100vh;
        }
    </style>
</head>
<body>
    <div id="editor"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ace/1.23.4/ace.js"></script>
    <script>
        var editor = ace.edit("editor");
        editor.setTheme("ace/theme/monokai");
        editor.session.setMode("ace/mode/latex");
        editor.setOptions({ fontSize: "14pt", wrap: true, scrollPastEnd: 0.5, autoScrollEditorIntoView: true });

        var tabId = null;
        editor.setTabId = function(id) { tabId = id; };
        editor.getTabId = function() { return tabId; };

        window.getEditorContent = function(tabId) {
            if (editor.getTabId() == tabId) {
                return editor.getValue();
            } else {
                return null;
            }
        };

        window.setEditorContent = function(tabId, content) {
            if (editor.getTabId() == tabId) {
                editor.setValue(content || "", -1);
                editor.scrollToLine(0);
                editor.moveCursorTo(0, 0);
            }
        };

        window.setTheme = function(theme) {
            editor.setTheme("ace/theme/" + theme);
        };

        window.setFontSize = function(size) {
            editor.setOptions({ fontSize: size + "pt" });
        };

        editor.session.on('change', function(delta) {
            if (window.pywebview && window.pywebview.api && editor.getTabId() !== null) {
                window.pywebview.api.onEditorChange(editor.getTabId(), editor.getValue());
            }
        });

        editor.selection.on('changeCursor', function() {
            if (window.pywebview && window.pywebview.api && editor.getTabId() !== null) {
                var cursor = editor.getCursorPosition();
                window.pywebview.api.onCursorPositionChange(editor.getTabId(), cursor.row + 1, cursor.column);
            }
        });

        editor.focus();
    </script>
</body>
</html>
"""

class AceApi:
    def __init__(self):
        pass

    def onEditorChange(self, tab_id, content):
        tab = _get_current_tab_func()
        if tab and hasattr(tab, "editor_id") and tab.editor_id == tab_id:
            _active_editor_content[tab_id] = content
            tab.schedule_heavy_updates()
            if content != getattr(tab, "last_saved_content", ""):
                if not tab.is_dirty():
                    tab.editor.edit_modified(True)
                    tab.update_tab_title()
            else:
                if tab.is_dirty():
                    tab.editor.edit_modified(False)
                    tab.update_tab_title()
        return True

    def onCursorPositionChange(self, tab_id, line, col):
        tab = _get_current_tab_func()
        if tab and hasattr(tab, "editor_id") and tab.editor_id == tab_id:
            if _status_message_func:
                _status_message_func(f"Ln: {line}, Col: {col}")
        return True

def initialize(get_current_tab_func, schedule_heavy_updates_callback, apply_theme_callback, root_ref, perform_heavy_updates_cb, status_message_func, tabs_dict_ref):
    global _get_current_tab_func, _schedule_heavy_updates_callback, _apply_theme_callback, _root, _perform_heavy_updates_cb, _status_message_func, _tabs_dict
    _get_current_tab_func = get_current_tab_func
    _schedule_heavy_updates_callback = schedule_heavy_updates_callback
    _apply_theme_callback = apply_theme_callback
    _root = root_ref
    _perform_heavy_updates_cb = perform_heavy_updates_cb
    _status_message_func = status_message_func
    _tabs_dict = tabs_dict_ref # NEW

    # REMOVE: Do NOT create a dummy hidden window here.
    # if _WEBVIEW_AVAILABLE:
    #     webview.create_window('AutomaTeX Master Webview', html='<html><body>Loading...</body></html>', hidden=True)

def create_or_attach_ace_to_parent(tab, parent):
    if not _WEBVIEW_AVAILABLE:
        return
    # Always try to create Ace if not present, and always show/resize if present
    if hasattr(parent, "_ace_webview_instance"):
        try:
            # Show and resize the webview if already present
            parent._ace_webview_instance.show()
            parent._ace_webview_instance.resize(parent.winfo_width(), parent.winfo_height())
        except Exception as e:
            print(f"Error resizing or showing Ace Editor webview: {e}")
        return
    # Only create Ace window if parent is mapped (Tkinter mainloop started)
    if not parent.winfo_ismapped():
        parent.after(100, lambda: create_or_attach_ace_to_parent(tab, parent))
        return
    try:
        # Create the Ace webview window and embed it in the parent
        parent._ace_webview_instance = webview.create_window(
            f"Ace Editor {tab.editor_id}",
            html=html_ace_editor,
            js_api=AceApi(),
            resizable=True,
            hidden=False,
            width=parent.winfo_width(),
            height=parent.winfo_height()
        )
        parent._ace_webview_instance.tab_id = tab.editor_id
        parent._ace_webview_instance.show()
    except Exception as e:
        print(f"Error creating Ace Editor webview: {e}")
        parent.after(300, lambda: create_or_attach_ace_to_parent(tab, parent))

class AceEditorIntegration:
    """
    A class that mimics the tk.Text API to allow the rest of the application
    to interact with the Ace webview editor without major refactoring.
    """
    def __init__(self, tab):
        self.tab = tab

    def _get_window(self):
        if self.tab and hasattr(self.tab, 'ace_frame') and hasattr(self.tab.ace_frame, '_ace_webview_instance'):
            return self.tab.ace_frame._ace_webview_instance
        return None

    def get(self, start, end=None):
        return get_editor_content(self.tab.editor_id)

    def edit_modified(self, modified=None):
        if modified is None:
            return self.tab.is_dirty()
        else:
            if not modified:
                self.tab.last_saved_content = get_editor_content(self.tab.editor_id)
            self.tab.update_tab_title()

    def see(self, index):
        try:
            win = self._get_window()
            if win:
                line, col = map(int, index.split('.'))
                win.evaluate_js(f"editor.gotoLine({line}, {col}, true);")
        except Exception as e:
            print(f"Error in 'see' for Ace Editor: {e}")

    def focus(self):
        try:
            win = self._get_window()
            if win:
                win.evaluate_js("editor.focus();")
        except Exception as e:
            print(f"Error in 'focus' for Ace Editor: {e}")

    # --- Methods that can be no-ops or return dummy values for compatibility ---
    def edit_reset(self): pass
    def bind(self, *args, **kwargs): pass
    def config(self, **kwargs): pass
    def configure(self, **kwargs): pass
    def tag_configure(self, *args, **kwargs): pass
    def tag_remove(self, *args, **kwargs): pass
    def tag_add(self, *args, **kwargs): pass
    def tag_ranges(self, *args, **kwargs): return ()
    def mark_set(self, *args, **kwargs): pass
    def mark_gravity(self, *args, **kwargs): pass
    def window_create(self, *args, **kwargs): pass
    def delete(self, *args, **kwargs): pass
    def insert(self, *args, **kwargs): pass
    def winfo_height(self): return 1000
    def index(self, *args, **kwargs): return "1.0"
    def count(self, *args, **kwargs): return (len(self.get("1.0", "end-1c")),)

import re

def get_editor_content(editor_id):
    """Returns the current content for the given editor_id from Ace."""
    return _active_editor_content.get(editor_id, "")

def set_editor_content(editor_id, content):
    """Sets the content for the given editor_id in Ace."""
    # Try to find the webview window for this editor_id and set content via JS
    if not _WEBVIEW_AVAILABLE:
        _active_editor_content[editor_id] = content
        return
    try:
        for win in webview.windows:
            if hasattr(win, 'tab_id') and win.tab_id == editor_id:
                win.evaluate_js(f"window.setEditorContent('{editor_id}', {repr(content)})")
                _active_editor_content[editor_id] = content
                break
    except Exception as e:
        print(f"Error setting editor content in Ace Editor: {e}")