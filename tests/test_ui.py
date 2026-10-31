"""Tests for the modern UI: built-in icons, themes, close glyph, toasts."""

import contextlib
import tkinter as tk
from tkinter import ttk

import pytest

from flextabs import (
    DARK,
    LIGHT,
    IconManager,
    Palette,
    TabConfig,
    TabContent,
    TabManager,
    ToastNotification,
    TooltipWidget,
    apply_app_theme,
)
from flextabs.theme import palette_for, palette_from_style, resolve_palette


class Content(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text=self.tab_id).pack()


@pytest.fixture
def root():
    root = tk.Tk()
    root.withdraw()
    yield root
    for toast in list(ToastNotification._active_toasts):
        with contextlib.suppress(tk.TclError):
            toast.destroy()
    ToastNotification._active_toasts.clear()
    root.destroy()


def configs(*ids, **kwargs):
    return [TabConfig(i, i.upper(), Content, **kwargs) for i in ids]


# --- Built-in icons --------------------------------------------------------------


def test_builtin_icons_render(root):
    names = IconManager.builtin_names()
    assert {"home", "settings", "file", "close", "info", "x-circle"} <= set(names)
    for name in names:
        image = IconManager.get_builtin_icon(name, 16, "#123456", root)
        assert image is not None, name
        assert image.height() == 16


def test_builtin_icons_cached_per_size_and_color(root):
    a = IconManager.get_builtin_icon("home", 16, "#000000", root)
    assert IconManager.get_builtin_icon("home", 16, "#000000", root) is a
    assert IconManager.get_builtin_icon("home", 20, "#000000", root) is not a
    assert IconManager.get_builtin_icon("home", 16, "#ff0000", root) is not a


def test_unknown_builtin_icon_is_none(root):
    assert IconManager.get_builtin_icon("no-such-icon", 16, "#000", root) is None


def test_builtin_names_are_not_text_icons():
    assert IconManager.is_builtin("home")
    assert not IconManager.is_text_icon("home")
    assert IconManager.is_text_icon("Hm")


def test_register_custom_icon(root):
    IconManager.register_icon("dot-test", '<circle cx="12" cy="12" r="4"/>')
    try:
        assert IconManager.is_builtin("dot-test")
        assert IconManager.get_builtin_icon("dot-test", 12, "#000", root) is not None
    finally:
        IconManager._svg_icons.pop("dot-test")


def test_fallback_icons_are_builtin_names():
    for key, spec in IconManager.get_fallback_icons().items():
        assert IconManager.is_builtin(spec), key


# --- Themes ----------------------------------------------------------------------


def test_manager_does_not_change_global_ttk_theme(root):
    style = ttk.Style(root)
    before = style.theme_use()
    for theme in ("auto", "light", "dark"):
        TabManager(root, configs("a"), theme=theme)
    assert style.theme_use() == before


def test_auto_palette_blends_with_app_theme(root):
    palette = palette_from_style(root)
    style = ttk.Style(root)
    expected = root.winfo_rgb(style.lookup("TFrame", "background"))
    assert root.winfo_rgb(palette.surface) == expected


def test_resolve_palette(root):
    assert resolve_palette("light", root) is LIGHT
    assert resolve_palette("dark", root) is DARK
    custom = Palette(**{**LIGHT.__dict__, "name": "custom", "accent": "#ff0000"})
    assert resolve_palette(custom, root) is custom
    with pytest.raises(ValueError, match="Unknown theme"):
        resolve_palette("neon", root)


def test_native_theme_keeps_plain_ttk_look(root):
    m = TabManager(root, configs("a"), opener_type="toolbar", theme=None)
    m.open_tab("a")
    assert m.theme is None
    assert m.opener.buttons["a"].cget("style") == ""
    assert m.notebook.cget("style") == "TabManager.TNotebook"


def test_dark_theme_styles(root):
    m = TabManager(root, configs("a"), opener_type="sidebar", theme="dark")
    style = ttk.Style(root)
    assert style.lookup(m.theme.nav_button, "background") == DARK.bg
    assert style.lookup(m.theme.notebook + ".Tab", "background") == DARK.bg
    assert m.notebook.cget("style") == m.theme.notebook


def test_tab_icon_is_state_mapped(root):
    m = TabManager(root, configs("a", icon="home"), theme="light")
    m.open_tab("a")
    image = m.notebook.tab(m.tab_states["a"]["tab_object"], "image")
    # muted image normally, full-colour image for selected/active states
    flat = [str(x) for x in (image if isinstance(image, tuple) else (image,))]
    assert "selected" in " ".join(flat)


def test_set_theme_at_runtime_keeps_tabs(root):
    m = TabManager(root, configs("a", "b"), opener_type="sidebar", theme="light")
    m.open_tab("a")
    m.open_tab("b")
    root.update()
    m.set_theme("dark")
    root.update()
    assert m.theme.palette is DARK
    assert m.get_open_tabs() == ["a", "b"]
    assert m.notebook.cget("style") == m.theme.notebook
    assert m.opener.buttons["a"].cget("style") == m.theme.nav_button
    assert "alternate" in m.opener.buttons["a"].state()
    assert "selected" in m.opener.buttons["b"].state()

    m.set_theme(None)
    assert m.notebook.cget("style") == "TabManager.TNotebook"
    assert m.opener.buttons["a"].cget("style") == ""


def test_auto_theme_follows_app_theme_change(root):
    m = TabManager(root, configs("a"), theme="auto")
    before = m.theme.palette.name
    apply_app_theme(root, "dark")
    root.update()
    assert m.theme.palette.name != before
    assert m.theme.palette.dark


def test_apply_app_theme_registers_palette(root):
    palette = apply_app_theme(root, "dark")
    assert palette is DARK
    assert ttk.Style(root).theme_use() == "clam"
    assert palette_for(root) is DARK


# --- Openers ---------------------------------------------------------------------


def test_sidebar_title_is_above_buttons(root):
    m = TabManager(root, configs("a"), opener_config={"title": "Navigation"})
    slaves = m.opener.container.pack_slaves()
    assert slaves[0] is m.opener._widgets["title"]
    assert slaves[1] is m.opener.buttons_frame


def test_menu_uses_palette_colors(root):
    m = TabManager(root, configs("a", icon="home"), opener_type="menu", theme="dark")
    menu = m.opener.tabs_menu
    assert str(menu.cget("background")) == DARK.surface
    assert menu.entrycget(0, "image")
    assert menu.entrycget(0, "label") == "A"


# --- Close glyph -----------------------------------------------------------------


class Ev:
    """Minimal stand-in for a Tk mouse event."""

    def __init__(self, x, y):
        self.x, self.y = x, y


def closable_manager(root, cfgs, **kwargs):
    root.deiconify()
    root.geometry("600x300")
    m = TabManager(root, cfgs, close_button_style="button", **kwargs)
    m.pack(fill="both", expand=True)
    return m


def glyph_x(m, tab_id, y=10):
    """x of the close glyph on ``tab_id`` (scanning the tab row)."""
    nb = m.notebook
    return next(
        (
            x
            for x in range(nb.winfo_width())
            if nb.identify(x, y) == m._close_style.element
            and m._get_tab_id_at_position(x, y) == tab_id
        ),
        None,
    )


def click(m, x, y=10, release_x=None):
    m._on_close_glyph_press(Ev(x, y))
    m._on_close_glyph_click(Ev(x if release_x is None else release_x, y))


def test_close_glyph_closes_tab(root):
    m = closable_manager(root, configs("a", "b"))
    m.open_tab("a")
    m.open_tab("b")
    root.update()
    assert m.theme.has_close_glyph
    assert m.notebook.cget("style") == m._close_style.style

    x = glyph_x(m, "b")
    assert x is not None
    click(m, x)
    assert m.get_open_tabs() == ["a"]


def test_unclosable_tab_shows_lock_not_close(root):
    cfg = [TabConfig("a", "A", Content), TabConfig("p", "P", Content, closable=False)]
    m = closable_manager(root, cfg)
    m.open_tab("a")
    m.open_tab("p")
    root.update()
    images = m.theme.images(m)
    selected = m._close_style.selected_image
    assert selected.data() == images["lock"].data()

    # Clicking the lock does nothing (no close, no warning toast)
    toasts = len(ToastNotification._active_toasts)
    x = glyph_x(m, "p")
    assert x is not None
    click(m, x)
    assert m.get_open_tabs() == ["a", "p"]
    assert len(ToastNotification._active_toasts) == toasts

    m.select_tab("a")
    root.update()
    assert selected.data() == images["close"].data()


def test_hover_glyph_follows_hovered_tab(root):
    cfg = [TabConfig("a", "A", Content), TabConfig("p", "P", Content, closable=False)]
    m = closable_manager(root, cfg)
    m.open_tab("a")
    m.open_tab("p")
    root.update()
    images = m.theme.images(m)
    hover = m._close_style.hover_image
    a_x = next(x for x in range(300) if m._get_tab_id_at_position(x, 10) == "a")
    m._on_notebook_motion(Ev(a_x, 10))
    assert hover.data() == images["close"].data()
    p_x = next(x for x in range(600) if m._get_tab_id_at_position(x, 10) == "p")
    m._on_notebook_motion(Ev(p_x, 10))
    assert hover.data() == images["lock"].data()


def test_drag_onto_other_tabs_glyph_does_not_close(root):
    m = closable_manager(root, configs("a", "b"))
    m.open_tab("a")
    m.open_tab("b")
    root.update()
    x = glyph_x(m, "b")
    a_label_x = 20
    # press on tab a's label, release on tab b's glyph
    click(m, a_label_x, release_x=x)
    assert m.get_open_tabs() == ["a", "b"]


def test_click_on_tab_label_does_not_close(root):
    root.deiconify()
    m = TabManager(root, configs("a"), close_button_style="button")
    m.pack(fill="both", expand=True)
    m.open_tab("a")
    root.update()

    click(m, 20)
    assert m.get_open_tabs() == ["a"]


def test_add_close_button_has_icon(root):
    m = TabManager(root, configs("a"))
    m.open_tab("a")
    button = m.add_close_button(m.get_tab_content("a").frame, "a")
    assert button.cget("text") == "Close"
    assert button.cget("image")


# --- Tooltip and toast -----------------------------------------------------------


def test_tooltip_uses_palette(root):
    apply_app_theme(root, "light")
    button = ttk.Button(root, text="x")
    tip = TooltipWidget(button, "hello")
    tip._show_tooltip()
    label = tip.tooltip.winfo_children()[0]
    assert label.cget("background") == LIGHT.tooltip_bg
    assert label.cget("foreground") == LIGHT.tooltip_fg
    tip._hide_tooltip()


def test_tooltip_keeps_existing_bindings(root):
    button = ttk.Button(root, text="x")
    calls = []
    button.bind("<Enter>", lambda e: calls.append("app"))
    TooltipWidget(button, "hello")
    assert button.bind("<Enter>").count('== "break"} break') == 2


def test_toast_is_a_card_sized_to_content(root):
    root.deiconify()
    root.geometry("600x400")
    root.update()
    ToastNotification.show(root, "Short", duration=5000, toast_type="success")
    ToastNotification.show(root, "Long " * 60, duration=5000, toast_type="error")
    short, long = ToastNotification._active_toasts[-2:]
    root.update()
    assert long.winfo_reqheight() > short.winfo_reqheight()
    # Stacked: the second toast sits below the first
    assert long.winfo_y() >= short.winfo_y() + short.winfo_reqheight()
    images = [w for w in short.winfo_children()[0].winfo_children() if w.cget("image")]
    assert images, "status icon expected"


# --- Review fixes ------------------------------------------------------------------


@pytest.mark.parametrize("opener_type", ["sidebar", "toolbar"])
def test_set_theme_keeps_opener_layout(root, opener_type):
    root.deiconify()
    root.geometry("600x400")
    m = TabManager(root, configs("a", "b"), opener_type=opener_type, theme="light")
    m.pack(fill="both", expand=True)
    m.open_tab("a")
    root.update()
    container = m.opener.container
    size = (container.winfo_width(), container.winfo_height())

    m.set_theme("dark")
    root.update()
    container = m.opener.container
    assert (container.winfo_width(), container.winfo_height()) == size
    assert m.pack_slaves()[-1] is m.notebook


def test_app_theme_change_keeps_auto_opener_layout(root):
    root.deiconify()
    root.geometry("600x400")
    m = TabManager(root, configs("a"), theme="auto")
    m.pack(fill="both", expand=True)
    root.update()
    height = m.opener.container.winfo_height()
    assert height > 100
    ttk.Style(root).theme_use("clam")
    root.update()
    assert m.opener.container.winfo_height() == height


def test_custom_palette_with_reused_name_is_applied(root):
    import dataclasses

    custom = dataclasses.replace(LIGHT, bg="#ff00ff", accent="#ff0000")
    m = TabManager(root, configs("a"), opener_type="sidebar", theme="light")
    m.set_theme(custom)
    style = ttk.Style(root)
    assert style.lookup(m.theme.chrome_frame, "background") == "#ff00ff"
    # The stock light styles are untouched
    other = TabManager(root, configs("a"), theme="light")
    assert style.lookup(other.theme.chrome_frame, "background") == LIGHT.bg


def test_invalid_theme_leaves_manager_unchanged(root):
    m = TabManager(root, configs("a"), theme="auto")
    theme = m.theme
    with pytest.raises(ValueError):
        m.set_theme("solarized")
    assert m.theme is theme
    assert m._theme_spec == "auto"


def test_plain_look_marks_open_tabs_with_selected(root):
    m = TabManager(root, configs("a", "b"), opener_type="toolbar", theme=None)
    m.open_tab("a")
    root.update()
    state = m.opener.buttons["a"].state()
    assert "selected" in state
    assert "alternate" not in state
    assert "selected" not in m.opener.buttons["b"].state()


def test_theme_caches_drop_destroyed_roots():
    from flextabs.theme import Theme, _interp_alive, _registered

    for _ in range(3):
        r = tk.Tk()
        r.withdraw()
        TabManager(r, configs("a"), theme="light", close_button_style="button")
        r.destroy()
    r = tk.Tk()
    r.withdraw()
    try:
        TabManager(r, configs("a"), theme="light")
        assert all(_interp_alive(i) for i in Theme._applied.values())
        assert all(_interp_alive(e[1]) for e in Theme._images.values())
        assert all(_interp_alive(e[1]) for e in _registered.values())
    finally:
        r.destroy()


def test_set_theme_does_not_clear_other_managers_icons(root):
    a = TabManager(root, configs("a", icon="home"), theme="light")
    b = TabManager(root, configs("b", icon="home"), theme="light")
    b.open_tab("b")
    cached = IconManager.get_builtin_icon("home", 16, LIGHT.text, root)
    a.set_theme("dark")
    assert IconManager.get_builtin_icon("home", 16, LIGHT.text, root) is cached
