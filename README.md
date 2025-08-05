# FlexTabs

A flexible and extensible tab manager widget for tkinter applications built on top of `ttk.Notebook`. While `ttk.Notebook` provides the basic tab interface, FlexTabs extends it with multiple tab opening mechanisms (toolbar, sidebar, menu), advanced tab management features, and customizable behavior options.

## Why FlexTabs?

While tkinter's `ttk.Notebook` is great for basic tabbed interfaces, it has limitations:
- Only supports tabs displayed at the top of the widget
- No built-in way to dynamically open/close tabs from external UI elements
- Limited customization for tab opening mechanisms
- No built-in support for unclosable tabs, confirmations, or notifications

FlexTabs solves these problems by wrapping `ttk.Notebook` with a comprehensive management layer that provides modern tab interface patterns commonly seen in IDEs, browsers, and professional applications. It handles tab state retention after open and close actions. New opened tabs are appended to the end, and opener buttons can manage both opening and switching between opened tabs.

## Architecture

FlexTabs is built as a wrapper around tkinter's `ttk.Notebook` widget:

```
┌─────────────────────────────────────────┐
│              TabManager                 │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ TabOpener   │  │  ttk.Notebook   │   │
│  │ (Sidebar/   │  │                 │   │
│  │ Toolbar/    │  │ ┌─────────────┐ │   │
│  │ Menu)       │  │ │ TabContent  │ │   │
│  │             │  │ │   Frame     │ │   │
│  │ [Home]      │  │ └─────────────┘ │   │
│  │ [Settings]  │  │ ┌─────────────┐ │   │
│  │ [Help]      │  │ │ TabContent  │ │   │
│  │             │  │ │   Frame     │ │   │
│  └─────────────┘  │ └─────────────┘ │   │
│                   └─────────────────┘   │
└─────────────────────────────────────────┘
```

- **TabManager**: Main widget that coordinates everything
- **TabOpener**: External UI elements (sidebar, toolbar, menu) for opening tabs
- **ttk.Notebook**: The actual tab container (unchanged tkinter behavior)
- **TabContent**: Your custom content classes that populate each tab

## Features

- **Built on ttk.Notebook**: Full compatibility with existing tkinter tab functionality
- **Multiple Tab Openers**: Toolbar, Sidebar, and Menu-based tab opening
- **Flexible Tab Management**: Open, close, and switch between tabs programmatically
- **Customizable Styling**: Configure appearance of tabs, buttons, and notifications
- **Keyboard Shortcuts**: Built-in shortcuts for tab navigation and custom tab shortcuts
- **Close Confirmation**: Optional confirmation dialogs before closing tabs
- **Toast Notifications**: Built-in notification system for user feedback
- **Tooltips**: Hover tooltips for tab buttons
- **Event Callbacks**: Hook into tab lifecycle events
- **Runtime Configuration**: Add/remove tabs dynamically
- **Unclosable Tabs**: Mark tabs as permanent with special styling

## Installation

```bash
pip install flextabs
```

Or clone the repository:
```bash
git clone https://github.com/your-username/flextabs.git
cd flextabs
pip install -e .
```

## Running Tests

```
pytest
```

## Running the Demo

```
python3 -m flextabs
```

## Quick Start

Here's how you would create tabs with vanilla tkinter vs. FlexTabs:

### Traditional ttk.Notebook approach:
```python
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
notebook = ttk.Notebook(root)

# Manually create and add tabs
frame1 = ttk.Frame(notebook)
notebook.add(frame1, text="Tab 1")
tk.Label(frame1, text="Content 1").pack()

frame2 = ttk.Frame(notebook)
notebook.add(frame2, text="Tab 2")
tk.Label(frame2, text="Content 2").pack()

notebook.pack(fill=tk.BOTH, expand=True)
root.mainloop()
```

### FlexTabs approach:
```python
import tkinter as tk
from flextabs import TabManager, TabConfig, TabContent

class MyTabContent(TabContent):
    def setup_content(self):
        tk.Label(self.frame, text=f"Content for {self.config.title}").pack()

# Create main window
root = tk.Tk()
root.title("FlexTabs Demo")
root.geometry("800x600")

# Define tabs with rich configuration
tab_configs = [
    TabConfig("tab1", "Home", MyTabContent, tooltip="Home page"),
    TabConfig("tab2", "Settings", MyTabContent, closable=False),
    TabConfig("tab3", "Help", MyTabContent, keyboard_shortcut="<Control-h>"),
]

# Create tab manager with sidebar opener
tab_manager = TabManager(
    root,
    tab_configs=tab_configs,
    opener_type="sidebar",  # External UI for opening tabs
    opener_config={"position": "left", "width": 200, "title": "Navigation"}
)
tab_manager.pack(fill=tk.BOTH, expand=True)

root.mainloop()
```

The key difference: FlexTabs separates tab **definition** from tab **opening mechanism**, allowing you to create professional interfaces where tabs can be opened from sidebars, toolbars, menus, or programmatically.

## Tab Opener Types

### 1. Sidebar Opener
Perfect for navigation-style interfaces with vertical button layout.

```python
tab_manager = TabManager(
    parent,
    tab_configs=tabs,
    opener_type="sidebar",
    opener_config={
        "position": "left",  # or "right"
        "width": 200,
        "title": "Navigation",
        "style": {"bg": "#f0f0f0"}
    }
)
```

### 2. Toolbar Opener
Great for ribbon-style interfaces with horizontal or vertical button layouts.

```python
tab_manager = TabManager(
    parent,
    tab_configs=tabs,
    opener_type="toolbar",
    opener_config={
        "position": "top",  # "top", "bottom", "left", "right"
        "layout": "horizontal",  # or "vertical"
        "style": {"bg": "#e0e0e0"},
        "button_style": {"width": 15}
    }
)
```

### 3. Menu Opener
Integrates tabs into the application's menu bar.

```python
tab_manager = TabManager(
    parent,
    tab_configs=tabs,
    opener_type="menu",
    opener_config={
        "menu_title": "Windows"  # Menu name in menu bar
    }
)
```

## Tab Configuration

### TabConfig Parameters

```python
from flextabs import TabConfig

tab_config = TabConfig(
    id="unique_id",              # Unique identifier
    title="Tab Title",           # Display name
    content_class=MyTabContent,  # TabContent subclass
    icon="path/to/icon.png",     # Optional icon (not yet implemented)
    tooltip="Helpful tooltip",   # Hover tooltip text
    closable=True,              # Whether tab can be closed
    keyboard_shortcut="<Control-t>",  # Keyboard shortcut
    data={"key": "value"}       # Custom data dictionary
)
```

### Creating Tab Content

Extend the `TabContent` class to create your tab content:

```python
from flextabs import TabContent
import tkinter as tk
from tkinter import ttk

class MyTabContent(TabContent):
    def setup_content(self):
        """Required: Setup your tab's UI here"""
        # Access tab configuration
        title = self.config.title
        custom_data = self.config.data
        
        # Create UI elements
        ttk.Label(self.frame, text=f"Welcome to {title}").pack(pady=10)
        
        # Access the tab manager if needed
        manager = self.get_manager()
        close_btn = manager.add_close_button(self.frame, self.tab_id)
        close_btn.pack(pady=5)
    
    def on_tab_focus(self):
        """Optional: Called when tab gains focus"""
        print(f"Tab {self.tab_id} focused")
    
    def on_tab_blur(self):
        """Optional: Called when tab loses focus"""
        print(f"Tab {self.tab_id} blurred")
    
    def on_tab_close(self) -> bool:
        """Optional: Called before tab closes. Return False to prevent closing"""
        # Ask user for confirmation, save data, etc.
        return True  # Allow closing
    
    def cleanup(self):
        """Optional: Clean up resources when tab is destroyed"""
        super().cleanup()  # Always call parent cleanup
```

## Advanced Configuration

### Close Behavior

```python
from flextabs import TabManager, CloseMode, CloseConfirmationType

tab_manager = TabManager(
    parent,
    tab_configs=tabs,
    
    # Close button behavior
    close_button_style="right_click",  # "right_click", "double_click", "both"
    
    # Close mode - which tabs can be closed with click
    close_mode=CloseMode.ACTIVE_ONLY,  # ACTIVE_ONLY, ANY_VISIBLE, BOTH
    
    # Close confirmation
    close_confirmation=True,
    close_confirmation_type=CloseConfirmationType.YESNO,  # NONE, YESNO, WARNING, INFO
    
    # Keyboard shortcuts
    enable_keyboard_shortcuts=True
)
```

### Event Callbacks

```python
def on_tab_opened(tab_id: str):
    print(f"Tab {tab_id} opened")

def on_tab_closed(tab_id: str):
    print(f"Tab {tab_id} closed")

def on_tab_switched(new_tab_id: str, old_tab_id: str):
    print(f"Switched from {old_tab_id} to {new_tab_id}")

def on_tab_error(tab_id: str, error: Exception):
    print(f"Error in tab {tab_id}: {error}")

tab_manager.on_tab_opened = on_tab_opened
tab_manager.on_tab_closed = on_tab_closed
tab_manager.on_tab_switched = on_tab_switched
tab_manager.on_tab_error = on_tab_error
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

## API Reference

### TabManager Methods

#### Tab Management
- `open_tab(tab_id: str) -> bool` - Open a specific tab
- `close_tab(tab_id: str) -> bool` - Close a specific tab
- `select_tab(tab_id: str) -> bool` - Select/focus a specific tab
- `close_all_tabs() -> int` - Close all open tabs

#### Tab Information
- `is_tab_open(tab_id: str) -> bool` - Check if tab is open
- `get_open_tabs() -> list[str]` - Get list of open tab IDs
- `get_current_tab() -> str | None` - Get currently selected tab ID
- `get_tab_content(tab_id: str) -> TabContent | None` - Get tab content instance

#### Runtime Configuration
- `add_tab_config(config: TabConfig)` - Add new tab configuration
- `remove_tab_config(tab_id: str) -> bool` - Remove tab configuration
- `set_close_mode(mode: CloseMode)` - Change close mode
- `get_close_mode() -> CloseMode` - Get current close mode

#### UI Helpers
- `add_close_button(parent: Widget, tab_id: str) -> ttk.Button` - Add close button to tab content
- `show_notification(message: str, toast_type: str = "info", duration: int = 2000)` - Show toast notification

#### Cleanup
- `cleanup()` - Clean up all resources
- `destroy()` - Destroy the widget

### Built-in Keyboard Shortcuts

- `Ctrl+W` - Close current tab
- `Ctrl+Tab` - Next tab
- `Ctrl+Shift+Tab` - Previous tab
- `Ctrl+1-9` - Select tab by index
- Custom shortcuts defined in `TabConfig.keyboard_shortcut`

### Enums

#### TabPosition
- `TOP`, `BOTTOM`, `LEFT`, `RIGHT` - Opener positions

#### CloseMode
- `ACTIVE_ONLY` - Only close currently active tab on click
- `ANY_VISIBLE` - Close any visible tab on click
- `BOTH` - Close active tab normally, any tab with Ctrl+click

#### CloseConfirmationType
- `NONE` - No confirmation
- `YESNO` - Yes/No dialog
- `WARNING` - Warning dialog with OK/Cancel
- `INFO` - Info dialog with OK

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

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### Version 0.1.0
- Initial release
- Support for Toolbar, Sidebar, and Menu openers
- Tab lifecycle management
- Keyboard shortcuts
- Close confirmation dialogs
- Toast notifications
- Tooltip support
- Runtime tab configuration

## Support

If you encounter any issues or have questions, please:

1. Check the [examples](#examples) section
2. Search existing [GitHub Issues](https://github.com/your-username/flextabs/issues)
3. Create a new issue with:
   - Python version
   - Operating system
   - Minimal code example reproducing the issue
   - Full error traceback (if applicable)

## Roadmap

- [ ] Icon support for tabs and buttons
- [ ] Drag and drop tab reordering
- [ ] Tab groups and separators
- [ ] Custom tab close buttons
- [ ] Persistent tab state
- [ ] Theme system
- [ ] Animation effects
- [ ] Tab overflow handling

---

**FlexTabs** – Making Tkinter tab management flexible and powerful! 🚀

© 2025 MS-32154. All rights reserved.
Licensed under the [MIT License](https://opensource.org/licenses/MIT).
