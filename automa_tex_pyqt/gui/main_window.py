# File: main_window.py
import os
from PyQt6 import QtWidgets, QtCore, QtGui

# Global variables for main widgets and state (managed within this module)
# In PyQt, these are typically members of the MainWindow class.

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutomaTeX v1.0")
        self.setGeometry(100, 100, 1200, 800) # x, y, width, height

        # Central Widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # Remove default margins
        main_layout.setSpacing(5) # Spacing between widgets

        # --- Top Buttons Frame ---
        self.top_frame = QtWidgets.QFrame()
        self.top_frame.setContentsMargins(10, 10, 10, 5) # Padding
        top_layout = QtWidgets.QHBoxLayout(self.top_frame)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(3)
        main_layout.addWidget(self.top_frame)

        # --- Main Splitter (Outline Tree + Editor) ---
        # QSplitter allows resizing the panes by dragging the sash
        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)

        # --- Left Outline Tree Frame ---
        self.outline_frame = QtWidgets.QFrame()
        outline_layout = QtWidgets.QVBoxLayout(self.outline_frame)
        outline_layout.setContentsMargins(0, 0, 0, 0)
        # QTreeView for document outline (requires a model, QTreeWidget is simpler for direct item management)
        self.outline_tree = QtWidgets.QTreeWidget()
        self.outline_tree.setHeaderHidden(True) # Hide header
        outline_layout.addWidget(self.outline_tree)
        self.main_splitter.addWidget(self.outline_frame)
        self.main_splitter.setSizes([250, 950]) # Initial sizes for the panes

        # --- Editor Notebook Frame ---
        self.notebook_frame = QtWidgets.QFrame()
        notebook_layout = QtWidgets.QVBoxLayout(self.notebook_frame) # Corrected: Removed QtWidgets. prefix
        notebook_layout.setContentsMargins(0, 0, 0, 0)

        # Welcome Screen, placed inside the notebook_frame
        self.welcome_screen = QtWidgets.QFrame()
        self.welcome_screen.setContentsMargins(40, 40, 40, 40)
        welcome_layout = QtWidgets.QVBoxLayout(self.welcome_screen)
        welcome_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.welcome_title = QtWidgets.QLabel("Welcome to AutomaTeX")
        self.welcome_title.setFont(QtGui.QFont("Segoe UI", 24, QtGui.QFont.Weight.Bold))
        welcome_layout.addWidget(self.welcome_title)
        
        self.welcome_subtitle = QtWidgets.QLabel("Your AI-powered LaTeX Editor")
        self.welcome_subtitle.setFont(QtGui.QFont("Segoe UI", 14))
        welcome_layout.addWidget(self.welcome_subtitle)
        
        # Frame to hold buttons on the welcome screen
        self.welcome_button_frame = QtWidgets.QFrame()
        welcome_button_layout = QtWidgets.QHBoxLayout(self.welcome_button_frame)
        welcome_button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(self.welcome_button_frame)
        
        notebook_layout.addWidget(self.welcome_screen) # Initially show welcome screen

        self.notebook = QtWidgets.QTabWidget()
        self.notebook.setTabsClosable(True) # Allow closing tabs
        notebook_layout.addWidget(self.notebook) # Notebook is initially hidden

        self.main_splitter.addWidget(self.notebook_frame)

        # --- LLM Progress Bar ---
        self.llm_progress_bar = QtWidgets.QProgressBar()
        self.llm_progress_bar.setRange(0, 0) # Indeterminate mode
        self.llm_progress_bar.hide() # Initially hidden
        main_layout.addWidget(self.llm_progress_bar)

        # --- Status Bar ---
        self.status_bar_label = QtWidgets.QLabel("⏳ Initializing...")
        self.statusBar().addWidget(self.status_bar_label)
        self.statusBar().setStyleSheet("QStatusBar::item { border: 0px solid black };") # Remove border

        # --- Setup UI Buttons (Top Frame) ---
        self.btn_open = QtWidgets.QPushButton("📂 Open")
        self.btn_save = QtWidgets.QPushButton("💾 Save")
        self.btn_save_as = QtWidgets.QPushButton("💾 Save As")
        self.btn_compile = QtWidgets.QPushButton("🛠 Compile")
        self.btn_check = QtWidgets.QPushButton("🔍 Check")
        self.btn_complete = QtWidgets.QPushButton("✨ Complete")
        self.btn_generate = QtWidgets.QPushButton("🎯 Generate")
        self.btn_keywords = QtWidgets.QPushButton("🔑 Keywords")
        self.btn_prompts = QtWidgets.QPushButton("📝 Prompts")
        self.btn_translate = QtWidgets.QPushButton("🌐 Translate")
        self.btn_theme = QtWidgets.QPushButton("🌓 Theme")

        top_layout.addWidget(self.btn_open)
        top_layout.addWidget(self.btn_save)
        top_layout.addWidget(self.btn_save_as)
        top_layout.addWidget(self.btn_compile)
        top_layout.addWidget(self.btn_check)
        top_layout.addWidget(self.btn_complete)
        top_layout.addWidget(self.btn_generate)
        top_layout.addWidget(self.btn_keywords)
        top_layout.addWidget(self.btn_prompts)
        top_layout.addWidget(self.btn_translate)
        top_layout.addStretch(1) # Pushes theme button to the right
        top_layout.addWidget(self.btn_theme)

        # --- Connect Signals (will be connected to actual logic in main.py) ---
        # These connections are placeholders. Actual logic will be connected from main.py
        # after all modules are initialized.
        self.btn_open.clicked.connect(lambda: print("Open clicked"))
        self.btn_save.clicked.connect(lambda: print("Save clicked"))
        self.btn_save_as.clicked.connect(lambda: print("Save As clicked"))
        self.btn_compile.clicked.connect(lambda: print("Compile clicked"))
        self.btn_check.clicked.connect(lambda: print("Check clicked"))
        self.btn_complete.clicked.connect(lambda: print("Complete clicked"))
        self.btn_generate.clicked.connect(lambda: print("Generate clicked"))
        self.btn_keywords.clicked.connect(lambda: print("Keywords clicked"))
        self.btn_prompts.clicked.connect(lambda: print("Prompts clicked"))
        self.btn_translate.clicked.connect(lambda: print("Translate clicked"))
        self.btn_theme.clicked.connect(lambda: print("Theme clicked"))

        # --- Keyboard Shortcuts (Application-wide) ---
        # Actions are a good way to manage shortcuts and connect them to menu items/buttons
        self.action_generate = QtGui.QAction("Generate Text", self)
        self.action_generate.setShortcut(QtGui.QKeySequence("Ctrl+Shift+G"))
        self.addAction(self.action_generate)

        self.action_complete = QtGui.QAction("Complete Text", self)
        self.action_complete.setShortcut(QtGui.QKeySequence("Ctrl+Shift+C"))
        self.addAction(self.action_complete)

        self.action_check = QtGui.QAction("Check LaTeX", self)
        self.action_check.setShortcut(QtGui.QKeySequence("Ctrl+Shift+D"))
        self.addAction(self.action_check)

        self.action_paste_image = QtGui.QAction("Paste Image", self)
        self.action_paste_image.setShortcut(QtGui.QKeySequence("Ctrl+Shift+V"))
        self.addAction(self.action_paste_image)

        self.action_keywords = QtGui.QAction("Set Keywords", self)
        self.action_keywords.setShortcut(QtGui.QKeySequence("Ctrl+Shift+K"))
        self.addAction(self.action_keywords)

        self.action_prompts = QtGui.QAction("Edit Prompts", self)
        self.action_prompts.setShortcut(QtGui.QKeySequence("Ctrl+Shift+P"))
        self.addAction(self.action_prompts)

        self.action_open = QtGui.QAction("Open File", self)
        self.action_open.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        self.addAction(self.action_open)

        self.action_new = QtGui.QAction("New File", self)
        self.action_new.setShortcut(QtGui.QKeySequence.StandardKey.New)
        self.addAction(self.action_new)

        self.action_save = QtGui.QAction("Save File", self)
        self.action_save.setShortcut(QtGui.QKeySequence.StandardKey.Save)
        self.addAction(self.action_save)

        self.action_close_tab = QtGui.QAction("Close Tab", self)
        self.action_close_tab.setShortcut(QtGui.QKeySequence("Ctrl+W"))
        self.addAction(self.action_close_tab)

        self.action_translate = QtGui.QAction("Translate Document", self)
        self.action_translate.setShortcut(QtGui.QKeySequence("Ctrl+T"))
        self.addAction(self.action_translate)

        self.action_zoom_in = QtGui.QAction("Zoom In", self)
        self.action_zoom_in.setShortcut(QtGui.QKeySequence("Ctrl+="))
        self.addAction(self.action_zoom_in)

        self.action_zoom_out = QtGui.QAction("Zoom Out", self)
        self.action_zoom_out.setShortcut(QtGui.QKeySequence("Ctrl+-"))
        self.addAction(self.action_zoom_out)

        # Intercept the window close ('X') button to check for unsaved changes
        # This is done by overriding the closeEvent method.

        # Bind outline tree selection after gui_file_tab_manager is ready
        # This will be connected in main.py
        # self.outline_tree.itemClicked.connect(...) # For QTreeWidget
        # self.outline_tree.clicked.connect(...) # For QTreeView

    def closeEvent(self, event):
        """Handles closing the main window, checking for unsaved changes."""
        # This method will be overridden in main.py after file_tab_manager is initialized
        # For now, just accept the close event.
        event.accept()
