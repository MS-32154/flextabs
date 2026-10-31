"""Keyboard shortcut bookkeeping and routing between widgets sharing a window."""

import contextlib
import tkinter as tk
import weakref
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class _Binding:
    widget: tk.Misc
    sequence: str
    funcid: str
    callback: Callable
    tag: str | None


class ShortcutRegistry:
    """Adds key bindings without clobbering others and removes exactly those.

    Bindings are added with ``add="+"`` so existing application bindings on the
    same sequence are preserved, and removed by their function id so only the
    bindings created through this registry are affected.
    """

    def __init__(self):
        self._bindings: list[_Binding] = []

    def bind(
        self,
        widget: tk.Misc,
        sequence: str,
        callback: Callable,
        *,
        tag: str | None = None,
    ) -> str:
        """Bind ``callback`` to ``sequence`` on ``widget``; ``tag`` groups bindings."""
        funcid = widget.bind(sequence, callback, add="+")
        self._bindings.append(_Binding(widget, sequence, funcid, callback, tag))
        return funcid

    def unbind(self, tag: str | None):
        """Remove all bindings registered with ``tag``."""
        self._remove(lambda b: b.tag == tag)

    def unbind_all(self):
        """Remove every binding registered through this registry."""
        self._remove(lambda b: True)

    def bindings(self, sequence: str | None = None) -> list[_Binding]:
        """Registered bindings, optionally filtered by sequence."""
        return [b for b in self._bindings if sequence is None or b.sequence == sequence]

    def _remove(self, predicate: Callable[[_Binding], bool]):
        remaining = []
        for binding in self._bindings:
            if predicate(binding):
                # TclError: widget or interpreter already destroyed
                with contextlib.suppress(tk.TclError):
                    binding.widget.unbind(binding.sequence, binding.funcid)
            else:
                remaining.append(binding)
        self._bindings = remaining

    def __len__(self) -> int:
        return len(self._bindings)


def _is_within(widget: tk.Misc | None, ancestor: tk.Misc) -> bool:
    """True if ``widget`` is ``ancestor`` or one of its descendants."""
    if widget is None:
        return False
    path, root = str(widget), str(ancestor)
    return path == root or path.startswith(root + ".")


class FocusScope:
    """Decides which of several widgets in one toplevel handles window shortcuts.

    Shortcuts are bound on the toplevel, so every widget sharing it receives
    them. A scope claims an event when keyboard focus is inside its widget; if
    focus is inside none of the scopes in the window, the active scope (the
    most recently used one, initially the first created) claims it.
    """

    # toplevel path name per interpreter -> live scopes / last active scope
    _scopes: ClassVar[dict[tuple[int, str], weakref.WeakSet]] = {}
    _active: ClassVar[dict[tuple[int, str], weakref.ref]] = {}

    def __init__(self, widget: tk.Misc):
        self.widget = widget
        self._key = (id(widget.tk), str(widget.winfo_toplevel()))
        FocusScope._scopes.setdefault(self._key, weakref.WeakSet()).add(self)
        if self._active_scope() is None:
            self.activate()

    def _active_scope(self) -> FocusScope | None:
        ref = FocusScope._active.get(self._key)
        return ref() if ref is not None else None

    def activate(self):
        """Mark this scope as the most recently used one in its window."""
        FocusScope._active[self._key] = weakref.ref(self)

    def is_active(self) -> bool:
        return self._active_scope() is self

    def _focus_widget(self) -> tk.Misc | None:
        try:
            return self.widget.focus_get()
        except KeyError, tk.TclError:
            # focus_get() can fail for some Tk-internal widgets (e.g. popdowns)
            return None

    def owns_event(self) -> bool:
        """Should this scope handle a window-level shortcut right now?"""
        focus = self._focus_widget()
        if _is_within(focus, self.widget):
            return True
        peers = FocusScope._scopes.get(self._key, ())
        if any(_is_within(focus, peer.widget) for peer in peers if peer is not self):
            return False
        return self.is_active()

    def close(self):
        """Unregister this scope, handing "active" to a remaining peer if needed."""
        was_active = self.is_active()
        peers = FocusScope._scopes.get(self._key)
        if peers is not None:
            peers.discard(self)
            if not peers:
                del FocusScope._scopes[self._key]
        if was_active or self._active_scope() is None:
            FocusScope._active.pop(self._key, None)
            if peers:
                next(iter(peers)).activate()
