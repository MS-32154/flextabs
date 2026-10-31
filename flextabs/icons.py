"""Icons: built-in vector icon set, image-file loading, caching and fallbacks.

An icon *spec* (``TabConfig.icon``) is resolved in this order:

1. a built-in icon name, e.g. ``"home"`` -> crisp SVG icon tinted to the theme
2. an image file path, e.g. ``"icons/home.png"`` -> loaded with Pillow
3. anything else (e.g. an emoji or short text) -> rendered as text

Built-in icons are original 24x24 outline drawings rendered with Tk's native
SVG support (Tk 9+). Where SVG is unavailable they are simply omitted.
"""

import os
import tkinter as tk
from functools import cache
from typing import ClassVar

from PIL import Image, ImageTk

# Inner SVG markup on a 24x24 grid. Strokes inherit the root stroke colour;
# small filled dots use ``currentColor`` which is substituted at render time.
_DOT = '<circle cx="{x}" cy="{y}" r="1.05" fill="currentColor" stroke="none"/>'

_SVG_ICONS: dict[str, str] = {
    "home": '<path d="M3.5 11 12 4l8.5 7"/><path d="M6 9.5V20h12V9.5"/>'
    '<path d="M10 20v-5.5h4V20"/>',
    "settings": '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/>'
    '<circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
    "file": '<path d="M6.5 3.5h7l4 4v13h-11z"/><path d="M13.5 3.5v4h4"/>',
    "file-text": '<path d="M6.5 3.5h7l4 4v13h-11z"/><path d="M13.5 3.5v4h4"/>'
    '<path d="M9.5 12.5h5M9.5 16h5"/>',
    "folder": '<path d="M3.5 7A1.5 1.5 0 0 1 5 5.5h4l2 2.5h8A1.5 1.5 0 0 1 20.5 9.5'
    'v8.5a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 18z"/>',
    "help": '<circle cx="12" cy="12" r="8.5"/>'
    '<path d="M9.6 9.6a2.5 2.5 0 1 1 3.4 2.3c-.6.3-1 .8-1 1.5v.4"/>'
    + _DOT.format(x=12, y=16.9),
    "info": '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5"/>'
    + _DOT.format(x=12, y=7.9),
    "check-circle": '<circle cx="12" cy="12" r="8.5"/>'
    '<path d="m8.5 12.3 2.4 2.4 4.6-5"/>',
    "alert": '<path d="M10.4 4.6 3.3 17a1.8 1.8 0 0 0 1.6 2.7h14.2a1.8 1.8 0 0 0 '
    '1.6-2.7L13.6 4.6a1.8 1.8 0 0 0-3.2 0z"/><path d="M12 9.5v4"/>'
    + _DOT.format(x=12, y=16.6),
    "x-circle": '<circle cx="12" cy="12" r="8.5"/>'
    '<path d="m9.3 9.3 5.4 5.4M14.7 9.3l-5.4 5.4"/>',
    "close": '<path d="m6.5 6.5 11 11M17.5 6.5l-11 11"/>',
    "plus": '<path d="M12 5.5v13M5.5 12h13"/>',
    "chart": '<path d="M4 20h16"/><path d="M7.5 16.5V11M12 16.5V6.5M16.5 16.5V9"/>',
    "trending": '<path d="M4 20h16"/><path d="m4.5 15.5 4.5-4.5 3.5 3.5 6.5-6.5"/>'
    '<path d="M14.5 8h4.5v4.5"/>',
    "code": '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M13.5 5.5l-3 13"/>',
    "terminal": '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/>'
    '<path d="m7.5 9.5 3 2.5-3 2.5M12.5 15h4"/>',
    "database": '<ellipse cx="12" cy="6.5" rx="7" ry="2.75"/>'
    '<path d="M5 6.5v11c0 1.5 3.1 2.75 7 2.75s7-1.25 7-2.75v-11"/>'
    '<path d="M5 12c0 1.5 3.1 2.75 7 2.75S19 13.5 19 12"/>',
    "globe": '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17"/>'
    '<path d="M12 3.5c2.3 2.4 3.5 5.2 3.5 8.5s-1.2 6.1-3.5 8.5c-2.3-2.4-3.5-5.2-3.5-8.5'
    'S9.7 5.9 12 3.5z"/>',
    "lock": '<rect x="5" y="10.5" width="14" height="10" rx="2"/>'
    '<path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/>',
    "user": '<circle cx="12" cy="8.5" r="3.75"/><path d="M5 20a7 7 0 0 1 14 0"/>',
    "shield": '<path d="M12 3.5 5.5 6v5.5c0 4 2.7 7.4 6.5 9 3.8-1.6 6.5-5 6.5-9V6z"/>',
    "image": '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/>'
    '<circle cx="9" cy="10" r="1.6"/><path d="m20.5 15.5-4.5-4.5-9.5 8.5"/>',
    "grid": '<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/>'
    '<rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/>'
    '<rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/>'
    '<rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>',
    "layers": '<path d="m12 3.5 8.5 4.5-8.5 4.5-8.5-4.5z"/>'
    '<path d="m3.5 12.5 8.5 4.5 8.5-4.5"/>',
    "calendar": '<rect x="4" y="5.5" width="16" height="15" rx="2"/>'
    '<path d="M4 10h16M8.5 3.5v4M15.5 3.5v4"/>',
    "bell": '<path d="M6.5 16v-4.5a5.5 5.5 0 0 1 11 0V16l1.5 2h-14z"/>'
    '<path d="M10 20.5a2 2 0 0 0 4 0"/>',
    "refresh": '<path d="M19.5 11A7.5 7.5 0 0 0 6.2 7.2L4.5 9"/>'
    '<path d="M4.5 4.5V9H9"/>'
    '<path d="M4.5 13a7.5 7.5 0 0 0 13.3 3.8l1.7-1.8"/><path d="M19.5 19.5V15H15"/>',
    "trash": '<path d="M4.5 7h15M10 11v6M14 11v6"/>'
    '<path d="m6.5 7 .8 12.5a1.5 1.5 0 0 0 1.5 1.5h6.4a1.5 1.5 0 0 0 '
    '1.5-1.5L17.5 7"/>'
    '<path d="M9.5 7V4.5h5V7"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5 5"/>',
    "sun": '<circle cx="12" cy="12" r="3.75"/>'
    '<path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4'
    'M5.6 18.4 7 17M17 7l1.4-1.4"/>',
    "moon": '<path d="M19.5 14.5A7.5 7.5 0 1 1 9.5 4.5a6 6 0 0 0 10 10z"/>',
}

_SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
    'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{width}" '
    'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
)


@cache
def _image_extensions() -> frozenset[str]:
    """File extensions Pillow can open, lower-cased (e.g. ``.png``)."""
    return frozenset(ext.lower() for ext in Image.registered_extensions())


def _size_px(size: int | tuple[int, int] | None, default: int = 16) -> int:
    """Icon height in pixels from an int or (width, height) tuple."""
    if size is None:
        return default
    if isinstance(size, int):
        return size
    return int(size[1])


Photo = ImageTk.PhotoImage | tk.PhotoImage


class IconManager:
    """Shared icon utilities: built-in icons, image files, caching, fallbacks."""

    # key -> (image, tk interpreter); key always ends with id(interpreter)
    _cache: ClassVar[dict[tuple, tuple[Photo, object]]] = {}
    _default_size: ClassVar[tuple[int, int]] = (16, 16)
    _stroke_width: ClassVar[float] = 1.8
    _svg_icons: ClassVar[dict[str, str]] = dict(_SVG_ICONS)
    # Fallback keys map to icon specs (normally built-in icon names)
    _fallback_icons: ClassVar[dict[str, str]] = {
        "default": "file",
        "home": "home",
        "settings": "settings",
        "help": "help",
        "tools": "grid",
        "data": "chart",
        "reports": "trending",
        "folder": "folder",
        "file": "file",
        "image": "image",
        "text": "file-text",
        "code": "code",
        "database": "database",
        "network": "globe",
        "security": "lock",
        "user": "user",
        "admin": "shield",
        "error": "x-circle",
        "warning": "alert",
        "info": "info",
        "success": "check-circle",
    }

    # --- classification ------------------------------------------------------

    @classmethod
    def is_builtin(cls, icon: str | None) -> bool:
        """Return True if ``icon`` names a built-in icon."""
        return isinstance(icon, str) and icon in cls._svg_icons

    @classmethod
    def builtin_names(cls) -> list[str]:
        """Names of all built-in (and registered) icons."""
        return sorted(cls._svg_icons)

    @staticmethod
    def is_image_path(icon: str | None) -> bool:
        """Return True if ``icon`` refers to an image file rather than text/emoji.

        Decided from the string alone (never the filesystem): a value is an
        image path if it contains a path separator or ends in an image file
        extension Pillow can open. Everything else, including multi-codepoint
        emoji and text such as ``"v2.0"``, is not a path.
        """
        if not icon or not isinstance(icon, str):
            return False
        if "/" in icon or os.sep in icon:
            return True
        return os.path.splitext(icon)[1].lower() in _image_extensions()

    @classmethod
    def is_text_icon(cls, icon: str | None) -> bool:
        """Return True if ``icon`` is rendered as text (not a built-in or file)."""
        return (
            bool(icon)
            and isinstance(icon, str)
            and not cls.is_builtin(icon)
            and not cls.is_image_path(icon)
        )

    # --- cache helpers -------------------------------------------------------

    @staticmethod
    def _entry_alive(photo: Photo, interp) -> bool:
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

        Each image references its interpreter, so stale entries would otherwise
        keep destroyed Tk roots alive indefinitely.
        """
        dead = [
            key for key, entry in cls._cache.items() if not cls._entry_alive(*entry)
        ]
        for key in dead:
            del cls._cache[key]

    @classmethod
    def _cached(cls, key: tuple, interp, factory) -> Photo | None:
        entry = cls._cache.get(key)
        if entry is not None and entry[1] is interp and cls._entry_alive(*entry):
            return entry[0]
        # Pruning scans the whole cache, so only do it when an interpreter we
        # have not seen appears (that is when destroyed roots can linger).
        if not any(e[1] is interp for e in cls._cache.values()):
            cls._prune_dead()
        photo = factory()
        if photo is not None:
            cls._cache[key] = (photo, interp)
        return photo

    # --- image files ---------------------------------------------------------

    @classmethod
    def get_icon(
        cls, icon_path: str, size: tuple | None = None, master: tk.Misc | None = None
    ) -> ImageTk.PhotoImage | None:
        """Load (and cache) an image file icon for the interpreter of ``master``."""
        if not cls.is_image_path(icon_path):
            return None

        if isinstance(size, int):
            size = (size, size)
        size = tuple(size or cls._default_size)
        interp = master.tk if master is not None else None

        def load():
            try:
                with Image.open(icon_path) as image:
                    image = image.resize(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image, master=master)
            except OSError, ValueError, tk.TclError:
                return None  # missing/unreadable file or unsupported image

        return cls._cached(("file", icon_path, size, id(interp)), interp, load)

    # --- built-in icons ------------------------------------------------------

    @classmethod
    def register_icon(cls, name: str, svg_body: str):
        """Add a custom built-in icon from inner SVG markup on a 24x24 grid.

        Use ``currentColor`` for fills; strokes inherit the icon colour.
        """
        cls._svg_icons[name] = svg_body

    @classmethod
    def svg_for(cls, name: str, color: str, stroke_width: float | None = None) -> str:
        """Full SVG document for a built-in icon in ``color``."""
        body = cls._svg_icons[name].replace("currentColor", color)
        width = stroke_width if stroke_width is not None else cls._stroke_width
        return _SVG_TEMPLATE.format(color=color, width=width, body=body)

    @classmethod
    def get_builtin_icon(
        cls,
        name: str,
        size: int | tuple[int, int] | None = None,
        color: str = "#52525b",
        master: tk.Misc | None = None,
    ) -> tk.PhotoImage | None:
        """Render a built-in icon at ``size`` pixels in ``color``.

        Returns None for unknown names or if this Tk build cannot render SVG.
        """
        if not cls.is_builtin(name):
            return None
        px = _size_px(size, cls._default_size[1])
        interp = master.tk if master is not None else None

        def render():
            try:
                return tk.PhotoImage(
                    master=master,
                    data=cls.svg_for(name, color),
                    format=f"svg -scaletoheight {px}",
                )
            except tk.TclError:
                return None  # Tk without SVG support

        return cls._cached(("svg", name, px, color, id(interp)), interp, render)

    @classmethod
    def render(
        cls,
        spec: str | None,
        size: int | tuple[int, int] | None = None,
        color: str = "#52525b",
        master: tk.Misc | None = None,
    ) -> Photo | None:
        """Image for an icon spec (built-in name or file path), else None."""
        if cls.is_builtin(spec):
            return cls.get_builtin_icon(spec, size, color, master)
        if cls.is_image_path(spec):
            px = _size_px(size, cls._default_size[1])
            dims = (int(size[0]), int(size[1])) if isinstance(size, tuple) else (px, px)
            return cls.get_icon(spec, dims, master)
        return None

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

    # --- fallback icons ------------------------------------------------------

    @classmethod
    def get_fallback_text(cls, fallback_key: str | None = None) -> str:
        """Icon spec used when a tab has no icon (a built-in name by default)."""
        if fallback_key and fallback_key in cls._fallback_icons:
            return cls._fallback_icons[fallback_key]
        return cls._fallback_icons["default"]

    get_fallback_icon = get_fallback_text

    @classmethod
    def add_fallback_icon(cls, key: str, icon: str):
        cls._fallback_icons[key] = icon

    @classmethod
    def get_fallback_icons(cls) -> dict[str, str]:
        return cls._fallback_icons.copy()
