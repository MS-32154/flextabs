"""Palettes and flat ttk styles for FlexTabs widgets.

FlexTabs never switches the application's ttk theme on its own. It builds its
own namespaced styles (``FlexTabs.<palette>.*``) from elements cloned out of
Tk's built-in ``default`` theme, so they look the same on every platform and
leave the app's other widgets untouched.

``apply_app_theme()`` is an explicit opt-in that restyles the whole app to
match a palette (it switches to the ``clam`` theme).
"""

import contextlib
import hashlib
import itertools
import tkinter as tk
from dataclasses import dataclass, replace
from tkinter import font as tkfont
from tkinter import ttk
from typing import ClassVar

from .icons import IconManager

# --- colours -------------------------------------------------------------------


def _rgb(widget: tk.Misc, color: str) -> tuple[int, int, int]:
    r, g, b = widget.winfo_rgb(color)
    return r // 257, g // 257, b // 257


def _hex(rgb: tuple[float, float, float]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c))) for c in rgb))


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> str:
    """Blend colour ``a`` towards ``b`` by fraction ``t``."""
    return _hex(tuple(x + (y - x) * t for x, y in zip(a, b, strict=True)))


def _luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


@dataclass(frozen=True)
class Palette:
    """Colours used by FlexTabs widgets.

    ``bg`` is the chrome (sidebar, toolbar, tab bar); ``surface`` is the
    content area and the selected tab.
    """

    name: str
    surface: str
    bg: str
    hover: str
    selected: str
    border: str
    text: str
    text_muted: str
    accent: str
    on_accent: str
    tooltip_bg: str
    tooltip_fg: str
    info: str
    success: str
    warning: str
    error: str
    dark: bool = False

    def status_color(self, kind: str) -> str:
        return getattr(self, kind, self.info) if kind in _STATUS else self.info


_STATUS = frozenset({"info", "success", "warning", "error"})

LIGHT = Palette(
    name="light",
    surface="#ffffff",
    bg="#f4f4f5",
    hover="#e9e9ec",
    selected="#e4e4e7",
    border="#e4e4e7",
    text="#18181b",
    text_muted="#71717a",
    accent="#2563eb",
    on_accent="#ffffff",
    tooltip_bg="#27272a",
    tooltip_fg="#fafafa",
    info="#2563eb",
    success="#16a34a",
    warning="#d97706",
    error="#dc2626",
)

DARK = Palette(
    name="dark",
    surface="#18181b",
    bg="#111113",
    hover="#232327",
    selected="#2a2a2f",
    border="#2e2e33",
    text="#f4f4f5",
    text_muted="#a1a1aa",
    accent="#3b82f6",
    on_accent="#ffffff",
    tooltip_bg="#f4f4f5",
    tooltip_fg="#18181b",
    info="#60a5fa",
    success="#4ade80",
    warning="#fbbf24",
    error="#f87171",
    dark=True,
)

PRESETS = {"light": LIGHT, "dark": DARK}


def palette_from_style(widget: tk.Misc) -> Palette:
    """Derive a palette that blends with the app's current ttk theme."""
    style = ttk.Style(widget)
    surface_name = style.lookup("TFrame", "background") or "#ffffff"
    text_name = style.lookup("TLabel", "foreground") or "#000000"
    try:
        surface = _rgb(widget, surface_name)
        text = _rgb(widget, text_name)
    except tk.TclError:
        return LIGHT

    dark = _luminance(surface) < 0.4
    base = LIGHT if not dark else DARK
    shade = (255, 255, 255) if dark else (0, 0, 0)
    return replace(
        base,
        name=f"auto-{_hex(surface)[1:]}-{_hex(text)[1:]}",
        surface=_hex(surface),
        bg=_mix(surface, shade, 0.035),
        hover=_mix(surface, shade, 0.075),
        selected=_mix(surface, shade, 0.1),
        border=_mix(surface, shade, 0.13),
        text=_hex(text),
        text_muted=_mix(text, surface, 0.42),
    )


def _interp_alive(interp) -> bool:
    """True if the Tk application behind ``interp`` has not been destroyed."""
    try:
        interp.call("winfo", "exists", ".")
        return True
    except tk.TclError, RuntimeError:
        return False


def _prune_dead_interps(cache: dict, interp_of) -> None:
    """Remove entries whose Tk application is gone (they pin the interpreter)."""
    for key in [k for k, v in cache.items() if not _interp_alive(interp_of(v))]:
        del cache[key]


# --- palette registry (lets toasts/tooltips match the nearest manager) ---------

# (id(interp), toplevel path) -> (interpreter, [(owner, palette), ...]); the
# most recent registration wins and owners remove only their own entries.
_registered: dict[tuple[int, str], tuple[object, list[tuple[object, Palette]]]] = {}


def _window_key(widget: tk.Misc) -> tuple[int, str]:
    return (id(widget.tk), str(widget.winfo_toplevel()))


def register_palette(widget: tk.Misc, palette: Palette, owner: object = "app"):
    """Associate ``palette`` with the window containing ``widget``.

    ``owner`` identifies who registered it, so :func:`unregister_palette` can
    remove it again without affecting other owners in the same window.
    """
    _prune_dead_interps(_registered, lambda entry: entry[0])
    key = _window_key(widget)
    interp, stack = _registered.get(key, (widget.tk, []))
    if interp is not widget.tk:
        stack = []
    stack = [entry for entry in stack if entry[0] != owner]
    stack.append((owner, palette))
    _registered[key] = (widget.tk, stack)


def unregister_palette(widget: tk.Misc, owner: object = "app"):
    """Remove ``owner``'s palette for ``widget``'s window, if registered."""
    with contextlib.suppress(tk.TclError):
        key = _window_key(widget)
        entry = _registered.get(key)
        if entry is None:
            return
        stack = [item for item in entry[1] if item[0] != owner]
        if stack:
            _registered[key] = (entry[0], stack)
        else:
            del _registered[key]


def palette_for(widget: tk.Misc) -> Palette:
    """Palette registered for ``widget``'s window, else derived from ttk."""
    with contextlib.suppress(tk.TclError):
        entry = _registered.get(_window_key(widget))
        if entry is not None and entry[0] is widget.tk and entry[1]:
            return entry[1][-1][1]
    try:
        return palette_from_style(widget)
    except tk.TclError:
        return LIGHT


def resolve_palette(spec: str | Palette, widget: tk.Misc) -> Palette:
    """Turn ``"auto"``, ``"light"``, ``"dark"`` or a Palette into a Palette."""
    if isinstance(spec, Palette):
        return spec
    if spec == "auto":
        return palette_from_style(widget)
    if spec in PRESETS:
        return PRESETS[spec]
    raise ValueError(
        f"Unknown theme {spec!r}; use 'auto', 'light', 'dark', a Palette or None"
    )


# --- ttk styles ----------------------------------------------------------------

_SHARED_ELEMENTS = {  # our name -> element cloned from the 'default' theme
    "FlexTabs.border": "border",
    "FlexTabs.padding": "padding",
    "FlexTabs.label": "label",
    "FlexTabs.client": "client",
}


def _palette_key(palette: Palette) -> str:
    """Style-safe identifier unique to a palette's name *and* colours."""
    digest = hashlib.sha1(repr(palette).encode()).hexdigest()[:8]
    name = "".join(c if c.isalnum() else "-" for c in palette.name)
    return f"{name}-{digest}"


class ClosableNotebookStyle:
    """A notebook style whose close glyph images belong to one notebook.

    The glyph is a layout element shared by every tab, so it cannot differ per
    tab. Instead, the images shown for the selected and the hovered tab are
    swapped in place: a close glyph for closable tabs, a lock otherwise.
    """

    _ids = itertools.count(1)

    def __init__(self, theme: Theme, widget: tk.Misc):
        self.theme = theme
        uid = next(self._ids)
        self.style = f"{theme.prefix}.Closable{uid}.TNotebook"
        self.element = f"{theme.prefix}.close{uid}"
        self.selected_image = tk.PhotoImage(master=widget, width=20, height=12)
        self.hover_image = tk.PhotoImage(master=widget, width=20, height=12)
        self.ensure(widget)

    def ensure(self, widget: tk.Misc):
        """(Re)create the element and style in the current ttk theme."""
        style = ttk.Style(widget)
        with contextlib.suppress(tk.TclError):  # exists already in this theme
            style.element_create(
                self.element,
                "image",
                self.theme.images(widget)["close_blank"],
                ("active", self.hover_image),
                ("selected", self.selected_image),
                sticky="",
            )
        self.theme.configure_notebook(style, self.style, close_element=self.element)

    def _show(self, image: tk.PhotoImage, glyph: str, widget: tk.Misc):
        source = self.theme.images(widget).get(glyph)
        image.blank()
        if source is not None:
            image.tk.call(image, "copy", source, "-to", 0, 0)

    def show_selected(self, closable: bool | None, widget: tk.Misc):
        """Glyph for the selected tab: close, lock (not closable) or nothing."""
        glyph = "close_blank" if closable is None else ("close" if closable else "lock")
        self._show(self.selected_image, glyph, widget)

    def show_hover(self, closable: bool | None, widget: tk.Misc):
        """Glyph for the hovered tab."""
        glyph = "close_blank" if closable is None else ("close" if closable else "lock")
        self._show(self.hover_image, glyph, widget)


class Theme:
    """Flat ttk styles for one palette, created on demand per Tk interpreter."""

    # (id(interp), ttk theme name, palette key) -> interpreter
    _applied: ClassVar[dict[tuple[int, str, str], object]] = {}
    # (id(interp), palette key) -> (images that must stay referenced, interpreter)
    _images: ClassVar[dict[tuple[int, str], tuple[dict, object]]] = {}

    def __init__(self, palette: Palette):
        self.palette = palette
        self.key = _palette_key(palette)
        self.prefix = f"FlexTabs.{self.key}"
        self.has_close_glyph = False

    # Style names ---------------------------------------------------------------

    @property
    def chrome_frame(self) -> str:
        return f"{self.prefix}.Chrome.TFrame"

    @property
    def surface_frame(self) -> str:
        return f"{self.prefix}.Surface.TFrame"

    @property
    def divider(self) -> str:
        return f"{self.prefix}.Divider.TFrame"

    @property
    def title_label(self) -> str:
        return f"{self.prefix}.Title.TLabel"

    @property
    def nav_button(self) -> str:
        return f"{self.prefix}.Nav.TButton"

    @property
    def toolbar_button(self) -> str:
        return f"{self.prefix}.Toolbar.TButton"

    @property
    def notebook(self) -> str:
        return f"{self.prefix}.TNotebook"

    def closable_notebook_style(self, widget: tk.Misc) -> ClosableNotebookStyle:
        """A per-notebook style with a swappable close/lock glyph."""
        return ClosableNotebookStyle(self, widget)

    def menu_options(self) -> dict[str, str | int]:
        p = self.palette
        return {
            "background": p.surface,
            "foreground": p.text,
            "activebackground": p.hover,
            "activeforeground": p.text,
            "borderwidth": 1,
            "relief": "solid",
        }

    # Icons ---------------------------------------------------------------------

    def icon_states(
        self, spec: str | None, size, master: tk.Misc, selectable: bool = True
    ):
        """ttk image spec for an icon: muted normally, full colour when active.

        Returns a single image for image files, a state-mapped tuple for
        built-in icons, or None if the spec is not an image.
        """
        p = self.palette
        if IconManager.is_builtin(spec):
            muted = IconManager.get_builtin_icon(spec, size, p.text_muted, master)
            strong = IconManager.get_builtin_icon(spec, size, p.text, master)
            if muted is None or strong is None:
                return None
            if not selectable:
                return strong
            states = ("selected", "alternate", "active", "focus")
            spec_list: list = [muted]
            for state in states:
                spec_list += [state, strong]
            return tuple(spec_list)
        return IconManager.render(spec, size, p.text, master)

    # Creation ------------------------------------------------------------------

    def ensure(self, widget: tk.Misc):
        """Create this palette's elements and styles in ``widget``'s ttk theme."""
        style = ttk.Style(widget)
        interp = widget.tk
        key = (id(interp), style.theme_use(), self.key)
        if self._applied.get(key) is interp:
            self.has_close_glyph = self.images(widget).get("close") is not None
            return
        _prune_dead_interps(self._applied, lambda entry: entry)

        for name, source in _SHARED_ELEMENTS.items():
            with contextlib.suppress(tk.TclError):  # already exists in this theme
                style.element_create(name, "from", "default", source)

        images = self.images(widget)
        p, P = self.palette, self.prefix

        def image_element(name: str, normal: str, *state_images, **kw):
            with contextlib.suppress(tk.TclError):
                style.element_create(name, "image", images[normal], *state_images, **kw)

        # Accent indicators: a 2px bar tiled along the edge (border=0 tiles)
        image_element(
            f"{P}.navbar", "bar_v_off", ("selected", images["bar_v"]), sticky="ns"
        )
        image_element(
            f"{P}.tabbar", "bar_h_off", ("selected", images["bar_h"]), sticky="ew"
        )
        self.has_close_glyph = images.get("close") is not None

        default_font = tkfont.nametofont("TkDefaultFont", root=widget).actual()
        title_font = (default_font["family"], max(8, default_font["size"] - 1), "bold")

        # Frames and labels
        style.configure(self.chrome_frame, background=p.bg)
        style.configure(self.surface_frame, background=p.surface)
        style.configure(self.divider, background=p.border)
        style.configure(
            self.title_label,
            background=p.bg,
            foreground=p.text_muted,
            font=title_font,
            padding=(14, 12, 14, 6),
        )

        # Sidebar and toolbar buttons
        for name, bar_side, sticky, padding in (
            (self.nav_button, "left", "w", (10, 7)),
            (self.toolbar_button, "bottom", "", (12, 8)),
        ):
            bar = (
                f"{P}.navbar" if bar_side == "left" else f"{P}.tabbar",
                {"side": bar_side, "sticky": "ns" if bar_side == "left" else "ew"},
            )
            style.layout(name, [("FlexTabs.border", {"sticky": "nswe", "children": [
                bar,
                ("FlexTabs.padding", {"sticky": "nswe", "children": [
                    ("FlexTabs.label", {"sticky": sticky}),
                ]}),
            ]})])  # fmt: skip
            style.configure(
                name,
                background=p.bg,
                foreground=p.text_muted,
                relief="flat",
                borderwidth=0,
                padding=padding,
                anchor="w" if sticky else "center",
                width=0,  # natural width (clam gives TButton a minimum width)
            )
            style.map(
                name,
                background=[
                    ("pressed", p.selected), ("selected", p.selected),
                    ("active", p.hover), ("focus", p.hover),
                ],
                foreground=[
                    ("selected", p.text), ("alternate", p.text),
                    ("active", p.text), ("focus", p.text),
                ],
            )  # fmt: skip

        self.configure_notebook(style, self.notebook)
        self._applied[key] = interp

    def configure_notebook(
        self, style: ttk.Style, notebook: str, close_element: str | None = None
    ):
        """Layout and colours for a notebook style (optionally with a glyph)."""
        p, P = self.palette, self.prefix
        tab = f"{notebook}.Tab"
        label_children = [("FlexTabs.label", {"side": "left", "sticky": ""})]
        if close_element is not None:
            label_children.append((close_element, {"side": "left"}))
        style.layout(notebook, [("FlexTabs.client", {"sticky": "nswe"})])
        style.configure(
            notebook, background=p.bg, borderwidth=0, tabmargins=(0, 0, 0, 0),
            padding=0,
        )  # fmt: skip
        style.layout(tab, [("FlexTabs.border", {"sticky": "nswe", "children": [
            (f"{P}.tabbar", {"side": "bottom", "sticky": "ew"}),
            ("FlexTabs.padding", {"sticky": "nswe", "children": label_children}),
        ]})])  # fmt: skip
        style.configure(
            tab, background=p.bg, foreground=p.text_muted, relief="flat",
            borderwidth=0, padding=(14, 7, 10 if close_element else 14, 7), width=0,
        )  # fmt: skip
        style.map(
            tab,
            background=[("selected", p.surface), ("active", p.hover)],
            foreground=[("selected", p.text), ("active", p.text)],
            expand=[("selected", (0, 0, 0, 0))],
        )  # fmt: skip

    def images(self, widget: tk.Misc) -> dict[str, tk.PhotoImage | None]:
        """Indicator bars and glyph images, kept alive per interpreter."""
        key = (id(widget.tk), self.key)
        entry = self._images.get(key)
        if entry is not None and entry[1] is widget.tk and _interp_alive(entry[1]):
            return entry[0]
        _prune_dead_interps(self._images, lambda entry: entry[1])

        p = self.palette
        images = {}
        for name, (w, h) in (("bar_v", (2, 1)), ("bar_h", (1, 2))):
            bar = tk.PhotoImage(master=widget, width=w, height=h)
            bar.put(p.accent, to=(0, 0, w, h))
            images[name] = bar
            images[f"{name}_off"] = tk.PhotoImage(master=widget, width=w, height=h)
        # Close/lock glyphs with 8px of transparent space before them (element
        # padding is not honoured for image elements by every Tk build)
        for name, icon in (("close", "close"), ("lock", "lock")):
            glyph = IconManager.get_builtin_icon(icon, 12, p.text_muted, widget)
            if glyph is None:
                images[name] = None
                continue
            padded = tk.PhotoImage(master=widget, width=20, height=12)
            padded.tk.call(padded, "copy", glyph, "-to", 8, 0)
            images[name] = padded
        images["close_blank"] = tk.PhotoImage(master=widget, width=20, height=12)
        self._images[key] = (images, widget.tk)
        return images


def resolve_theme(spec: str | Palette | None, widget: tk.Misc) -> Theme | None:
    """Theme for a TabManager ``theme=`` argument (None keeps plain ttk look)."""
    if spec is None or spec == "native":
        return None
    return Theme(resolve_palette(spec, widget))


# --- fonts --------------------------------------------------------------------

# Preferred UI and monospace families on X11, where Tk otherwise often picks a
# legacy font. Windows and macOS already use the native system font.
UI_FONTS = (
    "Ubuntu Sans", "Ubuntu", "Cantarell", "Inter", "Noto Sans", "Segoe UI",
    "Open Sans", "DejaVu Sans", "Liberation Sans",
)  # fmt: skip
MONO_FONTS = (
    "Ubuntu Sans Mono", "Ubuntu Mono", "JetBrains Mono", "Cascadia Mono",
    "Noto Sans Mono", "DejaVu Sans Mono", "Liberation Mono",
)  # fmt: skip

_UI_NAMED_FONTS = (
    "TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
    "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont",
)  # fmt: skip


def pick_font_family(widget: tk.Misc, candidates: tuple[str, ...]) -> str | None:
    """First of ``candidates`` that Tk can use (case-insensitive), else None."""
    available = {f.lower(): f for f in tkfont.families(root=widget)}
    for name in candidates:
        if name.lower() in available:
            return available[name.lower()]
    return None


def apply_fonts(
    root: tk.Misc,
    family: str | None = "auto",
    size: int | None = None,
    mono_family: str | None = "auto",
) -> str | None:
    """Point Tk's named fonts at a modern UI font.

    ``family="auto"`` picks the first available of :data:`UI_FONTS`, and only
    on X11 (other platforms already use the system font). Pass a family name to
    force one, or ``None`` to leave fonts unchanged. ``size`` is in points.
    Returns the family applied, or None if nothing changed.

    Note: Tk builds without Xft (``tk::pkgconfig get fontsystem`` is ``x11``)
    only see legacy X11 fonts, so "auto" usually finds nothing there.
    """
    if family is None:
        return None
    x11 = root.tk.call("tk", "windowingsystem") == "x11"
    if family == "auto":
        family = pick_font_family(root, UI_FONTS) if x11 else None
        if family is None:
            return None
    if mono_family == "auto":
        mono_family = pick_font_family(root, MONO_FONTS) if x11 else None

    for name in _UI_NAMED_FONTS:
        with contextlib.suppress(tk.TclError):
            options: dict = {"family": family}
            if size is not None:
                options["size"] = size
            tkfont.nametofont(name, root=root).configure(**options)
    if mono_family:
        with contextlib.suppress(tk.TclError):
            options = {"family": mono_family}
            if size is not None:
                options["size"] = size
            tkfont.nametofont("TkFixedFont", root=root).configure(**options)
    return family


# --- whole-app theme (opt-in) --------------------------------------------------


def apply_app_theme(
    root: tk.Misc,
    palette: str | Palette = "light",
    font_family: str | None = "auto",
    font_size: int | None = None,
) -> Palette:
    """Restyle the whole application to match a palette.

    This switches the global ttk theme to ``clam`` and recolours the standard
    ttk widgets plus Text/Listbox/Menu defaults, so app content matches
    FlexTabs. Fonts are updated with :func:`apply_fonts` (pass
    ``font_family=None`` to keep them). Returns the palette used.
    """
    p = resolve_palette(palette, root)
    apply_fonts(root, font_family, font_size)
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(
        ".", background=p.surface, foreground=p.text, bordercolor=p.border,
        lightcolor=p.surface, darkcolor=p.surface, troughcolor=p.bg,
        focuscolor=p.accent, selectbackground=p.accent,
        selectforeground=p.on_accent, fieldbackground=p.surface,
        insertcolor=p.text, arrowcolor=p.text_muted,
    )  # fmt: skip
    style.map(".", background=[("disabled", p.surface)],
              foreground=[("disabled", p.text_muted)])  # fmt: skip

    style.configure(
        "TButton", background=p.bg, bordercolor=p.border, lightcolor=p.bg,
        darkcolor=p.bg, padding=(10, 5), focusthickness=1,
    )  # fmt: skip
    style.map(
        "TButton",
        background=[("pressed", p.selected), ("active", p.hover)],
        lightcolor=[("pressed", p.selected), ("active", p.hover)],
        darkcolor=[("pressed", p.selected), ("active", p.hover)],
        bordercolor=[("focus", p.accent)],
    )  # fmt: skip
    style.configure(
        "Accent.TButton", background=p.accent, foreground=p.on_accent,
        bordercolor=p.accent, lightcolor=p.accent, darkcolor=p.accent,
    )  # fmt: skip
    style.map(
        "Accent.TButton",
        background=[("pressed", p.accent), ("active", p.accent)],
        foreground=[("disabled", p.text_muted)],
    )
    style.configure("TLabelframe", background=p.surface, bordercolor=p.border)
    style.configure("TLabelframe.Label", background=p.surface, foreground=p.text_muted)
    style.configure("Muted.TLabel", foreground=p.text_muted)
    for widget_style in ("TRadiobutton", "TCheckbutton"):
        style.configure(
            widget_style, background=p.surface, indicatorbackground=p.surface,
            indicatorforeground=p.accent, upperbordercolor=p.border,
            lowerbordercolor=p.border,
        )  # fmt: skip
        style.map(
            widget_style,
            background=[("active", p.surface)],
            indicatorbackground=[("pressed", p.hover), ("selected", p.accent)],
            indicatorforeground=[("selected", p.on_accent)],
        )  # fmt: skip
    style.configure(
        "Treeview", background=p.surface, fieldbackground=p.surface,
        foreground=p.text, bordercolor=p.border, rowheight=24,
    )  # fmt: skip
    style.map(
        "Treeview",
        background=[("selected", p.selected)],
        foreground=[("selected", p.text)],
    )
    style.configure(
        "Treeview.Heading", background=p.bg, foreground=p.text_muted,
        bordercolor=p.border, lightcolor=p.bg, darkcolor=p.bg, relief="flat",
    )  # fmt: skip
    style.map("Treeview.Heading", background=[("active", p.hover)])
    style.configure(
        "TScrollbar", background=p.bg, troughcolor=p.surface,
        bordercolor=p.surface, lightcolor=p.bg, darkcolor=p.bg,
        arrowcolor=p.text_muted,
    )  # fmt: skip
    style.configure(
        "TEntry", fieldbackground=p.surface, bordercolor=p.border,
        lightcolor=p.surface, darkcolor=p.surface,
    )  # fmt: skip
    style.map("TEntry", bordercolor=[("focus", p.accent)],
              lightcolor=[("focus", p.accent)])  # fmt: skip
    style.configure("TSeparator", background=p.border)

    with contextlib.suppress(tk.TclError):
        root.configure(background=p.surface)
    for option, value in (
        ("*Text.background", p.surface), ("*Text.foreground", p.text),
        ("*Text.insertBackground", p.text), ("*Text.selectBackground", p.accent),
        ("*Text.selectForeground", p.on_accent), ("*Text.highlightThickness", 0),
        ("*Text.borderWidth", 0), ("*Listbox.background", p.surface),
        ("*Listbox.foreground", p.text), ("*Menu.background", p.surface),
        ("*Menu.foreground", p.text), ("*Menu.activeBackground", p.hover),
        ("*Menu.activeForeground", p.text),
    ):  # fmt: skip
        root.option_add(option, value)

    register_palette(root, p)
    return p
