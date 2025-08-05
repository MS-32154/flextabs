"""
FlexTabs - A flexible and extensible tab manager widget for tkinter applications.

Provides multiple tab opening mechanisms (toolbar, sidebar, menu) with customizable
behavior and styling options.
"""

from .tab_manager import TabManager
from .tab_base import TabConfig, TabContent, TabOpener
from .enums import TabPosition, CloseMode, CloseConfirmationType
from .openers import ToolbarOpener, SidebarOpener, MenuOpener
from .widgets import TooltipWidget, ToastNotification

__version__ = "0.1.0"
__author__ = "MS-32154"
__email__ = "msttoffg@gmail.com"

__all__ = [
    "TabManager",
    "TabConfig",
    "TabContent",
    "TabOpener",
    "TabPosition",
    "CloseMode",
    "CloseConfirmationType",
    "ToolbarOpener",
    "SidebarOpener",
    "MenuOpener",
    "TooltipWidget",
    "ToastNotification",
]
