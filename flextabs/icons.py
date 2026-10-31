"""Icon classification, loading and caching."""

import os
import tkinter as tk
from functools import cache
from typing import ClassVar

from PIL import Image, ImageTk


@cache
def _image_extensions() -> frozenset[str]:
    """File extensions Pillow can open, lower-cased (e.g. ``.png``)."""
    return frozenset(ext.lower() for ext in Image.registered_extensions())


class IconManager:
    """Shared icon utilities: text-vs-image detection, image cache, fallbacks."""

    # (icon_path, size, id(tk interpreter)) -> (PhotoImage, tk interpreter)
    _cache: ClassVar[
        dict[tuple[str, tuple[int, int], int], tuple[ImageTk.PhotoImage, object]]
    ] = {}
    _default_size: ClassVar[tuple[int, int]] = (16, 16)
    _fallback_icons: ClassVar[dict[str, str]] = {
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
        "user": "👤",
        "admin": "👑",
        "error": "⚠️",
        "warning": "⚠️",
        "info": "ℹ️",
        "success": "✅",
    }

    # --- classification ------------------------------------------------------

    @staticmethod
    def is_image_path(icon: str | None) -> bool:
        """Return True if ``icon`` refers to an image file rather than text/emoji.

        Decided from the string alone (never the filesystem): a value is an
        image path if it contains a path separator or ends in an image file
        extension Pillow can open. Everything else, including multi-codepoint
        emoji and text such as ``"v2.0"``, is a text icon.
        """
        if not icon or not isinstance(icon, str):
            return False
        if "/" in icon or os.sep in icon:
            return True
        return os.path.splitext(icon)[1].lower() in _image_extensions()

    @classmethod
    def is_text_icon(cls, icon: str | None) -> bool:
        """Return True if ``icon`` should be rendered as text (e.g. an emoji)."""
        return bool(icon) and isinstance(icon, str) and not cls.is_image_path(icon)

    # --- image cache ---------------------------------------------------------

    @staticmethod
    def _entry_alive(photo: ImageTk.PhotoImage, interp) -> bool:
        """Return True if the image's Tk application and the image still exist.

        Destroying a Tk root does not delete its Tcl interpreter, so the image
        itself stays valid; the application is checked separately.
        """
        try:
            if interp is not None:
                interp.call("winfo", "exists", ".")
            photo.width()
            return True
        except tk.TclError, RuntimeError:
            return False

    @classmethod
    def _prune_dead(cls):
        """Drop cached images whose Tk application or image no longer exists.

        Each PhotoImage references its interpreter, so stale entries would
        otherwise keep destroyed Tk roots alive indefinitely.
        """
        dead = [
            key for key, entry in cls._cache.items() if not cls._entry_alive(*entry)
        ]
        for key in dead:
            del cls._cache[key]

    @classmethod
    def get_icon(
        cls, icon_path: str, size: tuple | None = None, master: tk.Misc | None = None
    ) -> ImageTk.PhotoImage | None:
        """Load (and cache) an image icon for the Tk interpreter of ``master``.

        PhotoImages belong to a single Tk interpreter, so the cache is keyed by
        interpreter; stale entries are pruned whenever a new image is loaded.
        """
        if not cls.is_image_path(icon_path):
            return None

        size = tuple(size or cls._default_size)
        interp = master.tk if master is not None else None
        cache_key = (icon_path, size, id(interp))

        entry = cls._cache.get(cache_key)
        if entry is not None and entry[1] is interp and cls._entry_alive(*entry):
            return entry[0]

        cls._prune_dead()

        try:
            with Image.open(icon_path) as image:
                image = image.resize(size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image, master=master)
        except OSError, ValueError, tk.TclError:
            # Missing/unreadable file or unsupported image
            return None

        cls._cache[cache_key] = (photo, interp)
        return photo

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()

    @classmethod
    def preload_icons(
        cls,
        icon_paths: list[str],
        size: tuple | None = None,
        master: tk.Misc | None = None,
    ):
        for icon_path in icon_paths:
            if icon_path:
                cls.get_icon(icon_path, size, master)

    # --- fallback text icons -------------------------------------------------

    @classmethod
    def get_fallback_text(cls, fallback_key: str | None = None) -> str:
        if fallback_key and fallback_key in cls._fallback_icons:
            return cls._fallback_icons[fallback_key]
        return cls._fallback_icons["default"]

    @classmethod
    def add_fallback_icon(cls, key: str, icon: str):
        cls._fallback_icons[key] = icon

    @classmethod
    def get_fallback_icons(cls) -> dict:
        return cls._fallback_icons.copy()
