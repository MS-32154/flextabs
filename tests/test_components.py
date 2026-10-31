"""Unit tests for extracted components: ShortcutRegistry and FocusScope."""

import tkinter as tk
from tkinter import ttk

import pytest

from flextabs.shortcuts import FocusScope, ShortcutRegistry


@pytest.fixture
def root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


def count(widget, sequence):
    return widget.bind(sequence).count('== "break"} break')


class TestShortcutRegistry:
    def test_bind_preserves_existing_bindings(self, root):
        root.bind("<F2>", lambda e: None)
        reg = ShortcutRegistry()
        reg.bind(root, "<F2>", lambda e: None)
        assert count(root, "<F2>") == 2
        reg.unbind_all()
        assert count(root, "<F2>") == 1
        assert len(reg) == 0

    def test_unbind_by_tag(self, root):
        reg = ShortcutRegistry()
        reg.bind(root, "<F3>", lambda e: None, tag="x")
        reg.bind(root, "<F4>", lambda e: None, tag="y")
        reg.unbind("x")
        assert count(root, "<F3>") == 0
        assert count(root, "<F4>") == 1
        assert [b.sequence for b in reg.bindings()] == ["<F4>"]

    def test_unbind_after_widget_destroyed(self):
        r = tk.Tk()
        reg = ShortcutRegistry()
        reg.bind(r, "<F6>", lambda e: None)
        r.destroy()
        reg.unbind_all()  # must not raise
        assert len(reg) == 0


class TestFocusScope:
    def test_first_scope_is_active(self, root):
        a = FocusScope(ttk.Frame(root))
        b = FocusScope(ttk.Frame(root))
        assert a.is_active() and not b.is_active()
        b.activate()
        assert b.is_active() and not a.is_active()
        a.close()
        b.close()

    def test_close_hands_over_active(self, root):
        a = FocusScope(ttk.Frame(root))
        b = FocusScope(ttk.Frame(root))
        a.close()
        assert b.is_active()
        b.close()
        assert FocusScope._active == {} or all(
            ref() is None for ref in FocusScope._active.values()
        )

    def test_focus_inside_overrides_active(self, root, monkeypatch):
        fa, fb = ttk.Frame(root), ttk.Frame(root)
        inner = ttk.Entry(fb)
        a, b = FocusScope(fa), FocusScope(fb)  # a active
        for w in (fa, fb):
            monkeypatch.setattr(w, "focus_get", lambda: inner)
        assert b.owns_event() and not a.owns_event()
        a.close()
        b.close()

    def test_scopes_in_different_windows_are_independent(self, root):
        top = tk.Toplevel(root)
        a = FocusScope(ttk.Frame(root))
        b = FocusScope(ttk.Frame(top))
        assert a.is_active() and b.is_active()
        a.close()
        b.close()
