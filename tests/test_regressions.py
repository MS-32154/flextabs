"""Regression tests for previously confirmed bugs."""

import tkinter as tk
from tkinter import ttk
from typing import ClassVar

import pytest
from PIL import Image

from flextabs import IconManager, TabConfig, TabContent, TabManager


class SimpleContent(TabContent):
    cleanups: ClassVar[list[str]] = []

    def setup_content(self):
        ttk.Label(self.frame, text=self.tab_id).pack()

    def cleanup(self):
        SimpleContent.cleanups.append(self.tab_id)
        super().cleanup()


class VetoContent(SimpleContent):
    def on_tab_close(self):
        return False


@pytest.fixture
def root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture(autouse=True)
def _reset_cleanups():
    SimpleContent.cleanups = []


@pytest.fixture
def icon_file(tmp_path):
    path = tmp_path / "icon.png"
    Image.new("RGB", (32, 32), "red").save(path)
    return str(path)


def configs(*ids, **kwargs):
    return [TabConfig(i, i.upper(), SimpleContent, **kwargs) for i in ids]


def binding_count(widget, sequence):
    """Number of separate callbacks bound to ``sequence`` on ``widget``."""
    return widget.bind(sequence).count('== "break"} break')


def tab_text(manager, tab_id):
    return manager.notebook.tab(manager.tab_states[tab_id]["tab_object"], "text")


# --- Icons ---------------------------------------------------------------------


def test_image_icons_work_across_tk_roots(icon_file):
    """Cached PhotoImages from a destroyed root must not be reused."""
    for _ in range(2):
        r = tk.Tk()
        r.withdraw()
        try:
            m = TabManager(r, configs("a", icon=icon_file), opener_type="toolbar")
            assert m.open_tab("a")
            assert m.notebook.tab(m.tab_states["a"]["tab_object"], "image")
        finally:
            r.destroy()


@pytest.mark.parametrize(
    "icon, is_image",
    [
        ("🏠", False),
        ("⚙️", False),
        ("👨‍👩‍👧", False),  # multi-codepoint emoji, len > 4
        ("x", False),
        ("a.png", True),  # short filename, len <= 5
        ("ICON.PNG", True),
        ("icons/home.png", True),
        ("icons/home", True),  # explicit path without extension
        ("No.1", False),  # dot but not an image extension
        ("v2.0", False),
        ("", False),
        (None, False),
    ],
)
def test_icon_kind_detection(icon, is_image):
    assert IconManager.is_image_path(icon) is is_image
    assert IconManager.is_text_icon(icon) is (bool(icon) and not is_image)


def test_long_emoji_shown_in_tab_and_opener(root):
    emoji = "👨‍👩‍👧"
    m = TabManager(root, configs("a", icon=emoji), opener_type="toolbar")
    m.open_tab("a")
    assert tab_text(m, "a").startswith(emoji)
    assert m.opener.buttons["a"].cget("text").startswith(emoji)


def test_missing_image_shows_title_only(root):
    m = TabManager(root, configs("a", icon="does/not/exist.png"), opener_type="toolbar")
    m.open_tab("a")
    assert tab_text(m, "a") == "A"
    assert m.opener.buttons["a"].cget("text") == "A"
    assert not m.opener.buttons["a"].cget("image")


def test_fallback_icon_is_opt_in(root):
    plain = TabManager(root, configs("a"), opener_type="toolbar")
    plain.open_tab("a")
    assert not plain.notebook.tab(plain.tab_states["a"]["tab_object"], "image")
    assert not plain.opener.buttons["a"].cget("image")

    m = TabManager(
        root,
        configs("b"),
        opener_type="toolbar",
        opener_config={"use_fallback_icons": True},
        use_notebook_fallback_icons=True,
    )
    m.open_tab("b")
    assert tab_text(m, "b") == "B"  # fallback is an image, not text
    assert m.notebook.tab(m.tab_states["b"]["tab_object"], "image")
    assert m.opener.buttons["b"].cget("image")


# --- Menu opener ---------------------------------------------------------------


def test_menu_opener_handles_dict_icon(root):
    cfg = [TabConfig("a", "A", SimpleContent, icon={"opener": "🏠", "tab": "📄"})]
    m = TabManager(root, cfg, opener_type="menu")
    assert m.opener.tabs_menu.entrycget(0, "label") == "🏠 A"


def test_menu_opener_shows_image_icon(root, icon_file):
    m = TabManager(root, configs("a", icon=icon_file), opener_type="menu")
    assert m.opener.tabs_menu.entrycget(0, "image")
    assert m.opener.tabs_menu.entrycget(0, "label") == "A"


def test_menu_cascade_removed_on_destroy(root):
    for _ in range(3):
        TabManager(root, configs("a"), opener_type="menu").destroy()
    # The flextabs-created menubar is detached once it is empty
    assert root.menubar is None
    assert root.cget("menu") == ""


def test_shared_menubar_kept_until_last_menu_opener_destroyed(root):
    m1 = TabManager(
        root, configs("a"), opener_type="menu", opener_config={"menu_title": "One"}
    )
    m2 = TabManager(
        root, configs("b"), opener_type="menu", opener_config={"menu_title": "Two"}
    )
    m1.destroy()
    assert root.menubar.entrycget("end", "label") == "Two"
    assert root.cget("menu") == str(root.menubar)
    m2.destroy()
    assert root.menubar is None


def test_app_owned_menubar_is_not_removed(root):
    menubar = tk.Menu(root)
    menubar.add_cascade(label="File", menu=tk.Menu(menubar, tearoff=0))
    root.menubar = menubar
    root.config(menu=menubar)
    TabManager(root, configs("a"), opener_type="menu").destroy()
    assert root.menubar is menubar
    assert root.cget("menu") == str(menubar)
    assert menubar.entrycget("end", "label") == "File"


# --- Cleanup -------------------------------------------------------------------


def test_destroy_cleans_up_all_open_tab_contents(root):
    cfg = [
        TabConfig("a", "A", SimpleContent),
        TabConfig("b", "B", SimpleContent, closable=False),
        TabConfig("c", "C", VetoContent),
    ]
    m = TabManager(root, cfg)
    for tab_id in "abc":
        m.open_tab(tab_id)
    m.destroy()
    assert sorted(SimpleContent.cleanups) == ["a", "b", "c"]


def test_close_destroys_tab_container(root):
    m = TabManager(root, configs("a"))
    m.open_tab("a")
    container = m.tab_states["a"]["tab_object"]
    m.close_tab("a")
    assert not container.winfo_exists()


# --- Keyboard bindings ---------------------------------------------------------


def test_destroy_preserves_app_bindings(root):
    root.bind("<Control-w>", lambda e: None)
    TabManager(root, configs("a")).destroy()
    assert binding_count(root, "<Control-w>") == 1


def test_multiple_managers_keep_their_shortcuts(root):
    m1 = TabManager(root, configs("a"))
    m2 = TabManager(root, configs("a"))
    assert binding_count(root, "<Control-w>") == 2
    m2.destroy()
    assert binding_count(root, "<Control-w>") == 1
    m1.destroy()
    assert binding_count(root, "<Control-w>") == 0


def test_remove_tab_config_unbinds_shortcut(root):
    m = TabManager(root, configs("a") + configs("d", keyboard_shortcut="<F9>"))
    assert binding_count(root, "<F9>") == 1
    m.remove_tab_config("d")
    assert binding_count(root, "<F9>") == 0


def test_runtime_added_shortcut_is_removed_on_destroy(root):
    m = TabManager(root, configs("a"))
    m.add_tab_config(TabConfig("z", "Z", SimpleContent, keyboard_shortcut="<F8>"))
    assert binding_count(root, "<F8>") == 1
    m.destroy()
    assert binding_count(root, "<F8>") == 0


# --- Tab positions -------------------------------------------------------------


def test_open_tab_selects_correct_tab_after_reorder(root):
    m = TabManager(root, configs("a", "b", "c"))
    for tab_id in "abc":
        m.open_tab(tab_id)
    m.notebook.insert(0, m.tab_states["c"]["tab_object"])  # order: c a b
    assert m.get_tab_index("c") == 0
    assert m._get_tab_id_by_index(0) == "c"

    m.open_tab("a")
    assert m._get_tab_id_by_widget(m.notebook.select()) == "a"

    m.close_tab("c")
    assert m.get_open_tabs() == ["a", "b"]
    assert [m._get_tab_id_by_widget(w) for w in m.notebook.tabs()] == ["a", "b"]


def test_current_tab_cleared_when_last_tab_closed(root):
    m = TabManager(root, configs("a"))
    m.open_tab("a")
    root.update()
    assert m.get_current_tab() == "a"
    m.close_tab("a")
    root.update()
    assert m.get_current_tab() is None


# --- Callback errors -----------------------------------------------------------


def test_callback_errors_do_not_fail_open_or_close(root):
    m = TabManager(root, configs("a"))
    errors = []
    m.on_tab_error = lambda tab_id, e: errors.append((tab_id, type(e)))
    m.on_tab_opened = lambda tab_id: 1 / 0
    m.on_tab_closed = lambda tab_id: 1 / 0

    assert m.open_tab("a") is True
    assert m.is_tab_open("a")
    assert m.close_tab("a") is True
    assert not m.is_tab_open("a")
    assert errors == [("a", ZeroDivisionError), ("a", ZeroDivisionError)]


# --- Opener button state -------------------------------------------------------


@pytest.mark.parametrize("opener_type", ["toolbar", "sidebar"])
def test_opener_button_reflects_open_and_current_state(root, opener_type):
    m = TabManager(root, configs("a", "b"), opener_type=opener_type)
    btn = m.opener.buttons
    m.open_tab("a")
    m.open_tab("b")
    root.update()
    # open -> 'alternate'; selected (current) -> 'selected'
    assert "alternate" in btn["a"].state() and "alternate" in btn["b"].state()
    assert "selected" in btn["b"].state() and "selected" not in btn["a"].state()

    m.select_tab("a")
    root.update()
    assert "selected" in btn["a"].state() and "selected" not in btn["b"].state()

    # Survives an opener rebuild
    m.add_tab_config(TabConfig("c", "C", SimpleContent))
    btn = m.opener.buttons
    assert "alternate" in btn["a"].state() and "selected" in btn["a"].state()
    assert "alternate" not in btn["c"].state()

    m.close_tab("a")
    root.update()
    assert "alternate" not in btn["a"].state() and "selected" not in btn["a"].state()


def test_icon_kind_independent_of_cwd(tmp_path, monkeypatch):
    (tmp_path / "Hm").write_text("not an image")
    monkeypatch.chdir(tmp_path)
    assert IconManager.is_text_icon("Hm")


def test_icon_cache_prunes_destroyed_interpreters(icon_file):
    IconManager.clear_cache()
    for _ in range(3):
        r = tk.Tk()
        r.withdraw()
        IconManager.get_icon(icon_file, (16, 16), master=r)
        r.destroy()
    r = tk.Tk()
    r.withdraw()
    try:
        IconManager.get_icon(icon_file, (16, 16), master=r)
        assert len(IconManager._cache) == 1
    finally:
        r.destroy()
        IconManager.clear_cache()


# --- Shortcut routing between managers sharing a window -----------------------


def press(managers, sequence):
    """Simulate a window-level shortcut: run every manager's handler for it."""
    for m in managers:
        for binding in m._shortcuts.bindings(sequence):
            binding.callback()


def two_managers(root):
    left, right = ttk.Frame(root), ttk.Frame(root)
    left.pack(side="left")
    right.pack(side="right")
    m1 = TabManager(left, configs("a", "b"))
    m2 = TabManager(right, configs("a", "b"))
    for m in (m1, m2):
        m.open_tab("a")
        m.open_tab("b")
    return m1, m2


def test_shortcut_handled_only_by_most_recently_used_manager(root):
    m1, m2 = two_managers(root)  # m2 used last
    press([m1, m2], "<Control-w>")
    assert m1.get_open_tabs() == ["a", "b"]
    assert m2.get_open_tabs() == ["a"]

    m1.select_tab("a")  # m1 becomes the most recently used
    press([m1, m2], "<Control-w>")
    assert m1.get_open_tabs() == ["b"]
    assert m2.get_open_tabs() == ["a"]


def test_shortcut_follows_keyboard_focus(root, monkeypatch):
    m1, m2 = two_managers(root)  # m2 used last
    focused = m1.get_tab_content("b").frame
    monkeypatch.setattr(m1, "focus_get", lambda: focused)
    monkeypatch.setattr(m2, "focus_get", lambda: focused)
    press([m1, m2], "<Control-w>")
    assert m1.get_open_tabs() == ["a"]
    assert m2.get_open_tabs() == ["a", "b"]


def test_per_tab_shortcut_is_scoped(root):
    m1 = TabManager(root, configs("a", keyboard_shortcut="<F5>"))
    m2 = TabManager(root, configs("a", keyboard_shortcut="<F5>"))
    m2.select_tab("a")
    m2.close_tab("a")
    press([m1, m2], "<F5>")
    assert not m1.is_tab_open("a")
    assert m2.is_tab_open("a")


def test_active_role_passes_on_when_manager_destroyed(root):
    m1, m2 = two_managers(root)  # m2 active
    m2.destroy()
    press([m1], "<Control-w>")
    assert m1.get_open_tabs() == ["a"]


def test_manager_without_shortcuts_does_not_take_focus_role(root):
    m1 = TabManager(root, configs("a", "b"))
    m2 = TabManager(root, configs("a"), enable_keyboard_shortcuts=False)
    m1.open_tab("a")
    m1.open_tab("b")
    m2.open_tab("a")  # used last, but has no shortcuts
    press([m1, m2], "<Control-w>")
    assert m1.get_open_tabs() == ["a"]


# --- Error reporting / cleanup-phase behaviour ---------------------------------


def test_tab_error_without_handler_is_logged(root, caplog):
    m = TabManager(root, configs("a"))
    m.on_tab_opened = lambda tab_id: 1 / 0
    with caplog.at_level("ERROR", logger="flextabs"):
        m.open_tab("a")
    assert any(
        r.exc_info and r.exc_info[0] is ZeroDivisionError for r in caplog.records
    )
    assert isinstance(m.tab_states["a"]["last_error"], ZeroDivisionError)


def test_failing_error_handler_is_logged_not_swallowed(root, caplog):
    m = TabManager(root, configs("a"))
    m.on_tab_opened = lambda tab_id: 1 / 0
    m.on_tab_error = lambda tab_id, e: [][0]
    with caplog.at_level("ERROR", logger="flextabs"):
        assert m.open_tab("a") is True
    assert any(r.exc_info and r.exc_info[0] is IndexError for r in caplog.records)


def test_content_cleanup_error_is_logged(root, caplog):
    class BadCleanup(SimpleContent):
        def cleanup(self):
            super().cleanup()
            raise RuntimeError("boom")

    m = TabManager(root, [TabConfig("a", "A", BadCleanup)])
    m.open_tab("a")
    with caplog.at_level("ERROR", logger="flextabs"):
        assert m.close_tab("a") is True
    assert "Error cleaning up content of tab 'a'" in caplog.text


def test_refresh_tab_icons_rebuilds_opener_when_refresh_fails(root, monkeypatch):
    m = TabManager(root, configs("a", "b"), opener_type="toolbar")
    m.open_tab("a")
    old_opener = m.opener

    def broken(_configs):
        raise RuntimeError("refresh broke")

    monkeypatch.setattr(old_opener, "refresh_opener", broken)
    m.refresh_tab_icons()
    assert m.opener is not old_opener
    assert not old_opener.container.winfo_exists()  # old one cleaned up
    assert "selected" in m.opener.buttons["a"].state()


def test_tab_id_at_position(root):
    root.deiconify()
    m = TabManager(root, configs("a", "b"))
    m.pack()
    m.open_tab("a")
    m.open_tab("b")
    root.update()
    x, y = 5, 5
    assert m._get_tab_id_at_position(x, y) == "a"
    assert m._get_tab_id_at_position(5000, 5000) is None


def test_flextabs_styles_created_in_every_root():
    for _ in range(2):
        r = tk.Tk()
        r.withdraw()
        try:
            m = TabManager(r, configs("a"), opener_type="toolbar", theme="light")
            style = m.opener.buttons["a"].cget("style")
            assert style == m.theme.toolbar_button
            assert ttk.Style(r).lookup(style, "background") == m.theme.palette.bg
        finally:
            r.destroy()


def test_unclosable_tabs_have_no_visual_noise(root):
    m = TabManager(root, configs("a", closable=False), opener_type="sidebar")
    m.open_tab("a")
    assert tab_text(m, "a") == "A"
    assert m.opener.buttons["a"].cget("text") == "A"
    assert m.opener.buttons["a"].cget("style") == m.theme.nav_button
