# FlexTabs API Documentation

Reference for FlexTabs 0.3.0. For an introduction and examples, see the [README](https://github.com/MS-32154/flextabs#readme).

## Table of Contents

1. [Core Classes](#core-classes)
   - [TabManager](#tabmanager)
   - [TabConfig](#tabconfig)
   - [TabContent](#tabcontent)
2. [Icons](#icons)
   - [IconManager](#iconmanager)
3. [Themes](#themes)
   - [Palette](#palette)
   - [Theme functions](#theme-functions)
4. [Enums](#enums)
5. [Opener Classes](#opener-classes)
6. [Widget Classes](#widget-classes)
7. [Utility Functions](#utility-functions)
8. [Advanced Topics](#advanced-topics)

---

## Core Classes

### TabManager

`TabManager(ttk.Frame)`: the main widget. It holds an opener (sidebar, toolbar or menu) and a `ttk.Notebook`, and manages the tabs' lifecycle.

#### Constructor

```python
TabManager(
    parent: tk.Misc,
    tab_configs: list[TabConfig],
    opener_type: str = "sidebar",
    opener_config: dict[str, Any] | None = None,
    close_button_style: str = "right_click",
    notebook_config: dict[str, Any] | None = None,
    close_confirmation: bool = False,
    close_confirmation_type: str | CloseConfirmationType = CloseConfirmationType.NONE,
    close_mode: str | CloseMode = CloseMode.ACTIVE_ONLY,
    enable_keyboard_shortcuts: bool = True,
    notebook_icon_size: tuple[int, int] = (16, 16),
    show_notebook_icons: bool = True,
    notebook_fallback_icon_key: str = "default",
    use_notebook_fallback_icons: bool = False,
    theme: str | Palette | None = "auto",
    **kwargs,
)
```

**Parameters:**

- `parent`: parent widget
- `tab_configs`: the available tabs
- `opener_type`: `"sidebar"`, `"toolbar"` or `"menu"`
- `opener_config`: options for the opener (see [Opener Classes](#opener-classes))
- `close_button_style`: `"button"` (close glyph on hovered/selected tabs, plus right-click), `"right_click"`, `"double_click"` or `"both"`
- `notebook_config`: extra `ttk.Notebook` options; a `"style"` here overrides the theme's notebook style
- `close_confirmation`: ask before closing a tab
- `close_confirmation_type`: dialog type, see [CloseConfirmationType](#closeconfirmationtype)
- `close_mode`: which tab a right-click or double-click closes, see [CloseMode](#closemode)
- `enable_keyboard_shortcuts`: built-in shortcuts and per-tab shortcuts
- `notebook_icon_size`: icon size on notebook tabs
- `show_notebook_icons`: show icons on notebook tabs
- `notebook_fallback_icon_key`: fallback icon key for tabs without an icon
- `use_notebook_fallback_icons`: show a fallback icon on tabs without an icon
- `theme`: `"auto"` (match the app's ttk theme), `"light"`, `"dark"`, a [Palette](#palette), or `None` for the plain ttk look. FlexTabs never changes the app's global ttk theme.
- `**kwargs`: extra `ttk.Frame` options

#### Tab operations

```python
def open_tab(self, tab_id: str) -> bool:
    """Open a tab (or select it if already open). Returns True on success."""

def close_tab(self, tab_id: str) -> bool:
    """Close a tab. Returns True if it was closed."""

def select_tab(self, tab_id: str) -> bool:
    """Select a tab, opening it if needed."""

def close_all_tabs(self) -> int:
    """Close all open tabs that allow it. Returns the number closed."""
```

`close_tab()` returns False if the tab is not open, is not closable, its `on_tab_close()` returns False, or the user declines the confirmation dialog.

#### Queries

```python
def is_tab_open(self, tab_id: str) -> bool
def get_open_tabs(self) -> list[str]
def get_current_tab(self) -> str | None          # selected tab, read live
def get_tab_index(self, tab_id: str) -> int | None  # position in the notebook
def get_tab_content(self, tab_id: str) -> TabContent | None
def get_close_mode(self) -> CloseMode
```

#### Runtime configuration

```python
def add_tab_config(self, config: TabConfig)
    """Add a tab. Raises ValueError if the ID exists."""

def remove_tab_config(self, tab_id: str) -> bool
    """Remove a tab (closing it first) and its shortcut."""

def set_close_mode(self, mode: str | CloseMode)

def set_theme(self, theme: str | Palette | None)
    """Switch the look at runtime. Raises ValueError for unknown names."""
```

#### Icons

```python
def refresh_tab_icons(self)
    """Reload all icons (clears the shared icon cache; use after icon files change)."""

def set_notebook_icon_settings(
    self,
    show_icons: bool | None = None,
    icon_size: tuple[int, int] | None = None,
    fallback_icon_key: str | None = None,
    use_fallback_icons: bool | None = None,
)

def set_opener_icon_settings(self, **kwargs)
    """Accepts show_icons, icon_size, fallback_icon_key, use_fallback_icons, icon_position."""

def get_available_fallback_icons(self) -> dict[str, str]
def add_fallback_icon(self, key: str, icon: str)
```

#### Utilities

```python
def show_notification(self, message: str, toast_type: str = "info", duration: int = 2000)

def add_close_button(self, parent: tk.Misc, tab_id: str) -> ttk.Button
    """A "Close" button (with a close icon) that closes tab_id. Raises ValueError
    if the tab is not closable."""

def cleanup(self)
    """Release everything: runs each open tab's cleanup(), removes key bindings
    and the opener. Called automatically by destroy()."""
```

#### Attributes

- `notebook`: the internal `ttk.Notebook`
- `opener`: the opener instance
- `theme`: the active `Theme`, or `None` for the plain look
- `tab_configs`: `dict[str, TabConfig]`
- `tab_states`: `dict[str, dict]` with `opened`, `tab_object`, `content_instance` and `last_error` per tab

#### Events

```python
tab_manager.on_tab_opened = lambda tab_id: ...
tab_manager.on_tab_closed = lambda tab_id: ...
tab_manager.on_tab_switched = lambda new_id, old_id: ...
tab_manager.on_tab_error = lambda tab_id, error: ...
```

Exceptions raised by callbacks and tab hooks are passed to `on_tab_error`; without it, FlexTabs shows an error toast and logs the error. A failing `on_tab_opened` or `on_tab_closed` does not make the open or close fail. Callbacks are not called while the manager is destroyed.

---

### TabConfig

```python
@dataclass
class TabConfig:
    id: str                                  # Required: unique identifier
    title: str                               # Required: display title
    content_class: type                      # Required: TabContent subclass
    icon: str | dict | None = None           # Optional: see Icons
    tooltip: str | None = None               # Optional: tooltip on the opener item
    closable: bool = True                    # Optional
    keyboard_shortcut: str | None = None     # Optional: Tk event sequence
    data: dict[str, Any] = field(default_factory=dict)  # Optional: your data
```

Raises `ValueError` if `id` or `title` is empty or `content_class` is not a `TabContent` subclass.

```python
def get_icon(self, context: str = "default") -> str | None:
    """Icon spec for "opener" or "tab" (dict icons), falling back to "default"."""
```

---

### TabContent

Abstract base class for the content of a tab.

```python
class TabContent(ABC):
    def __init__(self, parent: tk.Misc, tab_id: str, config: TabConfig, manager):
        # Called by TabManager; creates self.frame and calls setup_content()

    @abstractmethod
    def setup_content(self):
        """Build the tab's UI inside self.frame."""

    def on_tab_focus(self): ...        # the tab was selected
    def on_tab_blur(self): ...         # another tab was selected
    def on_tab_close(self) -> bool:    # return False to keep the tab open
        return True
    def cleanup(self): ...             # destroys self.frame; call super()

    def get_manager(self) -> TabManager | None
    @property
    def is_initialized(self) -> bool
```

Attributes: `parent`, `tab_id`, `config`, `frame` (a `ttk.Frame` to build in) and `manager` (a weak reference; use `get_manager()`).

If `setup_content()` raises, the tab is not opened, `RuntimeError` is reported through `on_tab_error`, and `open_tab()` returns False.

`cleanup()` runs when the tab closes and when the manager is destroyed, including for tabs that are not closable.

---

## Icons

An icon spec is resolved in this order:

1. **Built-in icon name**, such as `"home"`: rendered as an SVG image in the theme's colours (needs Tk 9)
2. **Image file path**: any value containing a path separator or ending in an image extension Pillow can open; loaded with Pillow and resized
3. **Text**: anything else, shown before the title (emoji work too)

Built-in icons: `alert`, `bell`, `calendar`, `chart`, `check-circle`, `close`, `code`, `database`, `file`, `file-text`, `folder`, `globe`, `grid`, `help`, `home`, `image`, `info`, `layers`, `lock`, `moon`, `plus`, `refresh`, `search`, `settings`, `shield`, `sun`, `terminal`, `trash`, `trending`, `user`, `x-circle`.

### IconManager

Class-level icon utilities. Images are cached per Tk interpreter.

```python
# Classification
IconManager.is_builtin(icon: str | None) -> bool
IconManager.is_image_path(icon: str | None) -> bool
IconManager.is_text_icon(icon: str | None) -> bool
IconManager.builtin_names() -> list[str]

# Rendering
IconManager.get_builtin_icon(
    name: str,
    size: int | tuple[int, int] | None = None,   # pixels (height)
    color: str = "#52525b",
    master: tk.Misc | None = None,
) -> tk.PhotoImage | None                         # None if unknown or no SVG support

IconManager.get_icon(icon_path: str, size: tuple | None = None,
                     master: tk.Misc | None = None) -> ImageTk.PhotoImage | None

IconManager.render(spec: str | None, size=None, color="#52525b",
                   master=None) -> PhotoImage | None   # built-in or file

IconManager.register_icon(name: str, svg_body: str)
    """Add an icon from inner SVG markup on a 24x24 grid. Strokes use the icon
    colour; use currentColor for fills."""

IconManager.svg_for(name: str, color: str, stroke_width: float | None = None) -> str

# Cache
IconManager.preload_icons(icon_paths: list[str], size=None, master=None)
IconManager.clear_cache()

# Fallback icons (used when enabled and a tab has no icon)
IconManager.get_fallback_icon(fallback_key: str | None = None) -> str
IconManager.get_fallback_text(fallback_key: str | None = None) -> str  # alias
IconManager.add_fallback_icon(key: str, icon: str)
IconManager.get_fallback_icons() -> dict[str, str]
```

Default fallback icons (key to built-in icon): `default`: `file`, `home`: `home`, `settings`: `settings`, `help`: `help`, `tools`: `grid`, `data`: `chart`, `reports`: `trending`, `folder`: `folder`, `file`: `file`, `image`: `image`, `text`: `file-text`, `code`: `code`, `database`: `database`, `network`: `globe`, `security`: `lock`, `user`: `user`, `admin`: `shield`, `error`: `x-circle`, `warning`: `alert`, `info`: `info`, `success`: `check-circle`.

---

## Themes

Module `flextabs.theme`. FlexTabs builds flat styles named `FlexTabs.<palette>-<hash>.*` from elements cloned out of Tk's `default` theme, so they look the same on every platform and leave other widgets alone.

### Palette

```python
@dataclass(frozen=True)
class Palette:
    name: str
    surface: str      # content area and selected tab
    bg: str           # sidebar, toolbar and tab bar
    hover: str
    selected: str     # selected opener item
    border: str
    text: str
    text_muted: str   # closed items, unselected tabs, captions
    accent: str       # indicator bars, accent buttons
    on_accent: str
    tooltip_bg: str
    tooltip_fg: str
    info: str         # toast status colours
    success: str
    warning: str
    error: str
    dark: bool = False
```

Presets: `LIGHT` and `DARK` (exported from `flextabs`). Make variants with `dataclasses.replace(LIGHT, name="brand", accent="#7c3aed")`. Styles are keyed by the palette's contents, so variants never overwrite each other.

### Theme functions

```python
apply_app_theme(root, palette: str | Palette = "light",
                font_family: str | None = "auto", font_size: int | None = None) -> Palette
    """Opt-in: restyle the whole app. Switches ttk to "clam", recolours the
    standard ttk widgets and Text/Listbox/Menu defaults, applies fonts and
    registers the palette for toasts and tooltips."""

apply_fonts(root, family: str | None = "auto", size: int | None = None,
            mono_family: str | None = "auto") -> str | None
    """Point Tk's named fonts at a modern UI font. "auto" picks the first
    available of UI_FONTS on X11 only; returns the family applied or None."""

pick_font_family(widget, candidates: tuple[str, ...]) -> str | None

palette_from_style(widget) -> Palette     # palette matching the current ttk theme
palette_for(widget) -> Palette            # palette registered for the window, else derived
register_palette(widget, palette, owner="app")  # palette for toasts/tooltips in a window
unregister_palette(widget, owner="app")         # remove that owner's palette again
resolve_palette(spec, widget) -> Palette  # "auto", "light", "dark" or a Palette
```

`UI_FONTS` and `MONO_FONTS` list the preferred font families.

#### Styling with a theme

With a theme, opener buttons use these ttk states:

- `selected`: the selected tab (accent bar and highlight)
- `alternate`: an open tab (full-strength text)
- neither: a closed tab (muted text)

Without a theme (`theme=None`), open tabs are marked `selected`, as in earlier versions.

---

## Enums

### TabPosition

```python
class TabPosition(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
```

### CloseMode

Which tab a right-click or double-click closes:

```python
class CloseMode(Enum):
    ACTIVE_ONLY = "active_only"  # only the selected tab
    ANY_VISIBLE = "any_visible"  # the tab under the pointer
    BOTH = "both"                # the selected tab, or any tab with Ctrl held
```

### CloseConfirmationType

```python
class CloseConfirmationType(Enum):
    NONE = "none"        # no dialog
    YESNO = "yesno"      # Yes/No question
    WARNING = "warning"  # OK/Cancel warning
    INFO = "info"        # information only; always closes
```

---

## Opener Classes

### TabOpener (base class)

```python
class TabOpener(ABC):
    def __init__(self, parent: tk.Misc, config: dict[str, Any])

    @abstractmethod
    def setup_opener(self, tab_configs: list[TabConfig]): ...

    def refresh_opener(self, tab_configs: list[TabConfig])  # rebuild items
    def set_tab_manager(self, tab_manager)
    def update_tab_state(self, tab_id: str, is_open: bool)  # a tab opened/closed
    def update_current_tab(self, tab_id: str | None)        # selection changed
    def cleanup(self)

    @property
    def theme(self) -> Theme | None  # the manager's theme
```

Options common to all openers:

```python
{
    "show_icons": True,
    "icon_size": (16, 16),
    "icon_position": "left",       # "left", "right", "top", "bottom"
    "use_fallback_icons": False,
    "fallback_icon_key": "default",
    "style": {},                   # extra options for the container ttk.Frame
    "button_style": {},            # extra options for each ttk.Button
}
```

### SidebarOpener

```python
{"position": "left", "width": 180, "title": None}  # position: "left" or "right"
```

Attributes: `sidebar` (the container), `buttons` (`dict[str, ttk.Button]`).

### ToolbarOpener

```python
{"position": "top", "layout": "horizontal"}  # position: top/bottom/left/right
```

Attributes: `toolbar` (the container), `buttons` (`dict[str, ttk.Button]`).

### MenuOpener

```python
{"menu_title": "Tabs"}
```

Adds a cascade to the window's menubar, creating the menubar if needed, and removes it on cleanup. Items show icons as images. Attribute: `tabs_menu`.

---

## Widget Classes

### TooltipWidget

```python
TooltipWidget(
    widget: tk.Misc,
    text: str,
    delay: int = 500,
    wraplength: int = 280,
    font: tuple | str | None = None,   # defaults to TkDefaultFont
)

def update_text(self, new_text: str)
```

Colours come from the window's palette. Bindings are added alongside the widget's existing ones.

### ToastNotification

```python
ToastNotification.show(
    parent: tk.Misc,
    message: str,
    duration: int = 2000,              # milliseconds
    toast_type: str = "info",          # "info", "success", "warning", "error"
    position: str = "top-right",       # "top-right", "bottom-right", "top-left", "bottom-left"
    mode: str = "stacked",             # "stacked" or "queued"
)
```

Toasts are cards with a status icon, sized to their message and coloured from the window's palette. Click a toast to dismiss it. `ToastNotification.ICONS` maps each type to a built-in icon; `COLORS` lists the light palette's status colours for reference.

---

## Utility Functions

```python
from flextabs import (
    apply_app_theme, apply_fonts, enable_dpi_awareness,
    create_simple_tab_manager, create_tab_config,
    get_version, get_version_info,
)

enable_dpi_awareness() -> bool
    """Windows only: make the process DPI aware so Tk renders sharply on
    high-DPI screens. Call before creating tk.Tk(). No-op elsewhere."""

create_simple_tab_manager(parent, tab_configs, opener_type="sidebar", **kwargs) -> TabManager
    """TabManager with default opener settings for the chosen type."""

create_tab_config(id, title, content_class, **kwargs) -> TabConfig

get_version() -> str
get_version_info() -> dict
add_default_fallback_icons()  # restore the built-in fallback icon mapping
```

Aliases: `TabPane` and `TabSheet` are alternative names for `TabContent`.

---

## Advanced Topics

### Several managers in one window

Shortcuts are bound on the toplevel window. When several managers share a window, each key press goes to one manager: the one containing keyboard focus, or else the one used most recently. Bindings are added with `add="+"` and removed individually, so your own bindings are never replaced.

### Custom openers

```python
class CustomOpener(TabOpener):
    def setup_opener(self, tab_configs):
        ...  # build widgets in self.parent; call self._open_tab_safe(tab_id) to open

    def update_tab_state(self, tab_id, is_open):
        ...  # reflect open/closed

    def update_current_tab(self, tab_id):
        ...  # reflect the selection
```

### Logging

FlexTabs logs through `logging` under the `flextabs` logger (and its submodules, such as `flextabs.tab_manager`).

### Threads

Tkinter is single-threaded. Update tabs from other threads with `widget.after()` or a queue polled from the main thread.

---

flextabs © 2025 MS-32154. All rights reserved.
