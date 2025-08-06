# FlexTabs API Documentation

## Table of Contents

1. [Core Classes](#core-classes)
   - [TabManager](#tabmanager)
   - [TabConfig](#tabconfig)
   - [TabContent](#tabcontent)
   - [IconManager](#iconmanager)
2. [Enums](#enums)
3. [Opener Classes](#opener-classes)
4. [Widget Classes](#widget-classes)
5. [Utility Functions](#utility-functions)

---

## Core Classes

### TabManager

The main widget class that manages tabs and coordinates all components.

#### Constructor

```python
TabManager(
    parent: Widget,
    tab_configs: list[TabConfig],
    opener_type: str = "sidebar",
    opener_config: dict[str, any] = None,
    close_button_style: str = "right_click",
    notebook_config: dict[str, any] = None,
    close_confirmation: bool = False,
    close_confirmation_type: str | CloseConfirmationType = CloseConfirmationType.NONE,
    close_mode: str | CloseMode = CloseMode.ACTIVE_ONLY,
    enable_keyboard_shortcuts: bool = True,
    notebook_icon_size: tuple = (16, 16),
    show_notebook_icons: bool = True,
    notebook_fallback_icon_key: str = "default",
    use_notebook_fallback_icons: bool = True,
    **kwargs
)
```

**Parameters:**
- `parent`: Parent tkinter widget
- `tab_configs`: List of TabConfig objects defining available tabs
- `opener_type`: Type of tab opener ("toolbar", "sidebar", "menu")
- `opener_config`: Configuration dict for the opener
- `close_button_style`: How tabs can be closed ("right_click", "double_click", "both")
- `notebook_config`: Additional ttk.Notebook configuration
- `close_confirmation`: Whether to show confirmation before closing tabs
- `close_confirmation_type`: Type of confirmation dialog
- `close_mode`: Which tabs can be closed
- `enable_keyboard_shortcuts`: Enable built-in keyboard shortcuts
- `notebook_icon_size`: Size of icons in notebook tabs
- `show_notebook_icons`: Whether to show icons in notebook tabs
- `notebook_fallback_icon_key`: Key for fallback icon when no image available
- `use_notebook_fallback_icons`: Whether to use fallback icons
- `**kwargs`: Additional ttk.Frame options

#### Methods

##### Tab Operations

```python
def open_tab(self, tab_id: str) -> bool:
    """Open a tab. Returns True if successful."""

def close_tab(self, tab_id: str) -> bool:
    """Close a tab. Returns True if successfully closed."""

def select_tab(self, tab_id: str) -> bool:
    """Select a specific tab. Opens it if not already open."""

def close_all_tabs(self) -> int:
    """Close all open tabs. Returns number of tabs closed."""
```

##### Tab State Queries

```python
def is_tab_open(self, tab_id: str) -> bool:
    """Check if a tab is currently open."""

def get_open_tabs(self) -> list[str]:
    """Get list of currently open tab IDs."""

def get_current_tab(self) -> str | None:
    """Get the currently selected tab ID."""

def get_tab_content(self, tab_id: str) -> TabContent | None:
    """Get the content instance for a tab."""
```

##### Runtime Configuration

```python
def add_tab_config(self, config: TabConfig):
    """Add a new tab configuration at runtime."""

def remove_tab_config(self, tab_id: str) -> bool:
    """Remove a tab configuration. Closes the tab if open."""

def set_close_mode(self, mode: str | CloseMode):
    """Change the close mode at runtime."""

def get_close_mode(self) -> CloseMode:
    """Get the current close mode."""
```

##### Icon Management

```python
def refresh_tab_icons(self):
    """Refresh all tab icons (useful after changing icon files)."""

def set_notebook_icon_settings(
    self,
    show_icons: bool = None,
    icon_size: tuple = None,
    fallback_icon_key: str = None,
    use_fallback_icons: bool = None
):
    """Update notebook icon settings at runtime."""

def set_opener_icon_settings(self, **kwargs):
    """Update opener icon settings at runtime."""

def get_available_fallback_icons(self) -> dict:
    """Get all available fallback icons."""

def add_fallback_icon(self, key: str, icon: str):
    """Add a custom fallback icon."""
```

##### Utilities

```python
def show_notification(
    self, 
    message: str, 
    toast_type: str = "info", 
    duration: int = 2000
):
    """Show a toast notification."""

def add_close_button(self, parent: Widget, tab_id: str) -> ttk.Button:
    """Add a close button inside tab content."""

def cleanup(self):
    """Clean up all resources."""
```

#### Events

Set these attributes to receive callbacks:

```python
tab_manager.on_tab_opened = lambda tab_id: print(f"Opened {tab_id}")
tab_manager.on_tab_closed = lambda tab_id: print(f"Closed {tab_id}")
tab_manager.on_tab_switched = lambda new_id, old_id: print(f"Switched from {old_id} to {new_id}")
tab_manager.on_tab_error = lambda tab_id, error: print(f"Error in {tab_id}: {error}")
```

---

### TabConfig

Configuration class for defining tabs.

#### Constructor

```python
@dataclass
class TabConfig:
    id: str                                    # Required: Unique identifier
    title: str                                 # Required: Display title  
    content_class: type                        # Required: TabContent subclass
    icon: str | dict | None = None             # Optional: Icon specification
    tooltip: str | None = None                 # Optional: Tooltip text
    closable: bool = True                      # Optional: Whether tab can be closed
    keyboard_shortcut: str | None = None       # Optional: Keyboard shortcut
    data: dict[str, Any] = field(default_factory=dict)  # Optional: Custom data
```

#### Methods

```python
def get_icon(self, context: str = "default") -> str | None:
    """Get icon for specific context (opener, tab, default)."""
```

#### Icon Specification

Icons can be specified in multiple ways:

```python
# Simple string (emoji or file path)
icon="🏠"
icon="/path/to/icon.png"

# Context-specific dictionary
icon={
    "opener": "🏠",              # Icon for tab opener button
    "tab": "/path/to/home.png",  # Icon for notebook tab
    "default": "📄"              # Fallback
}
```

---

### TabContent

Abstract base class for all tab content implementations.

#### Constructor

```python
def __init__(self, parent: Widget, tab_id: str, config: TabConfig, manager):
    # Automatically called - don't override
```

#### Abstract Methods

```python
@abstractmethod
def setup_content(self):
    """Required: Set up your tab's UI here."""
    pass
```

#### Optional Override Methods

```python
def on_tab_focus(self):
    """Called when tab becomes active."""
    pass

def on_tab_blur(self):
    """Called when tab loses focus."""
    pass

def on_tab_close(self) -> bool:
    """Called before closing. Return False to prevent closing."""
    return True

def cleanup(self):
    """Clean up resources when tab is destroyed."""
    pass
```

#### Properties

```python
self.parent      # Parent widget (ttk.Frame)
self.tab_id      # Tab identifier string
self.config      # TabConfig object
self.frame       # Main frame for tab content (pack your widgets here)
```

#### Methods

```python
def get_manager(self):
    """Get reference to the TabManager instance."""
    return self.manager() if self.manager else None

@property
def is_initialized(self) -> bool:
    """Check if tab was successfully initialized."""
    return self._is_initialized
```

#### Example Implementation

```python
class MyTabContent(TabContent):
    def setup_content(self):
        # Create your UI
        ttk.Label(self.frame, text=f"Content for {self.config.title}").pack(pady=20)
        
        # Add some interactive elements
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Action").pack(side=tk.LEFT, padx=5)
        
        # Add close button if tab is closable
        if self.config.closable:
            manager = self.get_manager()
            if manager:
                close_btn = manager.add_close_button(button_frame, self.tab_id)
                close_btn.pack(side=tk.LEFT, padx=5)
    
    def on_tab_focus(self):
        print(f"Tab {self.tab_id} is now active")
        # Refresh data, update status, etc.
    
    def on_tab_close(self):
        # Check for unsaved changes
        if hasattr(self, 'has_unsaved_changes') and self.has_unsaved_changes():
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "Save changes before closing?",
                parent=self.frame
            )
            if result is None:  # Cancel
                return False
            elif result:  # Yes, save
                self.save_changes()
        return True
    
    def cleanup(self):
        # Clean up resources
        print(f"Cleaning up tab {self.tab_id}")
        super().cleanup()
```

---

### IconManager

Static class for managing icon loading and caching.

#### Class Methods

```python
@classmethod
def get_icon(cls, icon_path: str, size: tuple = None) -> Optional[ImageTk.PhotoImage]:
    """Load and cache an icon from file path."""

@classmethod
def get_fallback_text(cls, fallback_key: str = None) -> str:
    """Get fallback text icon for a given key."""

@classmethod
def clear_cache(cls):
    """Clear the icon cache."""

@classmethod
def preload_icons(cls, icon_paths: list[str], size: tuple = None):
    """Preload multiple icons for better performance."""

@classmethod
def add_fallback_icon(cls, key: str, icon: str):
    """Add a custom fallback icon."""

@classmethod
def get_fallback_icons(cls) -> dict:
    """Get all available fallback icons."""
```

#### Built-in Fallback Icons

The IconManager comes with built-in fallback icons:

```python
{
    "default": "📄", "home": "🏠", "settings": "⚙️", "help": "❓",
    "tools": "🔧", "data": "📊", "reports": "📈", "folder": "📁",
    "file": "📄", "image": "🖼️", "text": "📝", "code": "💻",
    "database": "🗄️", "network": "🌐", "security": "🔒",
    "error": "⚠️", "warning": "⚠️", "info": "ℹ️", "success": "✅"
}
```

---

## Enums

### TabPosition

Defines positions for tab openers:

```python
class TabPosition(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
```

### CloseMode

Defines how tabs can be closed:

```python
class CloseMode(Enum):
    ACTIVE_ONLY = "active_only"    # Only active tab can be closed
    ANY_VISIBLE = "any_visible"    # Any visible tab can be closed
    BOTH = "both"                  # Active closes normally, others need Ctrl+click
```

### CloseConfirmationType

Defines types of close confirmation dialogs:

```python
class CloseConfirmationType(Enum):
    NONE = "none"        # No confirmation
    YESNO = "yesno"      # Yes/No dialog
    WARNING = "warning"  # Warning dialog with OK/Cancel
    INFO = "info"        # Info dialog (always proceeds)
```

---

## Opener Classes

### TabOpener (Base Class)

Abstract base class for all tab openers.

#### Constructor

```python
def __init__(self, parent: Widget, config: dict[str, Any]):
    self.parent = parent
    self.config = config
    self.tab_manager = None
    # ... internal setup
```

#### Abstract Methods

```python
@abstractmethod
def setup_opener(self, tab_configs: list[TabConfig]):
    """Set up the opener UI."""
    pass
```

#### Methods

```python
def refresh_opener(self, tab_configs: list[TabConfig]):
    """Refresh the opener with updated tab configs."""

def set_tab_manager(self, tab_manager):
    """Set reference to the tab manager."""

def cleanup(self):
    """Clean up resources."""

def update_tab_state(self, tab_id: str, is_open: bool):
    """Update visual state when tab opens/closes."""
```

#### Configuration Options

Common configuration options for all openers:

```python
{
    "show_icons": True,           # Show icons
    "icon_size": (16, 16),       # Icon size tuple
    "icon_position": "left",     # "left", "right", "top", "bottom"
    "fallback_icon_key": "default",  # Fallback icon key
    "use_fallback_icons": True,  # Use fallback icons
    "style": {},                 # ttk.Frame styling
    "button_style": {}           # Button styling (for button-based openers)
}
```

### ToolbarOpener

Creates a toolbar with tab buttons.

#### Additional Configuration

```python
{
    "position": "top",          # "top", "bottom", "left", "right"
    "layout": "horizontal",     # "horizontal" or "vertical"
    # ... plus common opener options
}
```

### SidebarOpener

Creates a sidebar with tab buttons.

#### Additional Configuration

```python
{
    "position": "left",         # "left" or "right"
    "width": 150,              # Sidebar width in pixels
    "title": "Navigation",     # Optional title
    # ... plus common opener options
}
```

### MenuOpener

Creates menu items in the application menu bar.

#### Additional Configuration

```python
{
    "menu_title": "Tabs",      # Title in menu bar
    # Note: Only emoji/text icons supported for menus
    # ... plus common opener options
}
```

---

## Widget Classes

### TooltipWidget

Provides tooltip functionality for widgets.

#### Constructor

```python
TooltipWidget(
    widget: Widget,
    text: str,
    delay: int = 500,
    wraplength: int = 250,
    font: tuple = ("TkDefaultFont", 8, "normal")
)
```

#### Methods

```python
def update_text(self, new_text: str):
    """Update the tooltip text."""
```

### ToastNotification

Static class for showing toast notifications.

#### Static Methods

```python
@staticmethod
def show(
    parent: Widget,
    message: str,
    duration: int = 2000,
    toast_type: str = "info",
    position: str = "top-right",
    mode: str = "stacked"
):
    """Show a toast notification."""
```

**Parameters:**
- `parent`: Parent widget
- `message`: Notification message
- `duration`: Duration in milliseconds
- `toast_type`: "info", "warning", "error", "success"
- `position`: "top-right", "bottom-right", "top-left", "bottom-left"
- `mode`: "stacked" (multiple toasts visible) or "queued" (one at a time)

---

## Utility Functions

### Module-Level Convenience Functions

```python
def create_simple_tab_manager(parent, tab_configs, opener_type="sidebar", **kwargs):
    """Create a TabManager with sensible defaults for most use cases."""

def create_tab_config(id, title, content_class, **kwargs):
    """Create a TabConfig with convenient defaults."""

def get_version():
    """Get the current version of FlexTabs."""

def get_version_info():
    """Get detailed version information."""

def add_default_fallback_icons():
    """Add a set of useful default fallback icons to the IconManager."""
```

---

## Complete Example

Here's a comprehensive example showing most features:

```python
import tkinter as tk
from tkinter import ttk, messagebox
from flextabs import (
    TabManager, TabConfig, TabContent, 
    CloseMode, CloseConfirmationType
)

class HomeTab(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text="Welcome to FlexTabs!", 
                 font=("TkDefaultFont", 16)).pack(pady=20)
        
        ttk.Label(self.frame, 
                 text="This tab cannot be closed.",
                 foreground="gray").pack()

class SettingsTab(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text="Settings", 
                 font=("TkDefaultFont", 14, "bold")).pack(pady=10)
        
        # Settings form
        form_frame = ttk.Frame(self.frame)
        form_frame.pack(pady=20, padx=20, fill=tk.X)
        
        ttk.Label(form_frame, text="Theme:").grid(row=0, column=0, sticky=tk.W)
        theme_var = tk.StringVar(value="Light")
        ttk.Combobox(form_frame, textvariable=theme_var, 
                    values=["Light", "Dark"]).grid(row=0, column=1, padx=10)
        
        ttk.Label(form_frame, text="Language:").grid(row=1, column=0, sticky=tk.W, pady=5)
        lang_var = tk.StringVar(value="English")
        ttk.Combobox(form_frame, textvariable=lang_var,
                    values=["English", "Spanish", "French"]).grid(row=1, column=1, padx=10, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Save Settings").pack(side=tk.LEFT, padx=5)
        
        # Add close button
        manager = self.get_manager()
        if manager:
            close_btn = manager.add_close_button(btn_frame, self.tab_id)
            close_btn.pack(side=tk.LEFT, padx=5)

class DataTab(TabContent):
    def setup_content(self):
        self.modified = False
        
        ttk.Label(self.frame, text="Data Analysis", 
                 font=("TkDefaultFont", 14, "bold")).pack(pady=10)
        
        # Simulate data interface
        data_frame = ttk.LabelFrame(self.frame, text="Dataset", padding=10)
        data_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Tree for data display
        columns = ("ID", "Name", "Value")
        tree = ttk.Treeview(data_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Sample data
        sample_data = [
            ("1", "Item A", "100"),
            ("2", "Item B", "200"),
            ("3", "Item C", "300")
        ]
        
        for item in sample_data:
            tree.insert("", "end", values=item)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Modify button to simulate changes
        ttk.Button(data_frame, text="Modify Data", 
                  command=self.modify_data).pack(pady=5)
    
    def modify_data(self):
        self.modified = True
        manager = self.get_manager()
        if manager:
            manager.show_notification("Data modified", "info")
    
    def on_tab_close(self):
        if self.modified:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                parent=self.frame
            )
            if result is None:  # Cancel
                return False
            elif result:  # Yes, save
                self.save_data()
        return True
    
    def save_data(self):
        # Simulate saving
        self.modified = False
        manager = self.get_manager()
        if manager:
            manager.show_notification("Data saved successfully", "success")

def main():
    root = tk.Tk()
    root.title("FlexTabs Complete Example")
    root.geometry("900x700")
    
    # Define tab configurations
    tab_configs = [
        TabConfig(
            id="home",
            title="Home",
            content_class=HomeTab,
            icon="🏠",
            tooltip="Go to home page",
            closable=False  # Cannot be closed
        ),
        TabConfig(
            id="settings",
            title="Settings",
            content_class=SettingsTab,
            icon="⚙️",
            tooltip="Application settings",
            keyboard_shortcut="<Control-comma>"
        ),
        TabConfig(
            id="data",
            title="Data Analysis", 
            content_class=DataTab,
            icon="📊",
            tooltip="Analyze your data",
            keyboard_shortcut="<Control-d>"
        )
    ]
    
    # Event handlers
    def on_tab_opened(tab_id):
        print(f"Tab opened: {tab_id}")
    
    def on_tab_closed(tab_id):
        print(f"Tab closed: {tab_id}")
    
    def on_tab_switched(new_tab_id, old_tab_id):
        print(f"Switched from {old_tab_id} to {new_tab_id}")
    
    # Create tab manager
    tab_manager = TabManager(
        parent=root,
        tab_configs=tab_configs,
        opener_type="sidebar",
        opener_config={
            "position": "left",
            "width": 180,
            "title": "Navigation",
            "show_icons": True,
            "icon_position": "left"
        },
        close_button_style="right_click",
        close_confirmation=True,
        close_confirmation_type=CloseConfirmationType.YESNO,
        close_mode=CloseMode.ACTIVE_ONLY,
        enable_keyboard_shortcuts=True,
        show_notebook_icons=True,
        notebook_icon_size=(16, 16)
    )
    
    # Set event callbacks
    tab_manager.on_tab_opened = on_tab_opened
    tab_manager.on_tab_closed = on_tab_closed
    tab_manager.on_tab_switched = on_tab_switched
    
    tab_manager.pack(fill=tk.BOTH, expand=True)
    
    # Open home tab by default
    tab_manager.open_tab("home")
    
    # Menu bar for additional actions
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Open Settings", 
                         command=lambda: tab_manager.open_tab("settings"))
    file_menu.add_command(label="Open Data Analysis", 
                         command=lambda: tab_manager.open_tab("data"))
    file_menu.add_separator()
    file_menu.add_command(label="Close All Tabs", 
                         command=tab_manager.close_all_tabs)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    
    # Status bar
    status_bar = ttk.Label(root, text="Ready | Use Ctrl+, for Settings, Ctrl+D for Data", 
                          relief=tk.SUNKEN, anchor=tk.W)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    root.mainloop()

if __name__ == "__main__":
    main()
```

This example demonstrates:
- Multiple tab types with different content
- Icon usage and tooltips
- Keyboard shortcuts
- Event handling
- Close confirmation
- Runtime notifications
- Integration with menu system
- Unsaved changes handling

---

## Advanced Topics

### Custom Tab Openers

You can create custom tab openers by inheriting from `TabOpener`:

```python
class CustomOpener(TabOpener):
    def setup_opener(self, tab_configs):
        # Create your custom opener UI
        pass
    
    def update_tab_state(self, tab_id, is_open):
        # Update your custom UI when tabs open/close
        pass
```

### Performance Optimization

- Icons are automatically cached for performance
- Tabs use lazy loading (created only when first opened)
- Smart refresh avoids unnecessary widget recreation
- Proper cleanup prevents memory leaks

### Error Handling

FlexTabs includes comprehensive error handling:
- Tab initialization errors are caught and reported
- Tab content errors are isolated to individual tabs
- User-friendly error notifications
- Optional error callbacks for custom handling

### Threading Considerations

FlexTabs is designed for single-threaded tkinter applications. If you need to update tabs from background threads, use tkinter's thread-safe methods like `after()` or queue-based communication.

---

This completes the comprehensive API documentation for FlexTabs. The library provides a robust foundation for building tabbed interfaces in tkinter applications with extensive customization options and professional features.