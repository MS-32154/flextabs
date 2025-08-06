from tkinter import *
from collections import deque


class TooltipWidget:
    """A tooltip widget that can be attached to any tkinter widget."""

    def __init__(
        self,
        widget: Widget,
        text: str,
        delay: int = 500,
        wraplength: int = 250,
        font: tuple = ("TkDefaultFont", 8, "normal"),
    ):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self.font = font
        self.tooltip = None
        self.after_id = None

        # Bind events
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        widget.bind("<Motion>", self._on_motion)

    def _on_enter(self, event):
        self._cancel_tooltip()
        self.after_id = self.widget.after(self.delay, self._show_tooltip)

    def _on_leave(self, event):
        self._hide_tooltip()

    def _on_motion(self, event):
        if self.tooltip:
            self._position_tooltip(event)

    def _show_tooltip(self):
        if self.tooltip:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip = Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        self.tooltip.attributes("-topmost", True)

        Label(
            self.tooltip,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=self.font,
            padx=4,
            pady=2,
            wraplength=self.wraplength,
            justify=LEFT,
        ).pack()

    def _hide_tooltip(self):
        self._cancel_tooltip()
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def _cancel_tooltip(self):
        if self.after_id:
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

        x = event.x_root + 10
        y = event.y_root + 10

        if x + tooltip_width > screen_width:
            x = event.x_root - tooltip_width - 10
        if y + tooltip_height > screen_height:
            y = event.y_root - tooltip_height - 10

        x = max(0, min(x, screen_width - tooltip_width))
        y = max(0, min(y, screen_height - tooltip_height))

        self.tooltip.wm_geometry(f"+{x}+{y}")

    def update_text(self, new_text: str):
        self.text = new_text
        if self.tooltip:
            for child in self.tooltip.winfo_children():
                if isinstance(child, Label):
                    child.config(text=new_text)
                    break


class ToastNotification:
    """A toast notification system supporting queued and stacked modes."""

    COLORS = {
        "info": {"bg": "#d1ecf1", "fg": "#0c5460", "border": "#bee5eb"},
        "warning": {"bg": "#fff3cd", "fg": "#856404", "border": "#ffeaa7"},
        "error": {"bg": "#f8d7da", "fg": "#721c24", "border": "#f5c6cb"},
        "success": {"bg": "#d4edda", "fg": "#155724", "border": "#c3e6cb"},
    }

    _queue = deque()
    _active_toasts = []
    _is_showing = False

    @staticmethod
    def show(
        parent: Widget,
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
    def _show_toast(
        parent: Widget,
        message: str,
        duration: int,
        toast_type: str,
        position: str,
        mode: str,
        on_close=None,
    ):
        root = parent
        while root.master:
            root = root.master

        root.update_idletasks()

        toast_width, toast_height = 280, 60
        screen_x = root.winfo_x()
        screen_y = root.winfo_y()
        screen_width = root.winfo_width()
        screen_height = root.winfo_height()

        x_offset = 20
        y_offset = (
            20 + (len(ToastNotification._active_toasts) * (toast_height + 10))
            if mode == "stacked"
            else 20
        )

        if position == "top-right":
            x = screen_x + screen_width - toast_width - x_offset
            y = screen_y + y_offset
        elif position == "bottom-right":
            x = screen_x + screen_width - toast_width - x_offset
            y = screen_y + screen_height - toast_height - y_offset
        elif position == "top-left":
            x = screen_x + x_offset
            y = screen_y + y_offset
        elif position == "bottom-left":
            x = screen_x + x_offset
            y = screen_y + screen_height - toast_height - y_offset
        else:
            x = screen_x + screen_width - toast_width - x_offset
            y = screen_y + y_offset

        toast = Toplevel(root)
        toast.wm_overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.wm_geometry(f"{toast_width}x{toast_height}+{x}+{y}")

        ToastNotification._active_toasts.append(toast)

        color_scheme = ToastNotification.COLORS.get(
            toast_type, ToastNotification.COLORS["info"]
        )

        frame = Frame(toast, bg=color_scheme["border"], padx=2, pady=2)
        frame.pack(fill=BOTH, expand=True)

        inner_frame = Frame(frame, bg=color_scheme["bg"])
        inner_frame.pack(fill=BOTH, expand=True)

        label = Label(
            inner_frame,
            text=message,
            bg=color_scheme["bg"],
            fg=color_scheme["fg"],
            font=("TkDefaultFont", 9),
            wraplength=260,
            justify=LEFT,
        )
        label.pack(expand=True, padx=10, pady=10)

        def dismiss(event=None):
            if toast in ToastNotification._active_toasts:
                ToastNotification._active_toasts.remove(toast)
            toast.destroy()
            if on_close:
                on_close()

        for widget in [toast, frame, inner_frame, label]:
            widget.bind("<Button-1>", dismiss)

        toast.after(duration, dismiss)
