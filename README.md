[![PyPI version](https://img.shields.io/pypi/v/flextabs.svg)](https://pypi.org/project/flextabs/)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/github/license/MS-32154/flextabs.svg)](LICENSE)

# FlexTabs

A powerful and flexible tab management library for Python tkinter applications that extends `ttk.Notebook` with advanced features like dynamic tab opening/closing, multiple opener styles, keyboard shortcuts, icon support, and state retention.

## Table of Contents

- [Features](#features)
  - [Core Features](#core-features)
  - [Advanced Features](#advanced-features)
- [Installation](#installation)
- [Running the Demo](#running-the-demo)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
  - [TabConfig](#tabconfig)
  - [TabContent](#tabcontent)
  - [TabManager](#tabmanager)
- [Opener Types](#opener-types)
  - [Sidebar Opener](#sidebar-opener)
  - [Toolbar Opener](#toolbar-opener)
  - [Menu Opener](#menu-opener)
- [Close Modes](#close-modes)
- [Keyboard Shortcuts](#keyboard-shortcuts)
  - [Built-in Shortcuts](#built-in-shortcuts)
  - [Custom Shortcuts](#custom-shortcuts)
- [Event Callbacks](#event-callbacks)
- [Runtime Management](#runtime-management)
  - [Tab Operations](#tab-operations)
  - [Dynamic Configuration](#dynamic-configuration)
  - [Icon Management](#icon-management)
- [Notifications](#notifications)
- [Advanced Examples](#advanced-examples)
    - [Custom Tab with Complex UI](#custom-tab-with-complex-uI)
    - [Multi-Window Application](#multi-window-application)
    - [Notebook Styling](#notebook-styling)
- [Error Handling](#error-handling)
- [Performance Tips](#performance-tips)
- [Best Practices](#best-practices)
- [Requirements](#requirements)
- [Examples](#examples)
    - [Complete Application Example](#complete-application-example)
    - [Dynamic Tab Management](#dynamic-tab-management)
- [Styling and Customization](#styling-and-customization)
    - [Custom Tooltip Styling](#custom-tooltip-styling)
    - [TTK Styling and Compatibility](#ttk-styling-and-compatibility)
    - [Migrating from ttk.Notebook](#migrating-from-ttk.Notebook)
- [License](#license)
- [Contributing](#contributing)
- [Support](#support)
- [Roadmap](#roadmap)

## Features

### Core Features

- **Dynamic Tab Management**: Open and close tabs programmatically with state retention
- **Multiple Opener Styles**: Toolbar, Sidebar, and Menu-based tab openers
- **Flexible Close Modes**: Control how and when tabs can be closed
- **Icon Support**: Full icon support for both tab openers and notebook tabs (images + emoji/text fallbacks)
- **Keyboard Shortcuts**: Built-in navigation shortcuts plus custom tab shortcuts
- **State Management**: Automatic tab state tracking and restoration
- **Event System**: Comprehensive callbacks for tab lifecycle events
- **Toast Notifications**: Built-in notification system for user feedback
- **Runtime Configuration**: Change settings and add/remove tabs at runtime

### Advanced Features

- **Smart Refresh**: Efficient UI updates that preserve layout and state
- **Multiple Close Confirmation Types**: None, Yes/No, Warning, or Info dialogs
- **Unclosable Tabs**: Mark tabs as permanent with visual indicators
- **Icon Caching**: Automatic icon loading and caching for performance
- **Tooltip Support**: Rich tooltips for tab openers
- **Error Handling**: Robust error handling with user-friendly notifications

## Installation

```bash
pip install flextabs
```

Or clone the repository:

```bash
git clone https://github.com/MS-32154/flextabs.git
cd flextabs
pip install -e .
```

**Dependencies:**

- Python 3.8+
- tkinter (usually included with Python)
- Pillow (PIL) for image icon support

## Running the Demo

```
python3 -m flextabs
```

## Quick Start

```python
import tkinter as tk
from tkinter import ttk
from flextabs import TabManager, TabConfig, TabContent

# Create your tab content classes
class HomeTabContent(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text="Welcome to the Home tab!").pack(pady=20)

class SettingsTabContent(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text="Settings Configuration").pack(pady=20)
        # Add a close button
        self.manager().add_close_button(self.frame, self.tab_id).pack(pady=10)

# Create the main window
root = tk.Tk()
root.title("FlexTabs Demo")
root.geometry("800x600")

# Define tab configurations
tab_configs = [
    TabConfig(
        id="home",
        title="Home",
        content_class=HomeTabContent,
        icon="🏠",  # Emoji icon
        tooltip="Go to home page",
        closable=False  # This tab cannot be closed
    ),
    TabConfig(
        id="settings",
        title="Settings",
        content_class=SettingsTabContent,
        icon="⚙️",
        tooltip="Application settings",
        keyboard_shortcut="<Control-s>"
    )
]

# Create the tab manager
tab_manager = TabManager(
    parent=root,
    tab_configs=tab_configs,
    opener_type="sidebar",  # or "toolbar", "menu"
    opener_config={
        "position": "left",
        "width": 150,
        "title": "Navigation"
    }
)
tab_manager.pack(fill=tk.BOTH, expand=True)

# Open the home tab by default
tab_manager.open_tab("home")

root.mainloop()
```

## Core Components

### TabConfig

Defines the configuration for each tab:

```python
TabConfig(
    id="unique_id",              # Required: Unique identifier
    title="Tab Title",           # Required: Display title
    content_class=YourContent,   # Required: TabContent subclass
    icon="🏠",                   # Optional: Icon (emoji, text, or file path)
    tooltip="Helpful text",      # Optional: Tooltip text
    closable=True,               # Optional: Whether tab can be closed
    keyboard_shortcut="<Control-t>",  # Optional: Keyboard shortcut
    data={"key": "value"}        # Optional: Custom data dictionary
)
```

#### Icon Support

FlexTabs supports multiple icon types:

```python
# Emoji/text icons (≤4 characters)
icon="🏠"
icon="⚙️"
icon="📊"

# File paths to images (PNG, JPEG, etc.)
icon="/path/to/icon.png"
icon="resources/settings.ico"

# Context-specific icons
icon={
    "opener": "🏠",              # Icon for tab opener
    "tab": "/path/to/home.png",  # Icon for notebook tab
    "default": "📄"              # Fallback
}
```

### TabContent

Base class for all tab content. Inherit from this to create your tabs:

```python
class MyTabContent(TabContent):
    def setup_content(self):
        """Required: Set up your tab's UI here"""
        ttk.Label(self.frame, text="My content").pack()

    def on_tab_focus(self):
        """Optional: Called when tab becomes active"""
        print(f"Tab {self.tab_id} focused")

    def on_tab_blur(self):
        """Optional: Called when tab loses focus"""
        print(f"Tab {self.tab_id} blurred")

    def on_tab_close(self) -> bool:
        """Optional: Called before closing. Return False to prevent."""
        return True  # Allow closing

    def cleanup(self):
        """Optional: Clean up resources"""
        super().cleanup()
```

### TabManager

The main component that orchestrates everything:

```python
TabManager(
    parent=root,                    # Parent widget
    tab_configs=[...],              # List of TabConfig objects
    opener_type="sidebar",          # "toolbar", "sidebar", or "menu"
    opener_config={},               # Opener-specific configuration
    close_button_style="right_click",  # "right_click", "double_click", "both"
    close_confirmation=False,       # Enable close confirmations
    close_confirmation_type="none", # "none", "yesno", "warning", "info"
    close_mode="active_only",       # "active_only", "any_visible", "both"
    enable_keyboard_shortcuts=True, # Enable built-in shortcuts
    show_notebook_icons=True,       # Show icons in notebook tabs
    notebook_icon_size=(16, 16),    # Icon size for notebook tabs
    **kwargs                        # Additional ttk.Frame options
)
```

## Opener Types

### Sidebar Opener

Creates a sidebar with navigation buttons:

```python
opener_config = {
    "position": "left",      # "left" or "right"
    "width": 150,           # Sidebar width
    "title": "Navigation",  # Optional title
    "style": {},           # ttk.Frame styling
    "button_style": {},    # Button styling
    "show_icons": True,    # Show icons on buttons
    "icon_size": (16, 16), # Icon size
    "icon_position": "left" # "left", "right", "top", "bottom"
}
```

### Toolbar Opener

Creates a horizontal or vertical toolbar:

```python
opener_config = {
    "position": "top",        # "top", "bottom", "left", "right"
    "layout": "horizontal",   # "horizontal" or "vertical"
    "style": {},             # ttk.Frame styling
    "button_style": {},      # Button styling
    "show_icons": True,      # Show icons on buttons
    "icon_size": (16, 16),   # Icon size
    "icon_position": "left"  # Icon position relative to text
}
```

### Menu Opener

Creates a menu in the application's menu bar:

```python
opener_config = {
    "menu_title": "Tabs",    # Menu title in menu bar
    "show_icons": True,      # Show icons in menu items
    # Note: Icons are limited to emoji/text for menus
}
```

## Close Modes

Control how tabs can be closed:

- **`active_only`**: Only the currently active tab can be closed
- **`any_visible`**: Any visible tab can be closed by clicking
- **`both`**: Active tab closes normally, others require Ctrl+click

## Keyboard Shortcuts

### Built-in Shortcuts

- `Ctrl+W`: Close current tab
- `Ctrl+Tab`: Next tab
- `Ctrl+Shift+Tab`: Previous tab
- `Ctrl+1` through `Ctrl+9`: Select tab by index

### Custom Shortcuts

Add shortcuts to individual tabs:

```python
TabConfig(
    id="settings",
    title="Settings",
    content_class=SettingsContent,
    keyboard_shortcut="<Control-comma>"  # Ctrl+,
)
```

## Event Callbacks

Set up callbacks to respond to tab events:

```python
def on_tab_opened(tab_id):
    print(f"Tab {tab_id} opened")

def on_tab_closed(tab_id):
    print(f"Tab {tab_id} closed")

def on_tab_switched(new_tab_id, old_tab_id):
    print(f"Switched from {old_tab_id} to {new_tab_id}")

def on_tab_error(tab_id, error):
    print(f"Error in tab {tab_id}: {error}")

tab_manager.on_tab_opened = on_tab_opened
tab_manager.on_tab_closed = on_tab_closed
tab_manager.on_tab_switched = on_tab_switched
tab_manager.on_tab_error = on_tab_error
```

## Runtime Management

### Tab Operations

```python
# Open/close tabs
tab_manager.open_tab("settings")
tab_manager.close_tab("settings")

# Check tab status
is_open = tab_manager.is_tab_open("settings")
current_tab = tab_manager.get_current_tab()
open_tabs = tab_manager.get_open_tabs()

# Select tabs
tab_manager.select_tab("home")

# Close all tabs
closed_count = tab_manager.close_all_tabs()

# Get tab content instance
content = tab_manager.get_tab_content("settings")
```

### Dynamic Configuration

```python
# Add new tab at runtime
new_tab = TabConfig(
    id="reports",
    title="Reports",
    content_class=ReportsContent
)
tab_manager.add_tab_config(new_tab)

# Remove tab
tab_manager.remove_tab_config("reports")

# Change close mode
tab_manager.set_close_mode("any_visible")
```

### Icon Management

```python
# Refresh all icons (useful after changing icon files)
tab_manager.refresh_tab_icons()

# Update icon settings
tab_manager.set_notebook_icon_settings(
    show_icons=True,
    icon_size=(20, 20),
    fallback_icon_key="default"
)

tab_manager.set_opener_icon_settings(
    show_icons=True,
    icon_size=(18, 18),
    icon_position="top"
)

# Add custom fallback icons
tab_manager.add_fallback_icon("custom", "🔧")
available_icons = tab_manager.get_available_fallback_icons()
```

## Notifications

Show toast notifications to users:

```python
# Basic notification
tab_manager.show_notification("Tab opened successfully")

# Styled notifications
tab_manager.show_notification(
    "Settings saved!",
    toast_type="success",  # "info", "warning", "error", "success"
    duration=3000  # milliseconds
)
```

## Advanced Examples

### Custom Tab with Complex UI

```python
class DataAnalysisTab(TabContent):
    def setup_content(self):
        # Create a complex interface
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="Load Data").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Export").pack(side=tk.LEFT, padx=(0, 5))

        # Content area with notebook
        content_nb = ttk.Notebook(main_frame)
        content_nb.pack(fill=tk.BOTH, expand=True)

        # Data tab
        data_frame = ttk.Frame(content_nb)
        content_nb.add(data_frame, text="Raw Data")

        # Charts tab
        chart_frame = ttk.Frame(content_nb)
        content_nb.add(chart_frame, text="Charts")

    def on_tab_focus(self):
        # Refresh data when tab becomes active
        self.refresh_data()

    def on_tab_close(self):
        # Ask user to save unsaved changes
        if self.has_unsaved_changes():
            from tkinter import messagebox
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "Save changes before closing?",
                parent=self.frame
            )
            if result is None:  # Cancel
                return False
            elif result:  # Yes
                self.save_changes()
        return True

    def refresh_data(self):
        # Implementation here
        pass

    def has_unsaved_changes(self):
        # Check for unsaved changes
        return False

    def save_changes(self):
        # Save changes
        pass
```

### Multi-Window Application

```python
class MultiWindowApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Window App")

        # Create main tab manager
        self.main_tabs = TabManager(
            parent=self.root,
            tab_configs=self.get_main_tab_configs(),
            opener_type="toolbar",
            opener_config={"position": "top"}
        )
        self.main_tabs.pack(fill=tk.BOTH, expand=True)

        # Set up callbacks
        self.main_tabs.on_tab_opened = self.on_main_tab_opened

    def get_main_tab_configs(self):
        return [
            TabConfig("home", "Home", HomeTab, icon="🏠", closable=False),
            TabConfig("projects", "Projects", ProjectsTab, icon="📁"),
            TabConfig("settings", "Settings", SettingsTab, icon="⚙️")
        ]

    def on_main_tab_opened(self, tab_id):
        if tab_id == "projects":
            # When projects tab opens, populate with recent projects
            content = self.main_tabs.get_tab_content(tab_id)
            if content:
                content.load_recent_projects()

    def run(self):
        self.main_tabs.open_tab("home")
        self.root.mainloop()
```

### Notebook Styling

FlexTabs uses `ttk.Notebook` internally, so all standard ttk styling applies:

```python
import tkinter.ttk as ttk

# Create custom notebook style
style = ttk.Style()
style.configure("Custom.TNotebook",
               background="lightgray",
               tabmargins=[0, 5, 0, 0])
style.configure("Custom.TNotebook.Tab",
               padding=[20, 10],
               background="white")

tab_manager = TabManager(
    parent,
    tab_configs=tabs,
    notebook_config={
        "style": "Custom.TNotebook",  # Apply custom ttk style
        "padding": 5
    }
)
```

You can also access the underlying `ttk.Notebook` directly:

```python
# Access the internal ttk.Notebook for advanced customization
internal_notebook = tab_manager.notebook
internal_notebook.configure(width=500, height=300)
```

## Error Handling

FlexTabs includes comprehensive error handling:

```python
# Errors are automatically caught and can be handled via callback
def handle_tab_error(tab_id, error):
    print(f"Error in tab {tab_id}: {error}")
    # Log to file, show user message, etc.

tab_manager.on_tab_error = handle_tab_error
```

## Performance Tips

1. **Icon Preloading**: Icons are automatically preloaded and cached
2. **Smart Refresh**: UI updates use smart refresh to avoid recreating widgets unnecessarily
3. **Lazy Loading**: Tabs are only created when first opened
4. **Memory Management**: Proper cleanup prevents memory leaks

## Best Practices

1. **Tab IDs**: Use descriptive, unique IDs for all tabs
2. **Resource Cleanup**: Always implement `cleanup()` in TabContent subclasses that use resources
3. **Error Handling**: Implement robust error handling in your TabContent classes
4. **Icon Sizes**: Use consistent icon sizes for better visual appearance
5. **Keyboard Shortcuts**: Use standard shortcuts when possible (Ctrl+S for settings, etc.)

## Examples

### Complete Application Example

```python
import tkinter as tk
from tkinter import ttk, messagebox
from flextabs import TabManager, TabConfig, TabContent

class HomeTab(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text="Welcome to the Home Tab!",
                 font=("TkDefaultFont", 16)).pack(pady=20)

        ttk.Button(self.frame, text="Open Settings",
                  command=lambda: self.get_manager().open_tab("settings")).pack(pady=5)

class SettingsTab(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text="Settings",
                 font=("TkDefaultFont", 14, "bold")).pack(pady=10)

        # Some settings widgets
        ttk.Checkbutton(self.frame, text="Enable notifications").pack(pady=2)
        ttk.Checkbutton(self.frame, text="Auto-save").pack(pady=2)

        # Add close button
        close_btn = self.get_manager().add_close_button(self.frame, self.tab_id)
        close_btn.pack(pady=10)

class DataTab(TabContent):
    def setup_content(self):
        self.data_modified = False

        ttk.Label(self.frame, text="Data Editor").pack(pady=10)

        self.text_area = tk.Text(self.frame, height=10, width=50)
        self.text_area.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        self.text_area.bind('<KeyPress>', self.on_data_change)

    def on_data_change(self, event):
        self.data_modified = True

    def on_tab_close(self) -> bool:
        if self.data_modified:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                parent=self.frame
            )
            if result is None:  # Cancel
                return False
            elif result:  # Yes - save
                # Simulate saving
                self.get_manager().show_notification("Data saved!", "success")
        return True

def main():
    root = tk.Tk()
    root.title("FlexTabs Demo Application")
    root.geometry("900x600")

    # Define tabs
    tabs = [
        TabConfig("home", "Home", HomeTab,
                 tooltip="Application home page",
                 keyboard_shortcut="<Control-h>"),
        TabConfig("settings", "Settings", SettingsTab,
                 tooltip="Application settings",
                 closable=False),  # Can't be closed
        TabConfig("data", "Data Editor", DataTab,
                 tooltip="Edit your data here",
                 keyboard_shortcut="<Control-d>"),
    ]

    # Create tab manager with sidebar
    tab_manager = TabManager(
        root,
        tab_configs=tabs,
        opener_type="sidebar",
        opener_config={
            "position": "left",
            "width": 180,
            "title": "Navigation",
            "style": {"bg": "#f8f9fa"}
        },
        close_confirmation=True,
        close_confirmation_type="yesno",
        enable_keyboard_shortcuts=True
    )

    # Set up event handlers
    def on_tab_opened(tab_id):
        tab_manager.show_notification(f"Opened {tabs[0].title}", "info")

    tab_manager.on_tab_opened = on_tab_opened
    tab_manager.pack(fill=tk.BOTH, expand=True)

    # Open home tab by default
    tab_manager.open_tab("home")

    root.mainloop()

if __name__ == "__main__":
    main()
```

### Dynamic Tab Management

```python
import tkinter as tk
from flextabs import TabManager, TabConfig, TabContent

class DynamicContent(TabContent):
    def setup_content(self):
        data = self.config.data
        tk.Label(self.frame, text=f"Dynamic tab: {data.get('content', 'No content')}").pack()

def create_dynamic_tab(tab_manager, counter):
    """Create a new tab dynamically"""
    tab_id = f"dynamic_{counter}"
    config = TabConfig(
        id=tab_id,
        title=f"Dynamic {counter}",
        content_class=DynamicContent,
        data={"content": f"This is dynamic tab #{counter}"}
    )

    tab_manager.add_tab_config(config)
    tab_manager.open_tab(tab_id)

# Usage in your application
root = tk.Tk()
tab_manager = TabManager(root, tab_configs=[], opener_type="toolbar")

# Add button to create new tabs
counter = 1
def add_tab():
    global counter
    create_dynamic_tab(tab_manager, counter)
    counter += 1

tk.Button(root, text="Add Tab", command=add_tab).pack()
tab_manager.pack(fill=tk.BOTH, expand=True)
```

## Styling and Customization

### Custom Tooltip Styling

The library includes built-in tooltips that can be customized by modifying the `TooltipWidget` class or by styling the underlying tkinter widgets.

### Toast Notifications

Built-in toast notification system with four types:

- `info` (blue) - General information
- `warning` (yellow) - Warnings
- `error` (red) - Error messages
- `success` (green) - Success messages

### TTK Styling and Compatibility

FlexTabs preserves full compatibility with `ttk.Notebook` styling and behavior:

```python
import tkinter.ttk as ttk

# All standard ttk.Notebook features work
style = ttk.Style()
style.configure("Custom.TNotebook", background="lightgray")
style.configure("Custom.TNotebook.Tab", padding=[20, 10])

# FlexTabs respects ttk themes
style.theme_use('clam')  # or 'alt', 'default', 'classic'

tab_manager = TabManager(
    parent,
    tab_configs=tabs,
    notebook_config={"style": "Custom.TNotebook"}
)

# Access underlying ttk.Notebook for direct manipulation
notebook = tab_manager.notebook
print(f"Current tab: {notebook.select()}")
print(f"All tabs: {notebook.tabs()}")
```

### Migrating from ttk.Notebook

If you have existing `ttk.Notebook` code, migration is straightforward:

**Before (ttk.Notebook):**

```python
notebook = ttk.Notebook(parent)
frame = ttk.Frame(notebook)
notebook.add(frame, text="My Tab")
# Content goes directly in frame
```

**After (FlexTabs):**

```python
class MyTab(TabContent):
    def setup_content(self):
        # Content goes in self.frame
        pass

config = TabConfig("my_tab", "My Tab", MyTab)
tab_manager = TabManager(parent, [config], opener_type="toolbar")
```

## Requirements

- Python 3.8+
- tkinter (usually included with Python)
- Pillow (PIL) for image icon support

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

If you encounter any issues or have questions, please:

1. Check the [examples](#examples) section
2. Search existing [GitHub Issues](https://github.com/MS-32154/flextabs/issues)
3. Create a new issue with:
   - Python version
   - Operating system
   - Minimal code example reproducing the issue
   - Full error traceback (if applicable)

## Roadmap

- [x] Icon support for tabs and buttons
- [ ] Drag and drop tab reordering
- [ ] Tab groups and separators
- [ ] Persistent tab state between sessions
- [ ] Theme system
- [ ] Animation effects
- [ ] Tab overflow handling

---

**FlexTabs** – Extending `ttk.Notebook` for powerful and flexible tab management in Tkinter.

© 2025 MS-32154. All rights reserved.
