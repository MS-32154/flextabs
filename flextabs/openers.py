from tkinter import *
from tkinter import ttk

from .enums import TabPosition
from .tab_base import TabOpener, TabConfig


class ToolbarOpener(TabOpener):
    """Toolbar-based tab opener."""

    def setup_opener(self, tab_configs: list[TabConfig]):
        position = TabPosition(self.config.get("position", "top"))
        layout = self.config.get("layout", "horizontal")

        # Create toolbar
        side_map = {
            TabPosition.TOP: TOP,
            TabPosition.BOTTOM: BOTTOM,
            TabPosition.LEFT: LEFT,
            TabPosition.RIGHT: RIGHT,
        }

        self.toolbar = ttk.Frame(self.parent, **self.config.get("style", {}))
        fill_direction = X if layout == "horizontal" else Y
        self.toolbar.pack(side=side_map[position], fill=fill_direction)
        self._widgets["toolbar"] = self.toolbar

        # Create buttons
        self.buttons = {}
        for tab_config in tab_configs:
            btn = self._create_button(self.toolbar, tab_config)

            # Pack button
            if layout == "horizontal":
                btn.pack(side=LEFT, padx=2, pady=2)
            else:
                btn.pack(side=TOP, fill=X, padx=2, pady=2)

            self.buttons[tab_config.id] = btn
            self._widgets[f"btn_{tab_config.id}"] = btn

    def update_tab_state(self, tab_id: str, is_open: bool):
        """Update button state based on tab open/close state."""
        if hasattr(self, "buttons") and tab_id in self.buttons:
            try:
                state = "pressed" if is_open else "normal"
                self.buttons[tab_id].configure(state=state)
            except:
                pass


class SidebarOpener(TabOpener):
    """Sidebar-based tab opener."""

    def setup_opener(self, tab_configs: list[TabConfig]):
        position = TabPosition(self.config.get("position", "left"))
        width = self.config.get("width", 150)

        side = LEFT if position == TabPosition.LEFT else RIGHT

        # Create sidebar
        self.sidebar = ttk.Frame(
            self.parent, width=width, **self.config.get("style", {})
        )
        self.sidebar.pack(side=side, fill=Y)
        self.sidebar.pack_propagate(False)
        self._widgets["sidebar"] = self.sidebar

        # Add title if specified
        title = self.config.get("title")
        if title:
            title_label = ttk.Label(
                self.sidebar, text=title, font=("TkDefaultFont", 10, "bold")
            )
            title_label.pack(side=TOP, pady=(5, 10))
            self._widgets["title"] = title_label

        # Create buttons
        self.buttons = {}
        for tab_config in tab_configs:
            btn_frame = ttk.Frame(self.sidebar)
            btn_frame.pack(side=TOP, fill=X, padx=5, pady=2)

            btn = self._create_button(btn_frame, tab_config)
            btn.pack(fill=X)

            self.buttons[tab_config.id] = btn
            self._widgets[f"btn_{tab_config.id}"] = btn
            self._widgets[f"frame_{tab_config.id}"] = btn_frame


class MenuOpener(TabOpener):
    """Menu-based tab opener."""

    def setup_opener(self, tab_configs: list[TabConfig]):
        root = self._get_root_window()
        if not root:
            raise ValueError("MenuOpener requires a Toplevel or Tk parent")

        # Create or get menu bar
        if not hasattr(root, "menubar") or not root.menubar:
            root.menubar = Menu(root)
            root.config(menu=root.menubar)

        # Create tabs menu
        menu_title = self.config.get("menu_title", "Tabs")
        self.tabs_menu = Menu(root.menubar, tearoff=0)
        root.menubar.add_cascade(label=menu_title, menu=self.tabs_menu)
        self._widgets["menu"] = self.tabs_menu

        # Add menu items
        for tab_config in tab_configs:
            label = tab_config.title
            if not tab_config.closable:
                label = f"• {label}"

            self.tabs_menu.add_command(
                label=label, command=lambda tid=tab_config.id: self._open_tab_safe(tid)
            )

    def refresh_opener(self, tab_configs: list[TabConfig]):
        """Refresh menu items."""
        if hasattr(self, "tabs_menu"):
            self.tabs_menu.delete(0, "end")
            for tab_config in tab_configs:
                label = (
                    f"• {tab_config.title}"
                    if not tab_config.closable
                    else tab_config.title
                )
                self.tabs_menu.add_command(
                    label=label,
                    command=lambda tid=tab_config.id: self._open_tab_safe(tid),
                )

    def _get_root_window(self) -> Tk | Toplevel | None:
        """Get the root window for menu attachment."""
        parent = self.parent
        while parent:
            if isinstance(parent, (Tk, Toplevel)):
                return parent
            parent = parent.master
        return None
