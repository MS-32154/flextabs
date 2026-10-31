import contextlib
import tkinter as tk
from collections import deque
from typing import ClassVar

from .icons import IconManager
from .theme import LIGHT, palette_for


class TooltipWidget:
    """A tooltip that can be attached to any tkinter widget."""

    def __init__(
        self,
        widget: tk.Misc,
        text: str,
        delay: int = 500,
        wraplength: int = 280,
        font: tuple | str | None = None,
    ):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self.font = font or "TkDefaultFont"
        self.tooltip = None
        self.after_id = None

        # Add to (not replace) any existing bindings
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<Motion>", self._on_motion, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, event):
        self._cancel_tooltip()
        self.after_id = self.widget.after(self.delay, self._show_tooltip)

    def _on_leave(self, event):
        self._hide_tooltip()

    def _on_motion(self, event):
        if self.tooltip:
            self._position_tooltip(event)

    def _show_tooltip(self):
        self.after_id = None
        if self.tooltip:
            return

        palette = palette_for(self.widget)
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        self.tooltip = tk.Toplevel(self.widget, background=palette.tooltip_bg)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        with contextlib.suppress(tk.TclError):
            self.tooltip.attributes("-topmost", True)

        tk.Label(
            self.tooltip,
            text=self.text,
            background=palette.tooltip_bg,
            foreground=palette.tooltip_fg,
            borderwidth=0,
            font=self.font,
            padx=8,
            pady=4,
            wraplength=self.wraplength,
            justify=tk.LEFT,
        ).pack()

    def _hide_tooltip(self):
        self._cancel_tooltip()
        if self.tooltip:
            with contextlib.suppress(tk.TclError):
                self.tooltip.destroy()
            self.tooltip = None

    def _cancel_tooltip(self):
        if self.after_id:
            with contextlib.suppress(tk.TclError):
                self.widget.after_cancel(self.after_id)
            self.after_id = None

    def _position_tooltip(self, event):
        if not self.tooltip:
            return

        self.tooltip.update_idletasks()
        tooltip_width = self.tooltip.winfo_reqwidth()
        tooltip_height = self.tooltip.winfo_reqheight()

        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()

        x = event.x_root + 12
        y = event.y_root + 16

        if x + tooltip_width > screen_width:
            x = event.x_root - tooltip_width - 12
        if y + tooltip_height > screen_height:
            y = event.y_root - tooltip_height - 12

        x = max(0, min(x, screen_width - tooltip_width))
        y = max(0, min(y, screen_height - tooltip_height))

        self.tooltip.wm_geometry(f"+{x}+{y}")

    def update_text(self, new_text: str):
        self.text = new_text
        if self.tooltip:
            for child in self.tooltip.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(text=new_text)
                    break


class ToastNotification:
    """Toast notifications (cards with a status icon), stacked or queued."""

    # Status accent colours of the light palette, for reference only: toasts
    # take their colours from the window's palette (see theme.palette_for).
    COLORS: ClassVar[dict[str, dict[str, str]]] = {
        kind: {"accent": getattr(LIGHT, kind)}
        for kind in ("info", "warning", "error", "success")
    }
    ICONS: ClassVar[dict[str, str]] = {
        "info": "info",
        "success": "check-circle",
        "warning": "alert",
        "error": "x-circle",
    }
    WIDTH: ClassVar[int] = 320
    MARGIN: ClassVar[int] = 16
    GAP: ClassVar[int] = 8

    _queue: ClassVar[deque] = deque()
    _active_toasts: ClassVar[list[tk.Toplevel]] = []
    _is_showing: ClassVar[bool] = False

    @staticmethod
    def show(
        parent: tk.Misc,
        message: str,
        duration: int = 2000,
        toast_type: str = "info",
        position: str = "top-right",
        mode: str = "stacked",
    ):
        ToastNotification._queue.append(
            (parent, message, duration, toast_type, position, mode)
        )
        if mode == "queued":
            if not ToastNotification._is_showing:
                ToastNotification._show_next_queued()
        else:
            ToastNotification._show_toast(*ToastNotification._queue.popleft())

    @staticmethod
    def _show_next_queued():
        if not ToastNotification._queue:
            ToastNotification._is_showing = False
            return

        ToastNotification._is_showing = True
        ToastNotification._show_toast(
            *ToastNotification._queue.popleft(),
            on_close=ToastNotification._show_next_queued,
        )

    @staticmethod
    def _stack_offset() -> int:
        """Vertical space taken by visible toasts (forgetting destroyed ones)."""
        offset = 0
        alive = []
        for toast in ToastNotification._active_toasts:
            try:
                if not toast.winfo_exists():
                    continue
                offset += toast.winfo_reqheight() + ToastNotification.GAP
            except tk.TclError:
                continue  # its application was destroyed
            alive.append(toast)
        ToastNotification._active_toasts[:] = alive
        return offset

    @staticmethod
    def _show_toast(
        parent: tk.Misc,
        message: str,
        duration: int,
        toast_type: str,
        position: str,
        mode: str,
        on_close=None,
    ):
        root = parent.winfo_toplevel()
        palette = palette_for(parent)
        width = ToastNotification.WIDTH

        toast = tk.Toplevel(root, background=palette.border)
        toast.wm_overrideredirect(True)
        with contextlib.suppress(tk.TclError):
            toast.attributes("-topmost", True)

        card = tk.Frame(toast, background=palette.surface, padx=12, pady=10)
        card.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        widgets: list[tk.Misc] = [toast, card]
        icon = IconManager.get_builtin_icon(
            ToastNotification.ICONS.get(toast_type, "info"),
            18,
            palette.status_color(toast_type),
            toast,
        )
        if icon is not None:
            icon_label = tk.Label(
                card, image=icon, background=palette.surface, borderwidth=0
            )
            icon_label.image = icon
            icon_label.pack(side=tk.LEFT, anchor="n", padx=(0, 10))
            widgets.append(icon_label)

        label = tk.Label(
            card,
            text=message,
            background=palette.surface,
            foreground=palette.text,
            font="TkDefaultFont",
            wraplength=width - 70,
            justify=tk.LEFT,
            anchor="w",
        )
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        widgets.append(label)

        # Size to content, then position inside the parent window
        toast.update_idletasks()
        height = toast.winfo_reqheight()
        root.update_idletasks()
        win_x, win_y = root.winfo_rootx(), root.winfo_rooty()
        win_w, win_h = root.winfo_width(), root.winfo_height()
        margin = ToastNotification.MARGIN
        stack = ToastNotification._stack_offset() if mode == "stacked" else 0

        right = win_x + win_w - width - margin
        left = win_x + margin
        top = win_y + margin + stack
        bottom = win_y + win_h - height - margin - stack
        x, y = {
            "top-left": (left, top),
            "bottom-left": (left, bottom),
            "bottom-right": (right, bottom),
        }.get(position, (right, top))
        toast.wm_geometry(f"{width}x{height}+{x}+{y}")

        ToastNotification._active_toasts.append(toast)
        dismissed = False

        def dismiss(event=None):
            nonlocal dismissed
            if dismissed:
                return
            dismissed = True
            if toast in ToastNotification._active_toasts:
                ToastNotification._active_toasts.remove(toast)
            with contextlib.suppress(tk.TclError):
                toast.destroy()
            if on_close:
                on_close()

        for widget in widgets:
            widget.bind("<Button-1>", dismiss)

        toast.after(duration, dismiss)
