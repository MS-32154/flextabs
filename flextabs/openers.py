from tkinter import *
from tkinter import ttk

from .enums import TabPosition
from .tab_base import TabOpener, TabConfig


class ButtonOpener(TabOpener):
    """Base class for tab openers that use buttons."""

    def setup_common_container(self, position, layout, width=None):
        side_map = {
            TabPosition.TOP: TOP,
            TabPosition.BOTTOM: BOTTOM,
            TabPosition.LEFT: LEFT,
            TabPosition.RIGHT: RIGHT,
        }
        side = side_map[position]
        fill = X if layout == "horizontal" else Y

        frame_kwargs = self.config.get("style", {})

        if width:
            self.container = ttk.Frame(self.parent, width=width, **frame_kwargs)
            self.container.pack(side=side, fill=Y)
            self.container.pack_propagate(False)
        else:
            self.container = ttk.Frame(self.parent, **frame_kwargs)
            self.container.pack(side=side, fill=fill)

        self._widgets["container"] = self.container
        self.buttons_frame = ttk.Frame(self.container)
        self.buttons_frame.pack(fill=BOTH, expand=True)
        self._widgets["buttons_frame"] = self.buttons_frame

    def _create_buttons(self, tab_configs: list[TabConfig], layout: str):
        self.buttons = {}
        self.button_frames = {}

        for tab_config in tab_configs:
            # Optional frame per button
            btn_parent = self.buttons_frame
            if self.use_button_frame():
                btn_frame = ttk.Frame(self.buttons_frame)
                btn_frame.pack(side=TOP, fill=X, padx=5, pady=2)
                self.button_frames[tab_config.id] = btn_frame
                self._widgets[f"frame_{tab_config.id}"] = btn_frame
                btn_parent = btn_frame

            btn = self._create_button(btn_parent, tab_config)
            self.pack_button(btn, layout)

            self.buttons[tab_config.id] = btn
            self._widgets[f"btn_{tab_config.id}"] = btn

    def _smart_refresh(self, tab_configs: list[TabConfig]) -> bool:
        if not hasattr(self, "buttons_frame") or not self.buttons_frame.winfo_exists():
            return False

        try:
            # Destroy existing buttons and frames
            for tab_id in list(self.buttons.keys()):
                if tab_id in self.button_frames:
                    frame = self.button_frames[tab_id]
                    if frame and frame.winfo_exists():
                        frame.destroy()
                    del self.button_frames[tab_id]
                    del self._widgets[f"frame_{tab_id}"]

                btn = self.buttons[tab_id]
                if btn and btn.winfo_exists():
                    btn.destroy()
                del self._widgets[f"btn_{tab_id}"]
                del self.buttons[tab_id]

            self._icons.clear()
            layout = self.config.get("layout", "horizontal")
            self._create_buttons(tab_configs, layout)
            return True
        except Exception:
            return False

    def update_tab_state(self, tab_id: str, is_open: bool):
        if hasattr(self, "buttons") and tab_id in self.buttons:
            try:
                state = "pressed" if is_open else "normal"
                self.buttons[tab_id].configure(state=state)
            except:
                pass

    def use_button_frame(self):
        return False

    def pack_button(self, btn, layout):
        if layout == "horizontal":
            btn.pack(side=LEFT, padx=2, pady=2)
        else:
            btn.pack(side=TOP, fill=X, padx=2, pady=2)


class ToolbarOpener(ButtonOpener):
    """Toolbar-based tab opener with smart refresh."""

    def setup_opener(self, tab_configs: list[TabConfig]):
        position = TabPosition(self.config.get("position", "top"))
        layout = self.config.get("layout", "horizontal")

        self.setup_common_container(position, layout)
        self._create_buttons(tab_configs, layout)
        self.toolbar = self.container  # For backward compatibility
        self._widgets["toolbar"] = self.toolbar


class SidebarOpener(ButtonOpener):
    """Sidebar-based tab opener with smart refresh."""

    def setup_opener(self, tab_configs: list[TabConfig]):
        position = TabPosition(self.config.get("position", "left"))
        width = self.config.get("width", 150)

        self.setup_common_container(position, layout="vertical", width=width)
        self._setup_title()
        self._create_buttons(tab_configs, layout="vertical")
        self.sidebar = self.container  # For backward compatibility
        self._widgets["sidebar"] = self.sidebar

    def use_button_frame(self):
        return True

    def _setup_title(self):
        title = self.config.get("title")
        if title:
            title_label = ttk.Label(
                self.container, text=title, font=("TkDefaultFont", 10, "bold")
            )
            title_label.pack(side=TOP, pady=(5, 10))
            self._widgets["title"] = title_label

    def pack_button(self, btn, layout):
        btn.pack(fill=X)


class MenuOpener(TabOpener):
    """Menu-based tab opener with smart refresh."""

    def setup_opener(self, tab_configs: list[TabConfig]):
        root = self._get_root_window()
        if not root:
            raise ValueError("MenuOpener requires a Toplevel or Tk parent")

        if not hasattr(root, "menubar") or not root.menubar:
            root.menubar = Menu(root)
            root.config(menu=root.menubar)

        menu_title = self.config.get("menu_title", "Tabs")
        self.tabs_menu = Menu(root.menubar, tearoff=0)
        root.menubar.add_cascade(label=menu_title, menu=self.tabs_menu)
        self._widgets["menu"] = self.tabs_menu

        self._create_menu_items(tab_configs)

    def _create_menu_items(self, tab_configs: list[TabConfig]):
        for tab_config in tab_configs:
            label = tab_config.title
            if not tab_config.closable:
                label = f"\u2022 {label}"

            if self.show_icons and tab_config.icon and len(tab_config.icon) <= 4:
                label = f"{tab_config.icon} {label}"

            self.tabs_menu.add_command(
                label=label, command=lambda tid=tab_config.id: self._open_tab_safe(tid)
            )

    def _smart_refresh(self, tab_configs: list[TabConfig]) -> bool:
        if not hasattr(self, "tabs_menu"):
            return False

        try:
            self.tabs_menu.delete(0, "end")
            self._icons.clear()
            self._create_menu_items(tab_configs)
            return True
        except Exception:
            return False

    def refresh_opener(self, tab_configs: list[TabConfig]):
        self._smart_refresh(tab_configs)

    def _get_root_window(self) -> Tk | Toplevel | None:
        parent = self.parent
        while parent:
            if isinstance(parent, (Tk, Toplevel)):
                return parent
            parent = parent.master
        return None
