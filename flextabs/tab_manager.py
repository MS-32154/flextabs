import contextlib
import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from PIL import ImageTk

from .enums import CloseConfirmationType, CloseMode
from .icons import IconManager
from .openers import MenuOpener, SidebarOpener, ToolbarOpener
from .shortcuts import FocusScope, ShortcutRegistry
from .tab_base import TabConfig, TabContent
from .widgets import ToastNotification

logger = logging.getLogger(__name__)


class TabManager(ttk.Frame):
    """Enhanced tab manager that can be used as a widget or library."""

    def __init__(
        self,
        parent: tk.Misc,
        tab_configs: list[TabConfig],
        opener_type: str = "sidebar",
        opener_config: dict[str, Any] | None = None,
        close_button_style: str = "right_click",
        notebook_config: dict[str, Any] | None = None,
        close_confirmation: bool = False,
        close_confirmation_type: (
            str | CloseConfirmationType
        ) = CloseConfirmationType.NONE,
        close_mode: str | CloseMode = CloseMode.ACTIVE_ONLY,
        enable_keyboard_shortcuts: bool = True,
        # Separate notebook tab icon configuration
        notebook_icon_size: tuple[int, int] = (16, 16),
        show_notebook_icons: bool = True,
        notebook_fallback_icon_key: str = "default",
        use_notebook_fallback_icons: bool = True,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        # Configuration
        self.tab_configs = {config.id: config for config in tab_configs}
        self.opener_config = opener_config or {}
        self.close_button_style = close_button_style
        self.notebook_config = notebook_config or {}
        self.close_confirmation = close_confirmation
        self.enable_keyboard_shortcuts = enable_keyboard_shortcuts

        # Notebook icon configuration (separate from opener)
        self.notebook_icon_size = notebook_icon_size
        self.show_notebook_icons = show_notebook_icons
        self.notebook_fallback_icon_key = notebook_fallback_icon_key
        self.use_notebook_fallback_icons = use_notebook_fallback_icons

        # Handle enum conversions
        self.close_confirmation_type = (
            CloseConfirmationType(close_confirmation_type)
            if isinstance(close_confirmation_type, str)
            else close_confirmation_type
        )
        self.close_mode = (
            CloseMode(close_mode) if isinstance(close_mode, str) else close_mode
        )

        # State management
        self.tab_states: dict[str, dict[str, Any]] = {}
        self._tab_icons: dict[str, ImageTk.PhotoImage | None] = {}
        self._initialize_tab_states(tab_configs)

        # Event callbacks
        self.on_tab_opened: Callable[[str], None] | None = None
        self.on_tab_closed: Callable[[str], None] | None = None
        self.on_tab_switched: Callable[[str, str | None], None] | None = None
        self.on_tab_error: Callable[[str, Exception], None] | None = None

        # Internal state
        self._current_tab_id: str | None = None
        self._is_destroyed = False
        self._shortcuts = ShortcutRegistry()
        self._focus_scope: FocusScope | None = None

        # Setup UI
        try:
            self._setup_opener(opener_type)
            self._setup_notebook()
            self._setup_close_buttons()
            if self.enable_keyboard_shortcuts:
                self._setup_keyboard_shortcuts()
            self._preload_icons()
        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Failed to initialize TabManager: {e}") from e

    def _initialize_tab_states(self, tab_configs: list[TabConfig]):
        """Initialize tab states."""
        for config in tab_configs:
            self.tab_states[config.id] = self._new_tab_state()

    @staticmethod
    def _new_tab_state() -> dict[str, Any]:
        """Return the initial state dict for a tab."""
        return {
            "opened": False,
            "exited": False,
            "tab_object": None,
            "content_instance": None,
            "last_error": None,
        }

    def _preload_icons(self):
        """Preload all icons for better performance."""
        # Collect all icon paths for both contexts
        opener_icon_paths = []
        tab_icon_paths = []

        for config in self.tab_configs.values():
            opener_icon = config.get_icon("opener")
            tab_icon = config.get_icon("tab")

            if opener_icon:
                opener_icon_paths.append(opener_icon)
            if tab_icon:
                tab_icon_paths.append(tab_icon)

        # Preload opener icons
        if opener_icon_paths and hasattr(self.opener, "icon_size"):
            IconManager.preload_icons(
                opener_icon_paths, self.opener.icon_size, master=self
            )

        # Preload notebook tab icons
        if tab_icon_paths and self.show_notebook_icons:
            IconManager.preload_icons(
                tab_icon_paths, self.notebook_icon_size, master=self
            )

    def _load_notebook_icon(self, tab_config: TabConfig) -> ImageTk.PhotoImage | None:
        """Load icon for notebook tab."""
        if not self.show_notebook_icons:
            return None

        icon_path = tab_config.get_icon("tab")
        if not icon_path:
            return None

        cache_key = f"tab_{tab_config.id}"
        if cache_key not in self._tab_icons:
            self._tab_icons[cache_key] = IconManager.get_icon(
                icon_path, self.notebook_icon_size, master=self
            )

        return self._tab_icons[cache_key]

    def _get_tab_text_with_icon(self, tab_config: TabConfig) -> str:
        """Get tab text, potentially with emoji icon."""
        text = tab_config.title

        # Add unclosable indicator
        if not tab_config.closable:
            text = f"• {text}"

        icon_path = tab_config.get_icon("tab")
        cache_key = f"tab_{tab_config.id}"

        # Text/emoji icon, otherwise fall back if no image could be loaded
        if self.show_notebook_icons and IconManager.is_text_icon(icon_path):
            text = f"{icon_path} {text}"
        elif (
            self.show_notebook_icons
            and self.use_notebook_fallback_icons
            and self._tab_icons.get(cache_key) is None
        ):
            # Use fallback icon if no image was loaded
            fallback_text = IconManager.get_fallback_text(
                self.notebook_fallback_icon_key
            )
            text = f"{fallback_text} {text}"

        return text

    def _setup_opener(self, opener_type: str):
        """Setup the tab opener based on type."""
        opener_classes = {
            "toolbar": ToolbarOpener,
            "sidebar": SidebarOpener,
            "menu": MenuOpener,
        }

        if opener_type not in opener_classes:
            raise ValueError(
                f"Unknown opener type: {opener_type}. Available: {list(opener_classes)}"
            )

        self.opener = opener_classes[opener_type](self, self.opener_config)
        self.opener.set_tab_manager(self)
        self.opener.setup_opener(list(self.tab_configs.values()))

    def _setup_notebook(self):
        """Setup the main notebook widget."""
        config = {"style": "TabManager.TNotebook"}
        config.update(self.notebook_config)

        self.notebook = ttk.Notebook(self, **config)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.notebook.bind("<Button-1>", lambda e: self._mark_active(), add="+")
        self.notebook.bind("<Destroy>", self._on_notebook_destroy)

    def _setup_close_buttons(self):
        """Setup close button functionality."""
        if self.close_button_style in ["right_click", "both"]:
            self.notebook.bind("<Button-3>", self._on_tab_click)
        if self.close_button_style in ["double_click", "both"]:
            self.notebook.bind("<Double-Button-1>", self._on_tab_click)

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for tab navigation.

        Shortcuts are bound on the toplevel window. When several managers share
        a window, a FocusScope routes each key press to a single manager: the
        one containing keyboard focus, else the most recently used one.
        """
        self._focus_scope = FocusScope(self)
        root = self.winfo_toplevel()

        shortcuts = {
            "<Control-w>": self._close_current_tab,
            "<Control-Tab>": self._next_tab,
            "<Control-Shift-Tab>": self._prev_tab,
        }
        for i in range(1, 10):
            shortcuts[f"<Control-Key-{i}>"] = lambda idx=i - 1: (
                self._select_tab_by_index(idx)
            )

        for sequence, action in shortcuts.items():
            self._shortcuts.bind(root, sequence, self._scoped(action))

        for config in self.tab_configs.values():
            self._bind_tab_shortcut(config)

    def _scoped(self, action: Callable[[], object]) -> Callable:
        """Wrap a shortcut action so it only runs for the manager owning the event."""

        def handler(event=None):
            if (
                not self._is_destroyed
                and self._focus_scope is not None
                and self._focus_scope.owns_event()
            ):
                action()

        return handler

    def _bind_tab_shortcut(self, config: TabConfig):
        """Bind a tab's own keyboard shortcut (if any) to open it."""
        if config.keyboard_shortcut:
            self._shortcuts.bind(
                self.winfo_toplevel(),
                config.keyboard_shortcut,
                self._scoped(lambda tid=config.id: self.open_tab(tid)),
                tag=config.id,
            )

    def _mark_active(self):
        """Record this manager as the most recently used one in its window."""
        if self._focus_scope is not None:
            self._focus_scope.activate()

    def _close_current_tab(self, event=None):
        """Close the currently selected tab."""
        tab_id = self.get_current_tab()
        if tab_id:
            self.close_tab(tab_id)

    def _next_tab(self, event=None):
        """Switch to the next tab."""
        tabs = self.notebook.tabs()
        if tabs:
            current = self.notebook.select()
            current_index = tabs.index(current) if current in tabs else -1
            self.notebook.select(tabs[(current_index + 1) % len(tabs)])

    def _prev_tab(self, event=None):
        """Switch to the previous tab."""
        tabs = self.notebook.tabs()
        if tabs:
            current = self.notebook.select()
            current_index = tabs.index(current) if current in tabs else -1
            self.notebook.select(tabs[(current_index - 1) % len(tabs)])

    def _select_tab_by_index(self, index: int):
        """Select tab by index."""
        tabs = self.notebook.tabs()
        if 0 <= index < len(tabs):
            self.notebook.select(tabs[index])

    def _on_tab_click(self, event):
        """Handle tab clicks for closing."""
        tab_id = self._get_tab_id_at_position(event.x, event.y)
        if not tab_id:
            return

        config = self.tab_configs[tab_id]

        if not config.closable:
            ToastNotification.show(
                self, f"Tab '{config.title}' cannot be closed", toast_type="warning"
            )
            return

        # Handle different close modes
        should_close = False
        if self.close_mode == CloseMode.ANY_VISIBLE or (
            self.close_mode == CloseMode.BOTH and event.state & 0x4
        ):
            should_close = True
        elif self.close_mode in [CloseMode.ACTIVE_ONLY, CloseMode.BOTH]:
            current_selection = self.notebook.select()
            if current_selection:
                current_tab_id = self._get_tab_id_by_widget(current_selection)
                should_close = current_tab_id == tab_id

        if should_close:
            self.close_tab(tab_id)

    def _get_tab_id_at_position(self, x: int, y: int) -> str | None:
        """Get tab ID at the given position."""
        try:
            clicked_tab = self.notebook.index(f"@{x},{y}")
        except tk.TclError:
            return None  # not over a tab
        return self._get_tab_id_by_index(clicked_tab)

    def _on_tab_changed(self, event):
        """Handle tab selection changes."""
        if self._is_destroyed:
            return

        current_tab = self.notebook.select()
        old_tab_id = self._current_tab_id
        new_tab_id = self._get_tab_id_by_widget(current_tab) if current_tab else None

        # Handle tab focus/blur
        if old_tab_id and old_tab_id != new_tab_id:
            old_content = self.tab_states.get(old_tab_id, {}).get("content_instance")
            if old_content:
                try:
                    old_content.on_tab_blur()
                except Exception as e:  # noqa: BLE001 - user hook, reported
                    self._handle_tab_error(old_tab_id, e)

        self._current_tab_id = new_tab_id
        if new_tab_id:
            self._mark_active()
            new_content = self.tab_states[new_tab_id]["content_instance"]
            if new_content:
                try:
                    new_content.on_tab_focus()
                except Exception as e:  # noqa: BLE001 - user hook, reported
                    self._handle_tab_error(new_tab_id, e)

        # Fire switch event
        self._fire_callback(
            self.on_tab_switched, new_tab_id or "unknown", new_tab_id, old_tab_id
        )

    def _on_notebook_destroy(self, event):
        """Handle notebook destruction."""
        if event.widget == self.notebook:
            self.cleanup()

    def _get_tab_id_by_index(self, index: int) -> str | None:
        """Get tab ID by its current position in the notebook."""
        tabs = self.notebook.tabs()
        if 0 <= index < len(tabs):
            return self._get_tab_id_by_widget(tabs[index])
        return None

    def get_tab_index(self, tab_id: str) -> int | None:
        """Get a tab's current position in the notebook, or None if not open."""
        state = self.tab_states.get(tab_id)
        if not state or not state["opened"] or state["tab_object"] is None:
            return None
        try:
            return self.notebook.index(state["tab_object"])
        except tk.TclError:
            return None

    def _get_tab_id_by_widget(self, widget_name: str) -> str | None:
        """Get tab ID by widget name."""
        for tab_id, state in self.tab_states.items():
            if (
                state["opened"]
                and state["tab_object"]
                and str(state["tab_object"]) == widget_name
            ):
                return tab_id
        return None

    def _handle_tab_error(self, tab_id: str, error: Exception):
        """Record a tab error and report it via on_tab_error, or toast + log."""
        if tab_id in self.tab_states:
            self.tab_states[tab_id]["last_error"] = error

        if self.on_tab_error:
            try:
                self.on_tab_error(tab_id, error)
            except Exception:
                logger.exception("on_tab_error callback failed for tab %r", tab_id)
        else:
            logger.error("Error in tab %r", tab_id, exc_info=error)
            ToastNotification.show(
                self, f"Error in tab '{tab_id}': {error}", toast_type="error"
            )

    def open_tab(self, tab_id: str) -> bool:
        """Open a tab. Returns True if successful."""
        if self._is_destroyed or tab_id not in self.tab_configs:
            return False

        self._mark_active()
        try:
            state = self.tab_states[tab_id]
            config = self.tab_configs[tab_id]

            if state["opened"] and not state["exited"]:
                self.notebook.select(state["tab_object"])
                return True

            return self._create_tab(tab_id, state, config)

        except Exception as e:  # noqa: BLE001 - user content class, reported
            self._handle_tab_error(tab_id, e)
            return False

    def _create_tab(self, tab_id: str, state: dict, config: TabConfig) -> bool:
        """Create a new tab with icon support."""
        # Create tab container and content
        state["tab_object"] = ttk.Frame(self.notebook)

        try:
            state["content_instance"] = config.content_class(
                state["tab_object"], tab_id, config, self
            )
        except Exception:
            state["tab_object"].destroy()
            state["tab_object"] = None
            raise

        # Get icon and text for notebook tab
        icon = self._load_notebook_icon(config)
        tab_text = self._get_tab_text_with_icon(config)

        # Add to notebook with icon if available
        add_kwargs = {"text": tab_text}
        if icon:
            add_kwargs["image"] = icon
            add_kwargs["compound"] = "left"

        self.notebook.add(state["tab_object"], **add_kwargs)

        # Keep reference to prevent garbage collection
        if icon:
            state["tab_object"]._tab_icon = icon

        state["opened"] = True
        state["exited"] = False

        # Select the new tab
        self.notebook.select(state["tab_object"])

        # Update opener and fire event. The tab is open at this point, so
        # errors here are reported but do not count as an open failure.
        self._notify_opener(tab_id, True)
        self._fire_callback(self.on_tab_opened, tab_id, tab_id)

        return True

    def _notify_opener(self, tab_id: str, is_open: bool):
        """Tell the opener about a tab state change, reporting any error."""
        if hasattr(self.opener, "update_tab_state"):
            try:
                self.opener.update_tab_state(tab_id, is_open)
            except Exception as e:  # noqa: BLE001 - opener may be user code
                self._handle_tab_error(tab_id, e)

    def _fire_callback(self, callback: Callable | None, tab_id: str, *args):
        """Invoke a user event callback, routing exceptions to the error handler."""
        if callback is None:
            return
        try:
            callback(*args)
        except Exception as e:  # noqa: BLE001 - user callback, reported
            self._handle_tab_error(tab_id, e)

    def close_tab(self, tab_id: str) -> bool:
        """Close a tab. Returns True if successfully closed."""
        if (
            self._is_destroyed
            or tab_id not in self.tab_states
            or not self.tab_states[tab_id]["opened"]
        ):
            return False

        state = self.tab_states[tab_id]
        config = self.tab_configs[tab_id]

        if not config.closable:
            ToastNotification.show(
                self, f"Tab '{config.title}' cannot be closed", toast_type="warning"
            )
            return False

        try:
            # Ask content if it's okay to close
            if (
                state["content_instance"]
                and not state["content_instance"].on_tab_close()
            ):
                return False

            # Show confirmation if enabled
            if self.close_confirmation and not self._show_close_confirmation(
                config.title
            ):
                return False

            return self._perform_tab_close(tab_id, state)

        except Exception as e:  # noqa: BLE001 - user hooks/dialogs, reported
            self._handle_tab_error(tab_id, e)
            return False

    def _perform_tab_close(self, tab_id: str, state: dict) -> bool:
        """Perform the actual tab close operation."""
        # Clean up content
        if state["content_instance"]:
            try:
                state["content_instance"].cleanup()
            except Exception:
                logger.exception("Error cleaning up content of tab %r", tab_id)

        # Remove from notebook and destroy the container frame
        tab_object = state["tab_object"]
        if tab_object is not None:
            with contextlib.suppress(tk.TclError):  # already removed
                self.notebook.forget(tab_object)
            with contextlib.suppress(tk.TclError):
                tab_object.destroy()

        state.update(
            {
                "opened": False,
                "exited": True,
                "content_instance": None,
                "tab_object": None,
            }
        )

        # Update opener and fire event. The tab is closed at this point, so
        # errors here are reported but do not count as a close failure.
        self._notify_opener(tab_id, False)
        self._fire_callback(self.on_tab_closed, tab_id, tab_id)

        return True

    def _show_close_confirmation(self, tab_title: str) -> bool:
        """Show confirmation dialog before closing tab."""
        if self.close_confirmation_type == CloseConfirmationType.YESNO:
            return messagebox.askyesno(
                "Close Tab",
                f"Are you sure you want to close '{tab_title}'?",
                parent=self,
            )
        if self.close_confirmation_type == CloseConfirmationType.WARNING:
            return messagebox.askokcancel(
                "Close Tab",
                f"Warning: Closing '{tab_title}' may result in data loss.\n\nContinue?",
                parent=self,
            )
        if self.close_confirmation_type == CloseConfirmationType.INFO:
            messagebox.showinfo(
                "Tab Closed", f"'{tab_title}' will be closed.", parent=self
            )
            return True
        return True

    def add_close_button(self, parent: tk.Misc, tab_id: str) -> ttk.Button:
        """Add a close button inside tab content."""
        config = self.tab_configs[tab_id]
        if not config.closable:
            raise ValueError(f"Tab '{tab_id}' is not closable")

        return ttk.Button(
            parent, text="✕ Close", command=lambda: self.close_tab(tab_id)
        )

    # Public API methods
    def is_tab_open(self, tab_id: str) -> bool:
        """Check if a tab is currently open."""
        return self.tab_states.get(tab_id, {}).get("opened", False)

    def get_open_tabs(self) -> list[str]:
        """Get list of currently open tab IDs."""
        return [
            tab_id
            for tab_id, state in self.tab_states.items()
            if state["opened"] and not state["exited"]
        ]

    def get_current_tab(self) -> str | None:
        """Get the currently selected tab ID (read live from the notebook)."""
        if self._is_destroyed:
            return None
        try:
            selected = self.notebook.select()
        except tk.TclError:
            return None
        return self._get_tab_id_by_widget(selected) if selected else None

    def select_tab(self, tab_id: str) -> bool:
        """Select a specific tab. Opens it if not already open."""
        if not self.is_tab_open(tab_id):
            return self.open_tab(tab_id)

        self._mark_active()
        tab_object = self.tab_states[tab_id]["tab_object"]
        if tab_object is None:
            return False
        try:
            self.notebook.select(tab_object)
        except tk.TclError:
            return False
        return True

    def close_all_tabs(self) -> int:
        """Close all open tabs. Returns number of tabs closed."""
        closed_count = 0
        for tab_id in list(self.get_open_tabs()):
            if self.close_tab(tab_id):
                closed_count += 1
        return closed_count

    def get_tab_content(self, tab_id: str) -> TabContent | None:
        """Get the content instance of an open tab, or None."""
        return self.tab_states.get(tab_id, {}).get("content_instance")

    def add_tab_config(self, config: TabConfig):
        """Add a new tab configuration at runtime."""
        if config.id in self.tab_configs:
            raise ValueError(f"Tab with ID '{config.id}' already exists")

        self.tab_configs[config.id] = config
        self.tab_states[config.id] = self._new_tab_state()

        # Preload icons for new tab
        opener_icon = config.get_icon("opener")
        tab_icon = config.get_icon("tab")

        if opener_icon and hasattr(self.opener, "icon_size"):
            IconManager.get_icon(opener_icon, self.opener.icon_size, master=self)
        if tab_icon and self.show_notebook_icons:
            IconManager.get_icon(tab_icon, self.notebook_icon_size, master=self)

        # Update opener and keyboard shortcut
        self._refresh_opener()

        if self.enable_keyboard_shortcuts and config.keyboard_shortcut:
            self._bind_tab_shortcut(config)

    def remove_tab_config(self, tab_id: str) -> bool:
        """Remove a tab configuration. Closes the tab if open."""
        if tab_id not in self.tab_configs:
            return False

        # Close tab if open
        if self.is_tab_open(tab_id) and not self.close_tab(tab_id):
            return False

        # Remove keyboard shortcut and configuration
        self._shortcuts.unbind(tag=tab_id)

        del self.tab_configs[tab_id]
        del self.tab_states[tab_id]

        # Clean up cached icons
        self._tab_icons.pop(f"tab_{tab_id}", None)

        # Update opener
        self._refresh_opener()

        return True

    def set_close_mode(self, mode: str | CloseMode):
        """Change the close mode at runtime."""
        self.close_mode = CloseMode(mode) if isinstance(mode, str) else mode

    def get_close_mode(self) -> CloseMode:
        """Get the current close mode."""
        return self.close_mode

    def show_notification(
        self, message: str, toast_type: str = "info", duration: int = 2000
    ):
        """Show a toast notification."""
        ToastNotification.show(self, message, duration, toast_type)

    def refresh_tab_icons(self):
        """Refresh all tab icons (useful after changing icon files)."""
        # Clear icon caches
        IconManager.clear_cache()
        self._tab_icons.clear()

        # Clear opener icons if it has them
        if hasattr(self.opener, "_icons"):
            self.opener._icons.clear()

        # Preload icons again
        self._preload_icons()

        # Use smart refresh for opener to preserve layout; rebuild if it fails
        if not self._refresh_opener():
            self._rebuild_opener()

        # Update existing notebook tabs without changing their order
        for tab_id, state in self.tab_states.items():
            if state["opened"] and state["tab_object"] is not None:
                config = self.tab_configs[tab_id]
                icon = self._load_notebook_icon(config)
                tab_text = self._get_tab_text_with_icon(config)

                tab_widget = state["tab_object"]
                try:
                    if icon:
                        self.notebook.tab(
                            tab_widget, text=tab_text, image=icon, compound="left"
                        )
                    else:
                        self.notebook.tab(tab_widget, text=tab_text, image="")
                except tk.TclError:
                    logger.warning("Failed to update tab %r", tab_id, exc_info=True)
                    continue
                # Keep a reference to prevent garbage collection
                tab_widget._tab_icon = icon

    def set_notebook_icon_settings(
        self,
        show_icons: bool | None = None,
        icon_size: tuple[int, int] | None = None,
        fallback_icon_key: str | None = None,
        use_fallback_icons: bool | None = None,
    ):
        """Update notebook icon settings at runtime."""
        if show_icons is not None:
            self.show_notebook_icons = show_icons
        if icon_size is not None:
            self.notebook_icon_size = icon_size
        if fallback_icon_key is not None:
            self.notebook_fallback_icon_key = fallback_icon_key
        if use_fallback_icons is not None:
            self.use_notebook_fallback_icons = use_fallback_icons

        if any(
            x is not None
            for x in [show_icons, icon_size, fallback_icon_key, use_fallback_icons]
        ):
            self.refresh_tab_icons()

    def set_opener_icon_settings(self, **kwargs):
        """Update opener icon settings at runtime."""
        if hasattr(self.opener, "show_icons") and "show_icons" in kwargs:
            self.opener.show_icons = kwargs["show_icons"]
        if hasattr(self.opener, "icon_size") and "icon_size" in kwargs:
            self.opener.icon_size = kwargs["icon_size"]
        if hasattr(self.opener, "fallback_icon_key") and "fallback_icon_key" in kwargs:
            self.opener.fallback_icon_key = kwargs["fallback_icon_key"]
        if (
            hasattr(self.opener, "use_fallback_icons")
            and "use_fallback_icons" in kwargs
        ):
            self.opener.use_fallback_icons = kwargs["use_fallback_icons"]
        if hasattr(self.opener, "icon_position") and "icon_position" in kwargs:
            self.opener.icon_position = kwargs["icon_position"]

        # Clear opener icon cache and refresh
        if hasattr(self.opener, "_icons"):
            self.opener._icons.clear()

        self._refresh_opener()

    def _refresh_opener(self) -> bool:
        """Refresh the opener's items; log and return False on failure."""
        if not hasattr(self.opener, "refresh_opener"):
            return True
        try:
            self.opener.refresh_opener(list(self.tab_configs.values()))
        except Exception:
            logger.exception("Opener refresh failed")
            return False
        return True

    def _rebuild_opener(self):
        """Replace the opener with a fresh instance of the same type."""
        opener_type = type(self.opener).__name__.removesuffix("Opener").lower()
        try:
            self.opener.cleanup()
        except Exception:
            logger.exception("Opener cleanup failed")
        try:
            self._setup_opener(opener_type)
        except Exception:
            logger.exception("Could not rebuild %r opener", opener_type)
        for tab_id in self.get_open_tabs():
            self._notify_opener(tab_id, True)

    def get_available_fallback_icons(self) -> dict[str, str]:
        """Get all available fallback icons."""
        return IconManager.get_fallback_icons()

    def add_fallback_icon(self, key: str, icon: str):
        """Add a custom fallback icon."""
        IconManager.add_fallback_icon(key, icon)

    def cleanup(self):
        """Clean up all resources."""
        if self._is_destroyed:
            return

        self._is_destroyed = True

        # Remove only the key bindings this manager added
        self._shortcuts.unbind_all()
        if self._focus_scope is not None:
            self._focus_scope.close()
            self._focus_scope = None

        # Tear down every open tab unconditionally (including non-closable
        # ones and ones whose on_tab_close() would veto) so TabContent.cleanup()
        # always runs. User callbacks are not fired during teardown.
        for tab_id, state in self.tab_states.items():
            content = state["content_instance"]
            if content is not None:
                try:
                    content.cleanup()
                except Exception:
                    logger.exception("Error cleaning up content of tab %r", tab_id)
            tab_object = state["tab_object"]
            if tab_object is not None:
                with contextlib.suppress(tk.TclError):
                    tab_object.destroy()
        self._current_tab_id = None

        if hasattr(self, "opener"):
            try:
                self.opener.cleanup()
            except Exception:
                logger.exception("Opener cleanup failed")

        # Clear icon caches
        self._tab_icons.clear()

        # Clear references
        self.tab_configs.clear()
        self.tab_states.clear()

    def destroy(self):
        """Override destroy to ensure cleanup."""
        self.cleanup()
        super().destroy()
