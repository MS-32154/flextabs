from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import weakref

from .widgets import TooltipWidget


@dataclass
class TabConfig:
    """Configuration for a single tab."""

    id: str
    title: str
    content_class: type
    icon: str | None = None
    tooltip: str | None = None
    closable: bool = True
    keyboard_shortcut: str | None = None
    data: dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.id or not self.title:
            raise ValueError("Tab ID and title cannot be empty")
        if not issubclass(self.content_class, TabContent):
            raise ValueError("content_class must be a subclass of TabContent")


class TabContent(ABC):
    """Abstract base class for tab content."""

    def __init__(self, parent: Widget, tab_id: str, config: TabConfig, manager):
        self.parent = parent
        self.tab_id = tab_id
        self.config = config
        self.manager = weakref.ref(manager)
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=BOTH, expand=True)
        self._is_initialized = False

        try:
            self.setup_content()
            self._is_initialized = True
        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Failed to initialize tab content for '{tab_id}': {e}")

    @abstractmethod
    def setup_content(self):
        """Setup the content of the tab. Must be implemented by subclasses."""
        pass

    def on_tab_focus(self):
        """Called when tab gains focus. Override if needed."""
        pass

    def on_tab_blur(self):
        """Called when tab loses focus. Override if needed."""
        pass

    def on_tab_close(self) -> bool:
        """Called before tab closes. Return False to prevent closing."""
        return True

    def cleanup(self):
        """Clean up resources when tab is destroyed."""
        if hasattr(self, "frame") and self.frame:
            self.frame.destroy()

    def get_manager(self):
        """Get the tab manager instance."""
        return self.manager() if self.manager else None

    @property
    def is_initialized(self) -> bool:
        """Check if the tab content was successfully initialized."""


class TabOpener(ABC):
    """Abstract base class for different tab opening mechanisms."""

    def __init__(self, parent: Widget, config: dict[str, any]):
        self.parent = parent
        self.config = config
        self.tab_manager = None
        self._widgets = {}
        self._tooltips = {}

    @abstractmethod
    def setup_opener(self, tab_configs: list[TabConfig]):
        """Setup the opener UI with the given tab configurations."""
        pass

    def refresh_opener(self, tab_configs: list[TabConfig]):
        """Refresh opener with new configurations."""
        self.cleanup()
        self.setup_opener(tab_configs)

    def set_tab_manager(self, tab_manager):
        """Set reference to the tab manager."""
        self.tab_manager = tab_manager

    def cleanup(self):
        """Clean up opener widgets."""
        # Clean up tooltips
        for tooltip in self._tooltips.values():
            if hasattr(tooltip, "_hide_tooltip"):
                tooltip._hide_tooltip()
        self._tooltips.clear()

        # Clean up widgets
        for widget in self._widgets.values():
            if widget and hasattr(widget, "winfo_exists"):
                try:
                    if widget.winfo_exists():
                        widget.destroy()
                except:
                    pass
        self._widgets.clear()

    def update_tab_state(self, tab_id: str, is_open: bool):
        """Update visual state of tab opener based on tab open/close state."""
        pass

    def _add_tooltip(self, widget: Widget, text: str):
        """Add tooltip to widget."""
        if text:
            tooltip = TooltipWidget(widget, text)
            self._tooltips[str(widget)] = tooltip
            return tooltip
        return None

    def _style_unclosable_widget(self, widget: Widget):
        """Apply special styling to unclosable tab widgets."""
        try:
            if isinstance(widget, ttk.Button):
                style = ttk.Style()
                style.configure(
                    "Unclosable.TButton", foreground="gray", background="lightgray"
                )
                widget.configure(style="Unclosable.TButton")
        except:
            pass

    def _open_tab_safe(self, tab_id: str):
        """Safely open tab with error handling."""
        try:
            if self.tab_manager:
                self.tab_manager.open_tab(tab_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open tab: {e}")

    def _create_button(self, parent: Widget, tab_config: TabConfig) -> ttk.Button:
        """Create a button for a tab configuration."""
        btn_style = self.config.get("button_style", {})
        btn = ttk.Button(
            parent,
            text=tab_config.title,
            command=lambda: self._open_tab_safe(tab_config.id),
            **btn_style,
        )

        if not tab_config.closable:
            self._style_unclosable_widget(btn)

        if tab_config.tooltip:
            self._add_tooltip(btn, tab_config.tooltip)

        return btn
