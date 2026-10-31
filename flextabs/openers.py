import contextlib
import logging
import tkinter as tk
from tkinter import ttk
from typing import ClassVar

from .enums import TabPosition
from .icons import IconManager
from .tab_base import TabConfig, TabOpener

logger = logging.getLogger(__name__)


class ButtonOpener(TabOpener):
    """Base class for tab openers that use buttons."""

    _SIDES: ClassVar[dict[TabPosition, str]] = {
        TabPosition.TOP: tk.TOP,
        TabPosition.BOTTOM: tk.BOTTOM,
        TabPosition.LEFT: tk.LEFT,
        TabPosition.RIGHT: tk.RIGHT,
    }

    def setup_common_container(self, position, layout, width=None):
        theme = self.theme
        side = self._SIDES[position]
        fill = tk.X if layout == "horizontal" else tk.Y

        frame_kwargs = dict(self.config.get("style", {}))
        if theme is not None:
            frame_kwargs.setdefault("style", theme.chrome_frame)

        if width:
            self.container = ttk.Frame(self.parent, width=width, **frame_kwargs)
            self.container.pack(side=side, fill=tk.Y)
            self.container.pack_propagate(False)
        else:
            self.container = ttk.Frame(self.parent, **frame_kwargs)
            self.container.pack(side=side, fill=fill)
        self._widgets["container"] = self.container

        if theme is not None:
            # Hairline between the opener and the notebook
            vertical = side in (tk.LEFT, tk.RIGHT)
            divider = ttk.Frame(
                self.parent,
                style=theme.divider,
                **({"width": 1} if vertical else {"height": 1}),
            )
            divider.pack(side=side, fill=tk.Y if vertical else tk.X)
            self._widgets["divider"] = divider

        inner = {"style": theme.chrome_frame} if theme is not None else {}
        self.buttons_frame = ttk.Frame(self.container, **inner)
        if theme is not None:
            self.buttons_frame.configure(
                padding=(6, 0) if layout == "horizontal" else (8, 4, 8, 8)
            )
        self.buttons_frame.pack(fill=tk.BOTH, expand=True)
        self._widgets["buttons_frame"] = self.buttons_frame

    def _create_buttons(self, tab_configs: list[TabConfig], layout: str):
        self.buttons = {}
        self.button_frames = {}
        self._layout = layout

        for tab_config in tab_configs:
            # Optional frame per button (plain ttk look only)
            btn_parent = self.buttons_frame
            if self.use_button_frame() and self.theme is None:
                btn_frame = ttk.Frame(self.buttons_frame)
                btn_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
                self.button_frames[tab_config.id] = btn_frame
                self._widgets[f"frame_{tab_config.id}"] = btn_frame
                btn_parent = btn_frame

            btn = self._create_button(btn_parent, tab_config)
            self.pack_button(btn, layout)

            self.buttons[tab_config.id] = btn
            self._widgets[f"btn_{tab_config.id}"] = btn

        self._sync_states()

    def _sync_states(self):
        """Re-apply open/current indication (e.g. after a rebuild)."""
        manager = self.tab_manager
        if manager is None:
            return
        for tab_id in self.buttons:
            self.update_tab_state(tab_id, manager.is_tab_open(tab_id))
        self.update_current_tab(manager.get_current_tab())

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
            layout = getattr(self, "_layout", self.config.get("layout", "horizontal"))
            self._create_buttons(tab_configs, layout)
            return True
        except Exception:
            logger.exception("Opener refresh failed; falling back to full rebuild")
            return False

    def _set_button_state(self, tab_id: str, state: str, on: bool):
        btn = getattr(self, "buttons", {}).get(tab_id)
        if btn is None:
            return
        with contextlib.suppress(tk.TclError):
            btn.state([state if on else f"!{state}"])

    def update_tab_state(self, tab_id: str, is_open: bool):
        """Open tabs carry the ttk 'alternate' state ('selected' when unthemed).

        Stock ttk themes draw 'alternate' as a default-button ring, so the plain
        look keeps marking open tabs with 'selected' instead.
        """
        state = "alternate" if self.theme is not None else "selected"
        self._set_button_state(tab_id, state, is_open)

    def update_current_tab(self, tab_id: str | None):
        """The selected tab carries the ttk 'selected' state (themed look only)."""
        if self.theme is None:
            return
        for other in getattr(self, "buttons", {}):
            self._set_button_state(other, "selected", other == tab_id)

    def _button_style(self) -> str | None:
        theme = self.theme
        if theme is None:
            return None
        horizontal = getattr(self, "_layout", "vertical") == "horizontal"
        return theme.toolbar_button if horizontal else theme.nav_button

    def use_button_frame(self):
        return False

    def pack_button(self, btn, layout):
        if self.theme is not None:
            if layout == "horizontal":
                btn.pack(side=tk.LEFT, padx=1)
            else:
                btn.pack(side=tk.TOP, fill=tk.X, pady=1)
        elif layout == "horizontal":
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        else:
            btn.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)


class ToolbarOpener(ButtonOpener):
    """Toolbar-based tab opener with smart refresh."""

    def setup_opener(self, tab_configs: list[TabConfig]):
        position = TabPosition(self.config.get("position", "top"))
        layout = self.config.get("layout", "horizontal")
        self._layout = layout

        self.setup_common_container(position, layout)
        self._create_buttons(tab_configs, layout)
        self.toolbar = self.container  # For backward compatibility
        self._widgets["toolbar"] = self.toolbar


class SidebarOpener(ButtonOpener):
    """Sidebar-based tab opener with smart refresh."""

    def setup_opener(self, tab_configs: list[TabConfig]):
        position = TabPosition(self.config.get("position", "left"))
        width = self.config.get("width", 180)
        self._layout = "vertical"

        self.setup_common_container(position, layout="vertical", width=width)
        self._setup_title()
        self._create_buttons(tab_configs, layout="vertical")
        self.sidebar = self.container  # For backward compatibility
        self._widgets["sidebar"] = self.sidebar

    def use_button_frame(self):
        return True

    def _setup_title(self):
        title = self.config.get("title")
        if not title:
            return
        theme = self.theme
        if theme is not None:
            title_label = ttk.Label(self.container, text=title, style=theme.title_label)
        else:
            title_label = ttk.Label(
                self.container, text=title, font=("TkDefaultFont", 10, "bold")
            )
        # Above the buttons (which already fill the remaining space)
        title_label.pack(side=tk.TOP, fill=tk.X, before=self.buttons_frame)
        self._widgets["title"] = title_label

    def pack_button(self, btn, layout):
        if self.theme is not None:
            btn.pack(side=tk.TOP, fill=tk.X, pady=1)
        else:
            btn.pack(fill=tk.X)


def _menu_is_empty(menu: tk.Menu) -> bool:
    """True if ``menu`` has no entries other than a tear-off line."""
    last = menu.index("end")
    if last is None:
        return True
    return all(menu.type(i) == "tearoff" for i in range(last + 1))


class MenuOpener(TabOpener):
    """Menu-based tab opener with smart refresh."""

    def setup_opener(self, tab_configs: list[TabConfig]):
        root = self._get_root_window()
        if not root:
            raise ValueError("MenuOpener requires a Toplevel or Tk parent")

        if not getattr(root, "menubar", None):
            root.menubar = tk.Menu(root)
            root.menubar._flextabs_created = True  # removed again when empty
            root.config(menu=root.menubar)

        menu_title = self.config.get("menu_title", "Tabs")
        menu_options = self.theme.menu_options() if self.theme is not None else {}
        self.tabs_menu = tk.Menu(root.menubar, tearoff=0, **menu_options)
        root.menubar.add_cascade(label=menu_title, menu=self.tabs_menu)
        self._widgets["menu"] = self.tabs_menu

        self._create_menu_items(tab_configs)

    def _create_menu_items(self, tab_configs: list[TabConfig]):
        for tab_config in tab_configs:
            item_kwargs = {
                "label": self._get_button_text(tab_config),
                "command": lambda tid=tab_config.id: self._open_tab_safe(tid),
            }
            image = self._load_icon(tab_config)
            if image is not None:
                item_kwargs["image"] = image
                item_kwargs["compound"] = "left"

            self.tabs_menu.add_command(**item_kwargs)

    def _load_icon(self, tab_config: TabConfig):
        """Menus take a single image, so use the full-colour icon."""
        if not self.show_icons:
            return None
        spec = self._icon_spec(tab_config)
        if not spec or IconManager.is_text_icon(spec):
            return None
        if tab_config.id not in self._icons:
            theme = self.theme
            if theme is not None:
                image = theme.icon_states(
                    spec, self.icon_size, self.parent, selectable=False
                )
            else:
                image = IconManager.render(spec, self.icon_size, "#3f3f46", self.parent)
            self._icons[tab_config.id] = image
        return self._icons[tab_config.id]

    def _smart_refresh(self, tab_configs: list[TabConfig]) -> bool:
        if not hasattr(self, "tabs_menu"):
            return False

        try:
            self.tabs_menu.delete(0, "end")
            self._icons.clear()
            self._create_menu_items(tab_configs)
            return True
        except Exception:
            logger.exception("Menu refresh failed")
            return False

    def refresh_opener(self, tab_configs: list[TabConfig]):
        self._smart_refresh(tab_configs)

    def cleanup(self):
        """Remove this opener's cascade from the menubar, then destroy the menu."""
        tabs_menu = getattr(self, "tabs_menu", None)
        root = self._get_root_window()
        menubar = getattr(root, "menubar", None) if root else None
        if tabs_menu is not None and menubar is not None:
            try:
                last = menubar.index("end")
                for i in range(last, -1, -1) if last is not None else ():
                    if menubar.type(i) == "cascade" and menubar.entrycget(
                        i, "menu"
                    ) == str(tabs_menu):
                        menubar.delete(i)
                # Detach a menubar we created once no menus remain in it
                if getattr(menubar, "_flextabs_created", False) and _menu_is_empty(
                    menubar
                ):
                    root.config(menu="")
                    menubar.destroy()
                    root.menubar = None
            except tk.TclError:
                pass  # menubar already destroyed
        super().cleanup()

    def _get_root_window(self) -> tk.Tk | tk.Toplevel | None:
        parent = self.parent
        while parent:
            if isinstance(parent, (tk.Tk, tk.Toplevel)):
                return parent
            parent = parent.master
        return None
