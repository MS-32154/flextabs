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


def label_x(m, tab_id, y=10):
    """x of the title label on ``tab_id`` (independent of font metrics)."""
    nb = m.notebook
    return next(
        (
            x
            for x in range(nb.winfo_width())
            if nb.identify(x, y) == "FlexTabs.label"
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
    a_label_x = label_x(m, "a")
    assert a_label_x is not None
    # press on tab a's label, release on tab b's glyph
    click(m, a_label_x, release_x=x)
    assert m.get_open_tabs() == ["a", "b"]


def test_click_on_tab_label_does_not_close(root):
    root.deiconify()
    m = TabManager(root, configs("a"), close_button_style="button")
    m.pack(fill="both", expand=True)
    m.open_tab("a")
    root.update()

    x = label_x(m, "a")
    assert x is not None
    click(m, x)
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
        assert all(_interp_alive(e[0]) for e in _registered.values())
    finally:
        r.destroy()


def test_set_theme_does_not_clear_other_managers_icons(root):
    a = TabManager(root, configs("a", icon="home"), theme="light")
    b = TabManager(root, configs("b", icon="home"), theme="light")
    b.open_tab("b")
    cached = IconManager.get_builtin_icon("home", 16, LIGHT.text, root)
    a.set_theme("dark")
    assert IconManager.get_builtin_icon("home", 16, LIGHT.text, root) is cached


# --- Fonts and DPI ---------------------------------------------------------------


def test_pick_font_family_is_case_insensitive(root):
    from tkinter import font as tkfont

    from flextabs.theme import pick_font_family

    existing = tkfont.families(root=root)[0]
    assert pick_font_family(root, ("No Such Font", existing.upper())) == existing
    assert pick_font_family(root, ("No Such Font",)) is None


def test_apply_fonts_explicit_family(root):
    from tkinter import font as tkfont

    from flextabs import apply_fonts

    family = tkfont.families(root=root)[0]
    assert apply_fonts(root, family, size=11) == family
    default = tkfont.nametofont("TkDefaultFont", root=root)
    assert default.cget("family") == family
    assert default.cget("size") == 11
    assert tkfont.nametofont("TkHeadingFont", root=root).cget("family") == family


def test_apply_fonts_auto_prefers_ui_fonts(root, monkeypatch):
    from tkinter import font as tkfont

    from flextabs import apply_fonts, theme

    real = tkfont.families(root=root)
    fake = (*real, "noto sans")  # pretend a preferred UI font is installed
    monkeypatch.setattr(theme.tkfont, "families", lambda root=None: fake)
    assert apply_fonts(root) == "noto sans"


def test_apply_fonts_none_and_no_candidates_leave_fonts(root, monkeypatch):
    from tkinter import font as tkfont

    from flextabs import apply_fonts, theme

    before = tkfont.nametofont("TkDefaultFont", root=root).actual()
    assert apply_fonts(root, None) is None
    monkeypatch.setattr(theme.tkfont, "families", lambda root=None: ("clean",))
    assert apply_fonts(root) is None
    apply_app_theme(root, "light", font_family=None)
    assert tkfont.nametofont("TkDefaultFont", root=root).actual() == before


def test_enable_dpi_awareness_is_noop_off_windows():
    from flextabs import enable_dpi_awareness

    assert enable_dpi_awareness() is False


def test_enable_dpi_awareness_on_windows(monkeypatch):
    import ctypes
    import sys

    from flextabs import dpi

    calls = []

    class Shcore:
        def SetProcessDpiAwareness(self, level):
            calls.append(level)
            return 0

    class Windll:
        shcore = Shcore()

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "windll", Windll(), raising=False)
    assert dpi.enable_dpi_awareness() is True
    assert calls == [2]


# --- Second review fixes -----------------------------------------------------------


def toast_messages():
    """Messages of the toasts currently on screen."""
    messages = []
    for toast in ToastNotification._active_toasts:
        card = toast.winfo_children()[0]
        messages += [w.cget("text") for w in card.winfo_children() if w.cget("text")]
    return messages


@pytest.fixture
def clean_toasts():
    ToastNotification._queue.clear()
    ToastNotification._is_showing = False
    yield
    ToastNotification._queue.clear()
    ToastNotification._is_showing = False


def test_queued_toast_with_destroyed_parent_does_not_block_queue(root, clean_toasts):
    frame = ttk.Frame(root)
    ToastNotification.show(frame, "first", 10_000, mode="queued")
    ToastNotification.show(frame, "orphan", 10_000, mode="queued")
    frame.destroy()
    ToastNotification._active_toasts[-1].event_generate("<Button-1>")  # dismiss
    assert ToastNotification._is_showing is False

    ToastNotification.show(root, "later", 10_000, mode="queued")
    assert "later" in toast_messages()


def test_stacked_toast_does_not_steal_from_queue(root, clean_toasts):
    ToastNotification.show(root, "q1", 10_000, mode="queued")
    ToastNotification.show(root, "q2", 10_000, mode="queued")
    ToastNotification.show(root, "stacked", 10_000)
    assert "stacked" in toast_messages()
    assert "q2" not in toast_messages()
    assert [t[1] for t in ToastNotification._queue] == ["q2"]


def test_int_icon_size_with_image_file(root, tmp_path):
    from PIL import Image

    path = tmp_path / "icon.png"
    Image.new("RGB", (32, 32), "red").save(path)
    m = TabManager(
        root,
        configs("a", icon=str(path)),
        opener_type="toolbar",
        opener_config={"icon_size": 20},
    )
    image = m.opener.buttons["a"].cget("image")
    assert image
    assert int(root.tk.call("image", "height", str(image[0]))) == 20


def test_palette_unregistered_when_theme_removed_or_destroyed(root):
    apply_app_theme(root, "light")
    m = TabManager(root, configs("a"), theme="dark")
    assert palette_for(root) is DARK
    m.set_theme(None)
    assert palette_for(root) is LIGHT  # back to the app's palette

    m.set_theme("dark")
    assert palette_for(root) is DARK
    m.destroy()
    assert palette_for(root) is LIGHT


def test_create_simple_tab_manager_accepts_overrides(root):
    from flextabs import create_simple_tab_manager

    m = create_simple_tab_manager(
        root, configs("a"), close_button_style="button", enable_keyboard_shortcuts=False
    )
    assert m.close_button_style == "button"
    assert m.enable_keyboard_shortcuts is False


def test_hover_glyph_after_theme_switch(root):
    m = closable_manager(root, configs("a", "b"))
    m.open_tab("a")
    m.open_tab("b")
    root.update()
    a_x = next(x for x in range(300) if m._get_tab_id_at_position(x, 10) == "a")
    m._on_notebook_motion(Ev(a_x, 10))
    m.set_theme("dark")
    root.update()
    m._on_notebook_motion(Ev(a_x, 10))
    assert m._close_style.hover_image.data() == m.theme.images(m)["close"].data()


def test_close_glyph_style_reused_per_palette(root):
    m = closable_manager(root, configs("a"))
    m.set_theme("dark")
    dark_style = m._close_style
    m.set_theme("light")
    m.set_theme("dark")
    assert m._close_style is dark_style
    assert m.notebook.cget("style") == dark_style.style


def test_refresh_does_not_accumulate_tooltips(root):
    m = TabManager(root, configs("a", "b", tooltip="tip"), opener_type="toolbar")
    for i in range(3):
        m.add_tab_config(TabConfig(f"x{i}", "X", Content, tooltip="tip"))
    assert len(m.opener._tooltips) == len(m.opener.buttons) == 5


def test_tooltip_after_widget_destroyed_is_harmless(root):
    button = ttk.Button(root, text="x")
    tip = TooltipWidget(button, "hello")
    button.destroy()
    tip._show_tooltip()  # e.g. a pending after() firing late
    assert tip.tooltip is None


def test_rebuilt_opener_packed_before_notebook(root):
    m = TabManager(root, configs("a"), opener_type="sidebar", theme="light")
    m.set_theme("dark")
    slaves = m.pack_slaves()
    assert slaves[-1] is m.notebook
    assert slaves.index(m.opener.container) < slaves.index(m.notebook)
