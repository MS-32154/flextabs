"""
FlexTabs - A powerful and flexible tab management library for tkinter

FlexTabs extends tkinter's ttk.Notebook with advanced features including:
- Dynamic tab opening/closing with state retention
- Multiple opener styles (Toolbar, Sidebar, Menu)
- Icon support with caching
- Keyboard shortcuts
- Event system with callbacks
- Toast notifications
- Runtime configuration

Basic Usage:
    from flextabs import TabManager, TabConfig, TabContent

    class MyTabContent(TabContent):
        def setup_content(self):
            ttk.Label(self.frame, text="My content").pack()

    tab_configs = [
        TabConfig("home", "Home", MyTabContent, icon="🏠", closable=False)
    ]

    tab_manager = TabManager(
        parent=root,
        tab_configs=tab_configs,
        opener_type="sidebar"
    )
"""

__version__ = "0.2.0"
__author__ = "MS-32154"
__email__ = "msttoffg@gmail.com"
__license__ = "MIT"

# Core components
from .enums import CloseConfirmationType, CloseMode, TabPosition
from .icons import IconManager

# Openers
from .openers import MenuOpener, SidebarOpener, ToolbarOpener
from .tab_base import TabConfig, TabContent, TabOpener
from .tab_manager import TabManager

# Widgets
from .widgets import ToastNotification, TooltipWidget

# Version info
VERSION = __version__
VERSION_INFO = tuple(
    int(part) if part.isdigit() else part for part in __version__.split(".")
)

# Public API
__all__ = [
    "VERSION",
    "VERSION_INFO",
    "CloseConfirmationType",
    "CloseMode",
    "IconManager",
    "MenuOpener",
    "SidebarOpener",
    "TabConfig",
    "TabContent",
    "TabManager",
    "TabOpener",
    "TabPosition",
    "ToastNotification",
    "ToolbarOpener",
    "TooltipWidget",
]


def get_version():
    """Get the current version of FlexTabs."""
    return __version__


def get_version_info():
    """Get detailed version information."""
    return {
        "version": __version__,
        "version_tuple": VERSION_INFO,
        "author": __author__,
        "license": __license__,
    }


# Convenience functions for common use cases
def create_simple_tab_manager(parent, tab_configs, opener_type="sidebar", **kwargs):
    """
    Create a TabManager with sensible defaults for most use cases.

    Args:
        parent: Parent widget
        tab_configs: List of TabConfig objects
        opener_type: "sidebar", "toolbar", or "menu"
        **kwargs: Additional TabManager options

    Returns:
        Configured TabManager instance
    """
    default_opener_configs = {
        "sidebar": {"position": "left", "width": 150, "title": "Navigation"},
        "toolbar": {"position": "top", "layout": "horizontal"},
        "menu": {"menu_title": "Tabs"},
    }

    opener_config = kwargs.pop("opener_config", {})
    opener_config = {**default_opener_configs.get(opener_type, {}), **opener_config}

    return TabManager(
        parent=parent,
        tab_configs=tab_configs,
        opener_type=opener_type,
        opener_config=opener_config,
        close_button_style="right_click",
        enable_keyboard_shortcuts=True,
        show_notebook_icons=True,
        **kwargs,
    )


def create_tab_config(id, title, content_class, **kwargs):
    """
    Create a TabConfig with convenient defaults.

    Args:
        id: Unique tab identifier
        title: Display title
        content_class: TabContent subclass
        **kwargs: Additional TabConfig options (icon, tooltip, closable, etc.)

    Returns:
        TabConfig instance
    """
    return TabConfig(id=id, title=title, content_class=content_class, **kwargs)


# Snapshot of IconManager's built-in fallback icons
_default_icon_fallbacks = IconManager.get_fallback_icons()


def add_default_fallback_icons():
    """(Re)apply the built-in fallback icons to the IconManager."""
    for key, icon in _default_icon_fallbacks.items():
        IconManager.add_fallback_icon(key, icon)


# Compatibility aliases for different naming conventions
TabPane = TabContent  # Alternative name
TabSheet = TabContent  # Alternative name
