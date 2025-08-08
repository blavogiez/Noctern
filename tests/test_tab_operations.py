"""
Tests for the tab operations module.
"""

import pytest
from unittest.mock import MagicMock, call

# Since this test file is in the tests/ directory, we need to adjust the path
# to import from the app/ directory. Pytest handles this with the pythonpath config.
from app import tab_operations

# A mock EditorTab class that simulates the real one for testing purposes.
class MockEditorTab:
    _tab_count = 0

    def __init__(self, parent, file_path, schedule_heavy_updates_callback):
        self.parent = parent
        self.file_path = file_path
        # Simulate a unique Tkinter widget path for each tab instance.
        self.widget_path = f".!notebook.!tab{MockEditorTab._tab_count}"
        MockEditorTab._tab_count += 1

    def load_file(self):
        """Mock method for file loading."""
        pass

    def __str__(self):
        """The string representation is used as the key in the open_tabs_dict."""
        return self.widget_path

@pytest.fixture(autouse=True)
def reset_mock_tab_counter():
    """Ensures the mock tab counter is reset before each test."""
    MockEditorTab._tab_count = 0

@pytest.fixture
def mock_notebook():
    """Provides a mock ttk.Notebook widget."""
    notebook = MagicMock()
    # The list of tab IDs the notebook is managing.
    managed_tabs = []
    notebook.tabs.return_value = managed_tabs
    
    # Simulate the .add() method to update the list of managed tabs.
    def add_tab(tab, text):
        managed_tabs.append(str(tab))
    notebook.add.side_effect = add_tab
    
    # Mock the after method
    notebook.after = MagicMock()
    
    return notebook

@pytest.fixture
def mock_callbacks():
    """Provides a dictionary of mock callback functions."""
    return {
        "apply_theme": MagicMock(),
        "on_tab_changed": MagicMock(),
        "schedule_heavy_updates": MagicMock(),
    }

def test_create_new_tab_for_new_file(mock_notebook, mock_callbacks):
    """
    Tests that a new tab is successfully created when the file is not already open.
    """
    # Arrange
    file_path = "/path/to/new_file.tex"
    open_tabs = {}

    # Act
    tab_operations.create_new_tab(
        file_path=file_path,
        notebook_widget=mock_notebook,
        open_tabs_dict=open_tabs,
        apply_theme_callback=mock_callbacks["apply_theme"],
        on_tab_changed_callback=mock_callbacks["on_tab_changed"],
        EditorTab_class=MockEditorTab,
        schedule_heavy_updates_callback=mock_callbacks["schedule_heavy_updates"]
    )

    # Assert
    mock_notebook.add.assert_called_once() # A new tab should be added.
    mock_notebook.select.assert_called_once() # The new tab should be selected.
    assert len(open_tabs) == 1 # The tab should be registered in the dictionary.
    assert list(open_tabs.values())[0].file_path == file_path
    # Callbacks for a new tab should be triggered.
    mock_callbacks["apply_theme"].assert_called_once()
    # Check that after was called to schedule on_tab_changed
    mock_notebook.after.assert_called_once()

def test_create_new_tab_for_existing_file(mock_notebook, mock_callbacks):
    """
    Tests that if a file is already open, the existing tab is selected
    and no new tab is created. This validates the recent bug fix.
    """
    # Arrange
    existing_file_path = "/path/to/existing_file.tex"
    
    # Simulate an already open tab environment.
    existing_tab = MockEditorTab(mock_notebook, existing_file_path, mock_callbacks["schedule_heavy_updates"])
    open_tabs = {str(existing_tab): existing_tab}
    # The notebook is already managing this one tab.
    mock_notebook.tabs.return_value.append(str(existing_tab))

    # Act
    tab_operations.create_new_tab(
        file_path=existing_file_path,
        notebook_widget=mock_notebook,
        open_tabs_dict=open_tabs,
        apply_theme_callback=mock_callbacks["apply_theme"],
        on_tab_changed_callback=mock_callbacks["on_tab_changed"],
        EditorTab_class=MockEditorTab,
        schedule_heavy_updates_callback=mock_callbacks["schedule_heavy_updates"]
    )

    # Assert
    mock_notebook.add.assert_not_called() # No new tab should be added.
    mock_notebook.select.assert_called_once_with(str(existing_tab)) # The existing tab should be selected.
    assert len(open_tabs) == 1 # The dictionary of open tabs should not change.
    # Callbacks for creating a new tab should NOT be triggered.
    mock_callbacks["apply_theme"].assert_not_called()
    mock_callbacks["on_tab_changed"].assert_not_called()
    mock_notebook.after.assert_not_called()

def test_create_new_tab_without_file_path(mock_notebook, mock_callbacks):
    """
    Tests that a new tab is successfully created when no file path is provided.
    """
    # Arrange
    file_path = None
    open_tabs = {}

    # Act
    tab_operations.create_new_tab(
        file_path=file_path,
        notebook_widget=mock_notebook,
        open_tabs_dict=open_tabs,
        apply_theme_callback=mock_callbacks["apply_theme"],
        on_tab_changed_callback=mock_callbacks["on_tab_changed"],
        EditorTab_class=MockEditorTab,
        schedule_heavy_updates_callback=mock_callbacks["schedule_heavy_updates"]
    )

    # Assert
    mock_notebook.add.assert_called_once()
    mock_notebook.select.assert_called_once()
    assert len(open_tabs) == 1
    assert list(open_tabs.values())[0].file_path == file_path
    mock_callbacks["apply_theme"].assert_called_once()
    mock_notebook.after.assert_called_once()

def test_create_multiple_tabs(mock_notebook, mock_callbacks):
    """
    Tests that multiple tabs can be created and managed correctly.
    """
    # Arrange
    open_tabs = {}
    
    file_paths = ["/path/to/file1.tex", "/path/to/file2.tex", "/path/to/file3.tex"]

    # Act
    for file_path in file_paths:
        tab_operations.create_new_tab(
            file_path=file_path,
            notebook_widget=mock_notebook,
            open_tabs_dict=open_tabs,
            apply_theme_callback=mock_callbacks["apply_theme"],
            on_tab_changed_callback=mock_callbacks["on_tab_changed"],
            EditorTab_class=MockEditorTab,
            schedule_heavy_updates_callback=mock_callbacks["schedule_heavy_updates"]
        )

    # Assert
    assert mock_notebook.add.call_count == 3
    assert mock_notebook.select.call_count == 3
    assert len(open_tabs) == 3
    assert mock_callbacks["apply_theme"].call_count == 3
    assert mock_notebook.after.call_count == 3
    
    # Check that all file paths are correctly stored
    stored_file_paths = [tab.file_path for tab in open_tabs.values()]
    for file_path in file_paths:
        assert file_path in stored_file_paths

def test_create_duplicate_tab(mock_notebook, mock_callbacks):
    """
    Tests that creating a tab for an already open file selects the existing tab.
    """
    # Arrange
    file_path = "/path/to/duplicate_file.tex"
    
    # Create first tab
    tab_operations.create_new_tab(
        file_path=file_path,
        notebook_widget=mock_notebook,
        open_tabs_dict={},
        apply_theme_callback=mock_callbacks["apply_theme"],
        on_tab_changed_callback=mock_callbacks["on_tab_changed"],
        EditorTab_class=MockEditorTab,
        schedule_heavy_updates_callback=mock_callbacks["schedule_heavy_updates"]
    )
    
    # Reset mocks to track calls for the second creation
    mock_notebook.add.reset_mock()
    mock_notebook.select.reset_mock()
    mock_callbacks["apply_theme"].reset_mock()
    mock_callbacks["on_tab_changed"].reset_mock()
    mock_notebook.after.reset_mock()

    # Create a new dictionary to simulate the existing tabs
    # In a real scenario, this would be the global tabs dictionary
    existing_tabs = {}
    # We need to simulate that the tab already exists
    existing_tab = MockEditorTab(mock_notebook, file_path, mock_callbacks["schedule_heavy_updates"])
    existing_tabs[str(existing_tab)] = existing_tab
    mock_notebook.tabs.return_value = [str(existing_tab)]

    # Act
    tab_operations.create_new_tab(
        file_path=file_path,
        notebook_widget=mock_notebook,
        open_tabs_dict=existing_tabs,
        apply_theme_callback=mock_callbacks["apply_theme"],
        on_tab_changed_callback=mock_callbacks["on_tab_changed"],
        EditorTab_class=MockEditorTab,
        schedule_heavy_updates_callback=mock_callbacks["schedule_heavy_updates"]
    )

    # Assert
    mock_notebook.add.assert_not_called() # No new tab should be added.
    mock_notebook.select.assert_called_once_with(str(existing_tab)) # The existing tab should be selected.
    mock_callbacks["apply_theme"].assert_not_called()
    mock_callbacks["on_tab_changed"].assert_not_called()
    mock_notebook.after.assert_not_called()
