"""FlexTabs demo application (run with ``python -m flextabs``)."""

import random
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from .dpi import enable_dpi_awareness
from .enums import CloseConfirmationType, CloseMode
from .icons import IconManager
from .tab_base import TabConfig, TabContent
from .tab_manager import TabManager
from .theme import Theme, apply_app_theme, palette_for
from .widgets import ToastNotification

# --- shared helpers --------------------------------------------------------------


def _fonts(widget: tk.Misc) -> dict[str, tkfont.Font]:
    """Heading/subheading fonts derived from the default UI font."""
    base = tkfont.nametofont("TkDefaultFont", root=widget).actual()
    family, size = base["family"], base["size"]
    return {
        "title": tkfont.Font(root=widget, family=family, size=size + 7, weight="bold"),
        "section": tkfont.Font(
            root=widget, family=family, size=size + 1, weight="bold"
        ),
    }


def icon_button(parent, text, icon, command, style="TButton") -> ttk.Button:
    """A ttk button with a built-in icon tinted for the current palette."""
    palette = palette_for(parent)
    color = palette.on_accent if style == "Accent.TButton" else palette.text
    image = IconManager.get_builtin_icon(icon, 16, color, parent)
    button = ttk.Button(
        parent,
        text=text,
        command=command,
        style=style,
        image=image or "",
        compound="left",
    )
    button.image = image
    return button


class Page(TabContent):
    """Content page with a title, a muted subtitle and a padded body."""

    title = ""
    subtitle = ""

    def setup_content(self):
        fonts = _fonts(self.frame)
        self.section_font = fonts["section"]
        self.frame.configure(padding=(28, 24))
        ttk.Label(self.frame, text=self.page_title(), font=fonts["title"]).pack(
            anchor="w"
        )
        if self.subtitle:
            ttk.Label(self.frame, text=self.subtitle, style="Muted.TLabel").pack(
                anchor="w", pady=(4, 12)
            )
        self.build(self.frame)

    def page_title(self) -> str:
        return self.title

    def build(self, body: ttk.Frame):
        raise NotImplementedError

    def section(self, parent: tk.Misc, text: str) -> ttk.Frame:
        ttk.Label(parent, text=text, font=self.section_font).pack(
            anchor="w", pady=(16, 6)
        )
        frame = ttk.Frame(parent)
        frame.pack(fill="x", anchor="w")
        return frame


# --- pages -------------------------------------------------------------------------


class HomeTab(Page):
    title = "Welcome"
    subtitle = "A flexible tab manager for tkinter applications."

    def build(self, body):
        features = self.section(body, "What to try")
        for line in (
            "Switch between sidebar, toolbar and menu openers in the header",
            "Toggle light and dark mode with the button in the header",
            "Close tabs with their close button, Ctrl+W, or a right-click",
            "Move between tabs with Ctrl+Tab and Ctrl+1 to Ctrl+9",
        ):
            ttk.Label(features, text=f"–  {line}").pack(anchor="w", pady=1)

        notify = self.section(body, "Notifications")
        for kind in ("info", "success", "warning", "error"):
            icon_button(
                notify,
                kind.title(),
                ToastNotification.ICONS[kind],
                lambda k=kind: self.show_toast(k),
            ).pack(side="left", padx=(0, 6))

        tabs = self.section(body, "Tabs at runtime")
        icon_button(
            tabs, "Add tab", "plus", self.add_dynamic_tab, style="Accent.TButton"
        ).pack(side="left", padx=(0, 6))
        icon_button(tabs, "Remove tab", "trash", self.remove_dynamic_tab).pack(
            side="left", padx=(0, 6)
        )
        icon_button(tabs, "Queued toasts", "bell", self.toast_queue_demo).pack(
            side="left"
        )

    def show_toast(self, kind):
        messages = {
            "info": "Here is some information.",
            "success": "Operation completed successfully.",
            "warning": "This is a warning message.",
            "error": "Something went wrong while processing.",
        }
        self.get_manager().show_notification(messages[kind], kind)

    def add_dynamic_tab(self):
        manager = self.get_manager()
        tab_id = f"dynamic_{random.randint(1000, 9999)}"
        config = TabConfig(
            id=tab_id,
            title=f"Document {tab_id[-4:]}",
            content_class=DocumentTab,
            icon="file-text",
            tooltip="A tab created at runtime",
        )
        manager.add_tab_config(config)
        manager.open_tab(tab_id)

    def remove_dynamic_tab(self):
        manager = self.get_manager()
        dynamic = [t for t in manager.tab_configs if t.startswith("dynamic_")]
        if not dynamic:
            manager.show_notification("There are no added tabs to remove.", "warning")
            return
        tab_id = dynamic[-1]
        title = manager.tab_configs[tab_id].title
        manager.remove_tab_config(tab_id)
        manager.show_notification(f"Removed {title}.", "info")

    def toast_queue_demo(self):
        manager = self.get_manager()
        steps = [
            ("Starting export...", "info"),
            ("Large dataset, this may take a moment.", "warning"),
            ("Export finished.", "success"),
        ]
        for message, kind in steps:
            ToastNotification.show(manager, message, 1400, kind, mode="queued")


class SettingsTab(Page):
    title = "Settings"
    subtitle = "Change how tabs behave while the app is running."

    def build(self, body):
        manager = self.get_manager()
        close = self.section(body, "Closing tabs with the mouse")
        self.close_mode = tk.StringVar(value=manager.get_close_mode().value)
        for value, label in (
            ("active_only", "Only the selected tab"),
            ("any_visible", "Any tab"),
            ("both", "Selected tab, or any tab with Ctrl held"),
        ):
            ttk.Radiobutton(
                close,
                text=label,
                value=value,
                variable=self.close_mode,
                command=lambda: manager.set_close_mode(self.close_mode.get()),
            ).pack(anchor="w", pady=1)

        icons = self.section(body, "Icons")
        self.show_icons = tk.BooleanVar(value=manager.show_notebook_icons)
        ttk.Checkbutton(
            icons,
            text="Show icons on tabs",
            variable=self.show_icons,
            command=lambda: manager.set_notebook_icon_settings(
                show_icons=self.show_icons.get()
            ),
        ).pack(anchor="w")

        actions = self.section(body, "This tab")
        icon_button(
            actions, "Close settings", "close", lambda: manager.close_tab(self.tab_id)
        ).pack(side="left")


class DataTab(Page):
    title = "Data"
    subtitle = "Live information about this tab manager."

    def build(self, body):
        columns = ("Property", "Value")
        self.tree = ttk.Treeview(body, columns=columns, show="headings", height=6)
        for col, width in zip(columns, (180, 360), strict=True):
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="x", pady=(8, 12))
        icon_button(body, "Refresh", "refresh", self.refresh).pack(anchor="w")
        self.refresh()

    def on_tab_focus(self):
        self.refresh()

    def refresh(self):
        manager = self.get_manager()
        if manager is None:
            return
        self.tree.delete(*self.tree.get_children())
        rows = [
            ("Open tabs", ", ".join(manager.get_open_tabs()) or "none"),
            ("Selected tab", manager.get_current_tab() or "none"),
            ("Close mode", manager.get_close_mode().value),
            ("Updated", time.strftime("%H:%M:%S")),
        ]
        for row in rows:
            self.tree.insert("", "end", values=row)


class HelpTab(Page):
    title = "Help"
    subtitle = "Keyboard shortcuts and mouse controls."

    def build(self, body):
        rows = [
            ("Ctrl+1 … Ctrl+9", "Select a tab by position"),
            ("Ctrl+Tab / Ctrl+Shift+Tab", "Next / previous tab"),
            ("Ctrl+W", "Close the selected tab"),
            ("F1 – F4", "Open Help, Home, Settings and Data"),
            ("Close button / right-click", "Close a tab"),
        ]
        table = self.section(body, "Shortcuts")
        for i, (keys, action) in enumerate(rows):
            ttk.Label(table, text=keys, font=self.section_font).grid(
                row=i, column=0, sticky="w", padx=(0, 24), pady=3
            )
            ttk.Label(table, text=action).grid(row=i, column=1, sticky="w", pady=3)

    def on_tab_close(self):
        return messagebox.askyesno(
            "Close Help", "Close the help tab?", parent=self.frame
        )


class SystemTab(Page):
    title = "System"
    subtitle = "This tab cannot be closed."

    def build(self, body):
        ttk.Label(
            body,
            text=(
                "Tabs created with closable=False stay open. Trying to close one "
                "shows a short notice instead."
            ),
            wraplength=480,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))


class DocumentTab(Page):
    subtitle = "A tab added at runtime."

    def page_title(self) -> str:
        return self.config.title

    def build(self, body):
        text = tk.Text(body, height=10, wrap="word", padx=10, pady=10)
        text.insert("1.0", "You can type here. Close this tab with its close button.")
        text.pack(fill="both", expand=True, pady=(8, 0))


# --- application -------------------------------------------------------------------

TAB_CONFIGS = [
    TabConfig(
        "home",
        "Home",
        HomeTab,
        icon="home",
        keyboard_shortcut="<F2>",
        tooltip="Start here",
    ),
    TabConfig(
        "settings",
        "Settings",
        SettingsTab,
        icon="settings",
        keyboard_shortcut="<F3>",
        tooltip="Behaviour settings",
    ),
    TabConfig(
        "data",
        "Data",
        DataTab,
        icon="chart",
        keyboard_shortcut="<F4>",
        tooltip="Live manager state",
    ),
    TabConfig(
        "help",
        "Help",
        HelpTab,
        icon="help",
        keyboard_shortcut="<F1>",
        tooltip="Shortcuts and controls",
    ),
    TabConfig(
        "system",
        "System",
        SystemTab,
        icon="lock",
        closable=False,
        tooltip="Cannot be closed",
    ),
]

OPENER_CONFIGS = {
    "sidebar": {"position": "left", "width": 190, "title": "WORKSPACE"},
    "toolbar": {"position": "top", "layout": "horizontal"},
    "menu": {"menu_title": "Tabs"},
}


class DemoApp:
    """Header (opener switch + theme toggle) above a TabManager."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.mode = "light"
        self.palette = apply_app_theme(root, self.mode)
        self.opener = tk.StringVar(value="sidebar")
        self.manager: TabManager | None = None

        self.header = ttk.Frame(root)
        self.header.pack(fill="x")
        ttk.Frame(root, height=1, style="Divider.TFrame").pack(fill="x")
        self.body = ttk.Frame(root)
        self.body.pack(fill="both", expand=True)

        self._build_header()
        self._apply_chrome()
        self.build_manager()

    def _build_header(self):
        fonts = _fonts(self.root)
        inner = ttk.Frame(self.header, padding=(16, 10))
        inner.pack(fill="x")
        self.header_inner = inner

        ttk.Label(
            inner, text="FlexTabs", font=fonts["section"], style="Header.TLabel"
        ).pack(side="left")
        ttk.Label(inner, text="demo", style="Header.Muted.TLabel").pack(
            side="left", padx=(6, 0)
        )

        self.theme_button = ttk.Button(
            inner, command=self.toggle_theme, style="Header.Toolbutton", takefocus=False
        )
        self.theme_button.pack(side="right")

        switch = ttk.Frame(inner, style="Header.TFrame")
        switch.pack(side="right", padx=(0, 16))
        self.switch = switch
        for value in ("sidebar", "toolbar", "menu"):
            ttk.Radiobutton(
                switch,
                text=value.title(),
                value=value,
                variable=self.opener,
                style="Header.Toolbutton",
                command=self.build_manager,
                takefocus=False,
            ).pack(side="left", padx=1)

    def _apply_chrome(self):
        """Header colours and the theme toggle icon for the current palette."""
        p = self.palette
        Theme(p).ensure(self.root)
        style = ttk.Style(self.root)
        style.configure("Divider.TFrame", background=p.border)
        style.configure("Header.TFrame", background=p.bg)
        for frame in (self.header, self.header_inner, self.switch):
            frame.configure(style="Header.TFrame")
        style.configure("Header.TLabel", background=p.bg, foreground=p.text)
        style.configure("Header.Muted.TLabel", background=p.bg, foreground=p.text_muted)
        style.configure(
            "Header.Toolbutton",
            background=p.bg,
            foreground=p.text_muted,
            padding=(10, 4),
            relief="flat",
            borderwidth=1,
            lightcolor=p.bg,
            darkcolor=p.bg,
            bordercolor=p.bg,
        )
        style.map(
            "Header.Toolbutton",
            background=[("selected", p.surface), ("active", p.hover)],
            foreground=[("selected", p.text), ("active", p.text)],
            lightcolor=[("selected", p.surface), ("active", p.hover)],
            darkcolor=[("selected", p.surface), ("active", p.hover)],
            bordercolor=[("selected", p.border), ("active", p.hover)],
        )
        icon = IconManager.get_builtin_icon(
            "sun" if p.dark else "moon", 16, p.text, self.root
        )
        self.theme_button.configure(image=icon or "", text="" if icon else "Theme")
        self.theme_button.image = icon

    def toggle_theme(self):
        self.mode = "dark" if self.mode == "light" else "light"
        self.palette = apply_app_theme(self.root, self.mode)
        self._apply_chrome()
        self.build_manager()

    def build_manager(self):
        previous = self.manager.get_open_tabs() if self.manager else ["home"]
        current = self.manager.get_current_tab() if self.manager else "home"
        for widget in self.body.winfo_children():
            widget.destroy()

        opener = self.opener.get()
        manager = TabManager(
            self.body,
            tab_configs=TAB_CONFIGS,
            opener_type=opener,
            opener_config=OPENER_CONFIGS[opener],
            close_button_style="button",
            close_confirmation=False,
            close_confirmation_type=CloseConfirmationType.NONE,
            close_mode=CloseMode.ACTIVE_ONLY,
            theme=self.mode,
        )
        manager.pack(fill="both", expand=True)
        self.manager = manager

        for tab_id in previous:
            if tab_id in manager.tab_configs:
                manager.open_tab(tab_id)
        if current in manager.tab_configs:
            manager.select_tab(current)


def create_demo_app() -> tk.Tk:
    enable_dpi_awareness()  # sharp rendering on high-DPI Windows displays
    root = tk.Tk()
    root.title("FlexTabs")
    root.geometry("960x620")
    root.minsize(720, 460)
    root.app = DemoApp(root)
    return root


if __name__ == "__main__":
    create_demo_app().mainloop()
