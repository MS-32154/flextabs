from tkinter import *


class TooltipWidget:
    """A tooltip widget that can be attached to any tkinter widget."""

    def __init__(self, widget: Widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip = None
        self.after_id = None

        # Bind events
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        widget.bind("<Motion>", self._on_motion)

    def _on_enter(self, event):
        """Schedule tooltip to show."""
        self._cancel_tooltip()
        self.after_id = self.widget.after(self.delay, self._show_tooltip)

    def _on_leave(self, event):
        """Hide tooltip when leaving widget."""
        self._hide_tooltip()

    def _on_motion(self, event):
        """Update tooltip position on mouse motion."""
        if self.tooltip:
            self._position_tooltip(event)

    def _show_tooltip(self):
        """Show the tooltip."""
        if self.tooltip:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip = Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        self.tooltip.attributes("-topmost", True)

        # Create tooltip content in one go
        Label(
            self.tooltip,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("TkDefaultFont", 8, "normal"),
            padx=4,
            pady=2,
        ).pack()

    def _hide_tooltip(self):
        """Hide the tooltip."""
        self._cancel_tooltip()
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def _cancel_tooltip(self):
        """Cancel scheduled tooltip."""
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

    def _position_tooltip(self, event):
        """Position tooltip relative to mouse with screen boundary checks."""
        if not self.tooltip:
            return

        # Get screen dimensions
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()

        # Update tooltip to get accurate dimensions
        self.tooltip.update_idletasks()
        tooltip_width = self.tooltip.winfo_reqwidth()
        tooltip_height = self.tooltip.winfo_reqheight()

        # Calculate preferred position
        x = event.x_root + 10
        y = event.y_root + 10

        # Adjust if tooltip would go off-screen horizontally
        if x + tooltip_width > screen_width:
            x = event.x_root - tooltip_width - 10

        # Adjust if tooltip would go off-screen vertically
        if y + tooltip_height > screen_height:
            y = event.y_root - tooltip_height - 10

        # Ensure tooltip stays on screen (fallback)
        x = max(0, min(x, screen_width - tooltip_width))
        y = max(0, min(y, screen_height - tooltip_height))

        self.tooltip.wm_geometry(f"+{x}+{y}")

    def update_text(self, new_text: str):
        """Update tooltip text."""
        self.text = new_text
        if self.tooltip:
            for child in self.tooltip.winfo_children():
                if isinstance(child, Label):
                    child.config(text=new_text)
                    break


class ToastNotification:
    """A simple toast notification system with fixed rendering."""

    COLORS = {
        "info": {"bg": "#d1ecf1", "fg": "#0c5460", "border": "#bee5eb"},
        "warning": {"bg": "#fff3cd", "fg": "#856404", "border": "#ffeaa7"},
        "error": {"bg": "#f8d7da", "fg": "#721c24", "border": "#f5c6cb"},
        "success": {"bg": "#d4edda", "fg": "#155724", "border": "#c3e6cb"},
    }

    @staticmethod
    def show(
        parent: Widget, message: str, duration: int = 2000, toast_type: str = "info"
    ):
        """Show a toast notification with proper positioning."""
        # Find the root window
        root = parent
        while root.master:
            root = root.master

        # Force geometry update to get accurate positioning
        root.update_idletasks()

        # Calculate position first
        x = root.winfo_x() + root.winfo_width() - 300
        y = root.winfo_y() + 50

        # Create toast window with all content at once to prevent flicker
        toast = Toplevel(root)
        toast.wm_overrideredirect(True)
        toast.attributes("-topmost", True)

        # Set geometry before creating content
        toast.wm_geometry(f"280x60+{x}+{y}")

        # Get color scheme
        color_scheme = ToastNotification.COLORS.get(
            toast_type, ToastNotification.COLORS["info"]
        )

        # Create all content in one operation
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

        # Set up click-to-dismiss for all components
        def dismiss(event):
            toast.destroy()

        for widget in [toast, frame, inner_frame, label]:
            widget.bind("<Button-1>", dismiss)

        # Auto-hide after duration
        toast.after(duration, toast.destroy)
