from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import weakref
import os
from PIL import Image, ImageTk
from typing import Optional, Dict, Any

from .widgets import TooltipWidget


@dataclass
class TabConfig:
    """Configuration for a single tab."""

    id: str
    title: str
    content_class: type
    icon: str | dict | None = None
    tooltip: str | None = None
    closable: bool = True
    keyboard_shortcut: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id or not self.title:
            raise ValueError("Tab ID and title cannot be empty")
        if not issubclass(self.content_class, TabContent):
            raise ValueError("content_class must be a subclass of TabContent")

    def get_icon(self, context: str = "default") -> str | None:
        if not self.icon:
            return None

        if isinstance(self.icon, str):
            return self.icon
        elif isinstance(self.icon, dict):
            return self.icon.get(context, self.icon.get("default"))

        return None


class IconManager:
    _cache: Dict[str, ImageTk.PhotoImage] = {}
    _default_size = (16, 16)
    _fallback_icons = {
        "default": "📄",
        "home": "🏠",
        "settings": "⚙️",
        "help": "❓",
        "tools": "🔧",
        "data": "📊",
        "reports": "📈",
        "folder": "📁",
        "file": "📄",
        "image": "🖼️",
        "text": "📝",
        "code": "💻",
        "database": "🗄️",
        "network": "🌐",
        "security": "🔒",
        "error": "⚠️",
        "warning": "⚠️",
        "info": "ℹ️",
        "success": "✅",
    }

    @classmethod
    def get_icon(
        cls, icon_path: str, size: tuple = None
    ) -> Optional[ImageTk.PhotoImage]:
        if not icon_path or len(icon_path) <= 4:
            return None

        size = size or cls._default_size
        cache_key = f"{icon_path}_{size[0]}x{size[1]}"

        if cache_key in cls._cache:
            return cls._cache[cache_key]

        try:
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
                image = image.resize(size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                cls._cache[cache_key] = photo
                return photo
        except Exception:
            pass

        return None

    @classmethod
    def get_fallback_text(cls, fallback_key: str = None) -> str:
        if fallback_key and fallback_key in cls._fallback_icons:
            return cls._fallback_icons[fallback_key]
        return cls._fallback_icons["default"]

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()

    @classmethod
    def preload_icons(cls, icon_paths: list[str], size: tuple = None):
        for icon_path in icon_paths:
            if icon_path:
                cls.get_icon(icon_path, size)

    @classmethod
    def add_fallback_icon(cls, key: str, icon: str):
        cls._fallback_icons[key] = icon

    @classmethod
    def get_fallback_icons(cls) -> dict:
        return cls._fallback_icons.copy()


class TabContent(ABC):
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
        pass

    def on_tab_focus(self):
        pass

    def on_tab_blur(self):
        pass

    def on_tab_close(self) -> bool:
        return True

    def cleanup(self):
        if hasattr(self, "frame") and self.frame:
            self.frame.destroy()

    def get_manager(self):
        return self.manager() if self.manager else None

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized


class TabOpener(ABC):
    def __init__(self, parent: Widget, config: dict[str, Any]):
        self.parent = parent
        self.config = config
        self.tab_manager = None
        self._widgets = {}
        self._tooltips = {}
        self._icons = {}

        self.icon_size = config.get("icon_size", (16, 16))
        self.show_icons = config.get("show_icons", True)
        self.icon_position = config.get("icon_position", "left")
        self.fallback_icon_key = config.get("fallback_icon_key", "default")
        self.use_fallback_icons = config.get("use_fallback_icons", True)

    @abstractmethod
    def setup_opener(self, tab_configs: list[TabConfig]):
        pass

    def refresh_opener(self, tab_configs: list[TabConfig]):
        if hasattr(self, "_smart_refresh") and self._smart_refresh(tab_configs):
            return
        self.cleanup()
        self.setup_opener(tab_configs)

    def _smart_refresh(self, tab_configs: list[TabConfig]) -> bool:
        return False

    def set_tab_manager(self, tab_manager):
        self.tab_manager = tab_manager

    def cleanup(self):
        for tooltip in self._tooltips.values():
            if hasattr(tooltip, "_hide_tooltip"):
                tooltip._hide_tooltip()
        self._tooltips.clear()

        for widget in self._widgets.values():
            if widget and hasattr(widget, "winfo_exists"):
                try:
                    if widget.winfo_exists():
                        widget.destroy()
                except:
                    pass
        self._widgets.clear()
        self._icons.clear()

    def update_tab_state(self, tab_id: str, is_open: bool):
        pass

    def _load_icon(self, tab_config: TabConfig) -> Optional[ImageTk.PhotoImage]:
        if not self.show_icons:
            return None

        icon_path = tab_config.get_icon("opener")
        if not icon_path:
            return None

        if tab_config.id not in self._icons:
            self._icons[tab_config.id] = IconManager.get_icon(icon_path, self.icon_size)

        return self._icons[tab_config.id]

    def _get_button_text(self, tab_config: TabConfig) -> str:
        text = tab_config.title
        icon_path = tab_config.get_icon("opener")

        icon_text = None
        if self.show_icons and icon_path and len(icon_path) <= 4:
            icon_text = icon_path
        elif (
            self.show_icons
            and self.use_fallback_icons
            and tab_config.id not in self._icons
        ):
            icon_text = IconManager.get_fallback_text(self.fallback_icon_key)

        if icon_text:
            if self.icon_position == "left":
                text = f"{icon_text} {text}"
            elif self.icon_position == "right":
                text = f"{text} {icon_text}"
            elif self.icon_position == "top":
                text = f"{icon_text}\n{text}"
            elif self.icon_position == "bottom":
                text = f"{text}\n{icon_text}"

        return text

    def _add_tooltip(self, widget: Widget, text: str):
        if text:
            tooltip = TooltipWidget(widget, text)
            self._tooltips[id(widget)] = tooltip
            return tooltip
        return None

    def _style_unclosable_widget(self, widget: Widget):
        try:
            if isinstance(widget, ttk.Button):
                if not hasattr(self.__class__, "_unclosable_style_created"):
                    style = ttk.Style()
                    style.configure(
                        "Unclosable.TButton", foreground="gray", background="lightgray"
                    )
                    self.__class__._unclosable_style_created = True
                widget.configure(style="Unclosable.TButton")
        except:
            pass

    def _open_tab_safe(self, tab_id: str):
        try:
            if self.tab_manager:
                self.tab_manager.open_tab(tab_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open tab: {e}")

    def _create_button(self, parent: Widget, tab_config: TabConfig) -> ttk.Button:
        btn_style = self.config.get("button_style", {})

        icon = self._load_icon(tab_config)
        text = self._get_button_text(tab_config)

        btn_kwargs = {
            "text": text,
            "command": lambda: self._open_tab_safe(tab_config.id),
            **btn_style,
        }

        if icon:
            btn_kwargs["image"] = icon
            btn_kwargs["compound"] = self._get_compound_mode()

        btn = ttk.Button(parent, **btn_kwargs)

        if icon:
            btn.image = icon

        if not tab_config.closable:
            self._style_unclosable_widget(btn)

        if tab_config.tooltip:
            self._add_tooltip(btn, tab_config.tooltip)

        return btn

    def _get_compound_mode(self) -> str:
        position_map = {
            "left": "left",
            "right": "right",
            "top": "top",
            "bottom": "bottom",
        }
        return position_map.get(self.icon_position, "left")
