[![PyPI version](https://img.shields.io/pypi/v/flextabs.svg)](https://pypi.org/project/flextabs/)
[![Python](https://img.shields.io/badge/python-3.15%2B-blue.svg)](https://www.python.org/)
[![Tests](https://github.com/MS-32154/flextabs/actions/workflows/tests.yml/badge.svg)](https://github.com/MS-32154/flextabs/actions/workflows/tests.yml)
[![License](https://img.shields.io/github/license/MS-32154/flextabs.svg)](LICENSE)

# FlexTabs

A flexible tab manager widget for tkinter. FlexTabs builds on `ttk.Notebook` and adds tabs that open and close on demand, a sidebar, toolbar or menu to open them from, a built-in icon set, flat light and dark themes, keyboard shortcuts, toast notifications and lifecycle callbacks.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Running the Demo](#running-the-demo)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
  - [TabConfig](#tabconfig)
  - [TabContent](#tabcontent)
  - [TabManager](#tabmanager)
- [Icons](#icons)
- [Themes](#themes)
- [Opener Types](#opener-types)
- [Closing Tabs](#closing-tabs)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Event Callbacks](#event-callbacks)
- [Runtime Management](#runtime-management)
- [Notifications and Tooltips](#notifications-and-tooltips)
- [Error Handling and Logging](#error-handling-and-logging)
- [Examples](#examples)
- [Platform Notes](#platform-notes)
- [What's New in 0.3.0](#whats-new-in-030)
- [Development](#development)
- [API Reference](#api-reference)
- [License](#license)
- [Contributing](#contributing)

## Features

- **Tabs on demand**: tabs are created when first opened and can be closed and reopened at any time
- **Three opener styles**: sidebar, toolbar or a menu in the window's menubar
- **Built-in icon set**: 31 outline icons (`"home"`, `"settings"`, `"chart"`, ...) rendered as crisp vector images in the theme's colours, plus image files and text icons
- **Flat themes**: `"auto"` blends with your app's current ttk theme, or use `"light"`, `"dark"` or a custom `Palette`; FlexTabs never changes your app's global ttk theme
- **Close buttons on tabs**: an optional close glyph on the hovered and selected tab, with a lock glyph for tabs that cannot be closed
- **Keyboard shortcuts**: built-in navigation shortcuts plus a shortcut per tab, which work correctly with several tab managers in one window
- **Lifecycle hooks and callbacks**: focus, blur, close vetoes and cleanup per tab, and opened/closed/switched/error callbacks per manager
- **Toast notifications and tooltips** that follow the theme
- **Runtime configuration**: add and remove tabs, change the close mode, icons and theme while the app runs
- **Typed**: ships a `py.typed` marker

## Installation

```bash
pip install flextabs
```

Or from a clone of the repository:

```bash
git clone https://github.com/MS-32154/flextabs.git
cd flextabs
pip install -e .
```

**Requirements**

- Python 3.15+
- tkinter, normally included with Python; built-in icons need Tk 9 (see [Platform Notes](#platform-notes))
- Pillow 10+, for image file icons

## Running the Demo

```bash
python -m flextabs
```

The `flextabs-demo` command does the same. The demo shows the sidebar, toolbar and menu openers, the light/dark toggle, tab close buttons, notifications and adding tabs at runtime.

## Quick Start

```python
import tkinter as tk
from tkinter import ttk

from flextabs import TabConfig, TabContent, TabManager


class HomeTab(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text="Welcome to the Home tab").pack(pady=20)


class SettingsTab(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text="Settings").pack(pady=20)
        # A "Close" button that closes this tab
        self.get_manager().add_close_button(self.frame, self.tab_id).pack()


root = tk.Tk()
root.title("FlexTabs")
root.geometry("800x500")

tab_configs = [
    TabConfig(
        id="home",
        title="Home",
        content_class=HomeTab,
        icon="home",  # built-in icon
        tooltip="Go to the home page",
        closable=False,  # this tab cannot be closed
    ),
    TabConfig(
        id="settings",
        title="Settings",
        content_class=SettingsTab,
        icon="settings",
        keyboard_shortcut="<Control-comma>",
    ),
]

tab_manager = TabManager(
    root,
    tab_configs=tab_configs,
    opener_type="sidebar",  # or "toolbar", "menu"
    opener_config={"title": "Navigation"},
    close_button_style="button",  # close glyph on tabs
)
tab_manager.pack(fill=tk.BOTH, expand=True)
tab_manager.open_tab("home")

root.mainloop()
```

## Core Components

### TabConfig

Describes one tab:

```python
TabConfig(
    id="unique_id",                   # Required: unique identifier
    title="Tab Title",                # Required: display title
    content_class=YourContent,        # Required: TabContent subclass
    icon="home",                      # Optional: built-in name, image path or text
    tooltip="Helpful text",           # Optional: tooltip on the opener item
    closable=True,                    # Optional: whether the tab can be closed
    keyboard_shortcut="<Control-t>",  # Optional: shortcut that opens the tab
    data={"key": "value"},            # Optional: your own data
)
```

### TabContent

Base class for the content of a tab. Build your UI in `setup_content()`, inside `self.frame`:

```python
class MyTab(TabContent):
    def setup_content(self):
        """Required: build the tab's UI in self.frame."""
        ttk.Label(self.frame, text="My content").pack()

    def on_tab_focus(self):
        """Optional: the tab became the selected tab."""

    def on_tab_blur(self):
        """Optional: another tab was selected."""

    def on_tab_close(self) -> bool:
        """Optional: return False to keep the tab open."""
        return True

    def cleanup(self):
        """Optional: release resources (timers, files, ...)."""
        super().cleanup()
```

Inside a tab you have `self.tab_id`, `self.config` (its `TabConfig`), `self.frame` and `self.get_manager()`.

`cleanup()` always runs when the tab closes and when the manager is destroyed, including for tabs that are not closable.

### TabManager

```python
TabManager(
    parent,                             # Parent widget
    tab_configs=[...],                  # List of TabConfig objects
    opener_type="sidebar",              # "sidebar", "toolbar" or "menu"
    opener_config={},                   # Opener options (see Opener Types)
    close_button_style="right_click",   # "button", "right_click", "double_click", "both"
    notebook_config={},                 # Extra ttk.Notebook options
    close_confirmation=False,           # Ask before closing
    close_confirmation_type="none",     # "none", "yesno", "warning", "info"
    close_mode="active_only",           # "active_only", "any_visible", "both"
    enable_keyboard_shortcuts=True,     # Built-in and per-tab shortcuts
    notebook_icon_size=(16, 16),        # Icon size on notebook tabs
    show_notebook_icons=True,           # Show icons on notebook tabs
    notebook_fallback_icon_key="default",
    use_notebook_fallback_icons=False,  # Icon for tabs that have none
    theme="auto",                       # "auto", "light", "dark", a Palette, or None
    **kwargs,                           # Extra ttk.Frame options
)
```

## Icons

An icon (`TabConfig.icon`) can be:

```python
icon="home"                 # a built-in icon name
icon="icons/report.png"     # an image file (anything Pillow can open)
icon="A"                    # any other text, shown as text (emoji work too)

# Different icons for the opener and the notebook tab
icon={"opener": "home", "tab": "icons/home.png", "default": "file"}
```

A value is treated as an image file if it contains a path separator or ends in an image file extension, as a built-in icon if it matches a built-in name, and as text otherwise.

**Built-in icons:** `alert`, `bell`, `calendar`, `chart`, `check-circle`, `close`, `code`, `database`, `file`, `file-text`, `folder`, `globe`, `grid`, `help`, `home`, `image`, `info`, `layers`, `lock`, `moon`, `plus`, `refresh`, `search`, `settings`, `shield`, `sun`, `terminal`, `trash`, `trending`, `user`, `x-circle`.

They are drawn in the theme's colours: muted normally, and full strength for the selected or hovered item. You can use them in your own widgets and add your own:

```python
from flextabs import IconManager

image = IconManager.get_builtin_icon("home", size=20, color="#2563eb", master=root)
ttk.Button(root, text="Home", image=image, compound="left").pack()

# Inner SVG markup on a 24x24 grid (strokes use the icon colour)
IconManager.register_icon("square", '<rect x="5" y="5" width="14" height="14" rx="2"/>')
```

**Fallback icons** for tabs without an icon are off by default. Turn them on with `use_notebook_fallback_icons=True` and `opener_config={"use_fallback_icons": True}`. Fallback keys map to built-in icons (`"default"` is `"file"`), and you can add your own with `tab_manager.add_fallback_icon("reports", "trending")`.

## Themes

```python
TabManager(root, tab_configs, theme="auto")   # default: match the app's ttk theme
TabManager(root, tab_configs, theme="dark")   # preset palettes: "light" and "dark"
TabManager(root, tab_configs, theme=None)     # plain ttk look, as in earlier versions
```

FlexTabs builds its own flat styles under `FlexTabs.*` style names and does not change the app's global ttk theme. With `"auto"` it derives its colours from the app's current theme, and follows the app if it switches ttk theme later.

To restyle the whole application to match, call `apply_app_theme()` once. It switches the app to ttk's `clam` theme, recolours the standard ttk widgets and the Text, Listbox and Menu defaults, and sets a modern UI font where one is available:

```python
from flextabs import apply_app_theme

palette = apply_app_theme(root, "dark")  # "light", "dark" or a Palette
tab_manager = TabManager(root, tab_configs, theme="dark")
```

Switch at runtime with `tab_manager.set_theme("light")`. Widgets created after `apply_app_theme()` use the new Text/Listbox/Menu colours; existing ones keep theirs.

**Custom colours:** start from a preset and change what you need. Give it its own name.

```python
from dataclasses import replace
from flextabs import LIGHT

brand = replace(LIGHT, name="brand", accent="#7c3aed")
TabManager(root, tab_configs, theme=brand)
```

`Palette` fields: `surface` (content and selected tab), `bg` (sidebar, toolbar and tab bar), `hover`, `selected`, `border`, `text`, `text_muted`, `accent`, `on_accent`, `tooltip_bg`, `tooltip_fg`, `info`, `success`, `warning`, `error` and `dark`.

**Fonts:** `apply_fonts(root)` points Tk's named fonts at the first available modern UI font (Ubuntu Sans, Cantarell, Inter, Noto Sans, ...) on X11, and does nothing on Windows and macOS, which already use the system font. Pass `family="..."` and `size=...` to choose, or `font_family=None` to `apply_app_theme()` to keep your fonts.

To style the notebook yourself instead, pass a style name in `notebook_config={"style": "My.TNotebook"}`; the internal notebook is also available as `tab_manager.notebook`.

## Opener Types

All openers accept these options in `opener_config`:

```python
{
    "show_icons": True,           # Show icons
    "icon_size": (16, 16),        # Icon size
    "icon_position": "left",      # "left", "right", "top", "bottom"
    "use_fallback_icons": False,  # Icon for tabs that have none
    "fallback_icon_key": "default",
    "style": {},                  # Extra options for the container ttk.Frame
    "button_style": {},           # Extra options for each ttk.Button
}
```

### Sidebar Opener

```python
opener_config = {
    "position": "left",   # "left" or "right"
    "width": 180,         # Width in pixels
    "title": "Navigation" # Optional heading above the items
}
```

The selected tab's item is highlighted with an accent bar, items for open tabs use full-strength text, and items for closed tabs are muted.

### Toolbar Opener

```python
opener_config = {
    "position": "top",       # "top", "bottom", "left", "right"
    "layout": "horizontal",  # "horizontal" or "vertical"
}
```

### Menu Opener

```python
opener_config = {"menu_title": "Tabs"}  # Cascade title in the window's menubar
```

Menu items show icons as images. If FlexTabs created the menubar, it removes it again once its last menu is gone.

## Closing Tabs

`close_button_style` controls the mouse:

- `"button"`: a close glyph appears on the hovered and the selected tab (right-click also closes). Tabs that are not closable show a small lock instead.
- `"right_click"` (default), `"double_click"` or `"both"`

`close_mode` controls which tab a right-click or double-click closes:

- `"active_only"`: only the selected tab
- `"any_visible"`: the tab under the pointer
- `"both"`: the selected tab, or any tab with Ctrl held

`close_confirmation=True` asks before closing, using `close_confirmation_type` `"yesno"`, `"warning"` or `"info"`. A tab's own `on_tab_close()` can also refuse.

## Keyboard Shortcuts

Built in (when `enable_keyboard_shortcuts=True`):

- `Ctrl+W`: close the selected tab
- `Ctrl+Tab` / `Ctrl+Shift+Tab`: next / previous tab
- `Ctrl+1` to `Ctrl+9`: select a tab by position

Each tab can also have its own shortcut that opens it, `keyboard_shortcut="<Control-comma>"`.

Shortcuts are added alongside your app's own bindings and removed precisely when a tab or the manager goes away. When several tab managers share a window, a shortcut goes to the manager that contains keyboard focus, or else to the one used most recently.

## Event Callbacks

```python
tab_manager.on_tab_opened = lambda tab_id: print("opened", tab_id)
tab_manager.on_tab_closed = lambda tab_id: print("closed", tab_id)
tab_manager.on_tab_switched = lambda new_id, old_id: print(old_id, "->", new_id)
tab_manager.on_tab_error = lambda tab_id, error: print("error in", tab_id, error)
```

If a callback raises, the error goes to `on_tab_error` and the operation still counts as done; for example `open_tab()` still returns True. Callbacks are not called while the manager is being destroyed.

## Runtime Management

```python
# Open, select and close
tab_manager.open_tab("settings")
tab_manager.select_tab("home")        # opens it if needed
tab_manager.close_tab("settings")
tab_manager.close_all_tabs()          # returns the number closed

# Query
tab_manager.is_tab_open("settings")
tab_manager.get_open_tabs()           # ["home", ...]
tab_manager.get_current_tab()         # selected tab ID, or None
tab_manager.get_tab_index("home")     # current position in the notebook
tab_manager.get_tab_content("home")   # the TabContent instance

# Change configuration
tab_manager.add_tab_config(TabConfig("reports", "Reports", ReportsTab, icon="trending"))
tab_manager.remove_tab_config("reports")
tab_manager.set_close_mode("any_visible")
tab_manager.set_theme("dark")

# Icons
tab_manager.set_notebook_icon_settings(show_icons=True, icon_size=(18, 18))
tab_manager.set_opener_icon_settings(icon_position="top")
tab_manager.refresh_tab_icons()       # reload image files after they change
```

## Notifications and Tooltips

```python
tab_manager.show_notification("Settings saved", toast_type="success", duration=3000)
```

Toasts are cards with a status icon in the palette's colours. `toast_type` is `"info"`, `"success"`, `"warning"` or `"error"`. For more control use `ToastNotification.show(parent, message, duration, toast_type, position, mode)`, where `position` is `"top-right"`, `"bottom-right"`, `"top-left"` or `"bottom-left"`, and `mode` is `"stacked"` (several at once) or `"queued"` (one after another).

Opener items show the tab's `tooltip`. You can add the same tooltips to any widget with `TooltipWidget(widget, "text")`.

## Error Handling and Logging

Errors raised by your tab content and callbacks are caught. They go to `on_tab_error` if you set it; otherwise FlexTabs shows an error toast and logs the error with its traceback. The last error per tab is kept in `tab_manager.tab_states[tab_id]["last_error"]`.

FlexTabs logs through the standard `logging` module under the `flextabs` logger:

```python
import logging
logging.getLogger("flextabs").setLevel(logging.WARNING)
```

## Examples

### Unsaved changes

```python
from tkinter import messagebox


class EditorTab(TabContent):
    def setup_content(self):
        self.modified = False
        self.text = tk.Text(self.frame, wrap="word")
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.bind("<<Modified>>", self.on_modified)

    def on_modified(self, event):
        self.modified = self.text.edit_modified()

    def on_tab_close(self) -> bool:
        if not self.modified:
            return True
        answer = messagebox.askyesnocancel(
            "Unsaved changes", "Save before closing?", parent=self.frame
        )
        if answer is None:  # Cancel
            return False
        if answer:
            self.save()
        return True

    def save(self):
        self.get_manager().show_notification("Saved", "success")
```

### Tabs created at runtime

```python
counter = 0


def new_document():
    global counter
    counter += 1
    tab_id = f"doc_{counter}"
    tab_manager.add_tab_config(
        TabConfig(tab_id, f"Document {counter}", EditorTab, icon="file-text")
    )
    tab_manager.open_tab(tab_id)
```

### A whole app in one theme

```python
import tkinter as tk

from flextabs import TabManager, apply_app_theme, enable_dpi_awareness

enable_dpi_awareness()  # sharp rendering on high-DPI Windows screens
root = tk.Tk()
apply_app_theme(root, "light")

tab_manager = TabManager(
    root, tab_configs, theme="light", close_button_style="button",
    opener_config={"title": "WORKSPACE"},
)
tab_manager.pack(fill=tk.BOTH, expand=True)
root.mainloop()
```

### Migrating from ttk.Notebook

```python
# Before
notebook = ttk.Notebook(parent)
frame = ttk.Frame(notebook)
notebook.add(frame, text="My Tab")

# After
class MyTab(TabContent):
    def setup_content(self):
        ...  # build the UI in self.frame

tab_manager = TabManager(parent, [TabConfig("my_tab", "My Tab", MyTab)])
```

## Platform Notes

- **Built-in icons need Tk 9**, which renders SVG natively. With an older Tk, built-in and fallback icons are not shown; image files and text icons still work.
- **Linux fonts:** Tk builds without Xft (where `root.tk.call("::tk::pkgconfig", "get", "fontsystem")` returns `x11`) can only use legacy X11 fonts, so text looks rough and `apply_fonts()` finds no modern font. Distribution packages (`python3-tk`) and conda-forge use Xft; some standalone Python builds do not.
- **Windows high-DPI screens:** call `flextabs.enable_dpi_awareness()` before creating `tk.Tk()`. Otherwise Windows scales the window as a bitmap and it looks blurry.

## What's New in 0.3.0

**New**

- Built-in icon set, `IconManager.get_builtin_icon()`, `render()`, `register_icon()` and `builtin_names()`
- Themes: `theme=` argument, `set_theme()`, `Palette`, `LIGHT`, `DARK`, `apply_app_theme()` and `apply_fonts()`
- `close_button_style="button"` with close and lock glyphs on tabs
- `get_tab_index()`, `enable_dpi_awareness()`, the `flextabs-demo` command and type information (`py.typed`)

**Changed** (check these when upgrading)

- Python 3.15 or newer is required
- The default look is now the flat `"auto"` theme; pass `theme=None` for the previous plain ttk look
- Tabs without an icon no longer get a fallback icon by default (`use_fallback_icons` and `use_notebook_fallback_icons` are now False); fallback icons map to built-in icon names, and `IconManager.get_fallback_text()` returns an icon name
- Icons are classified as image files by path separator or image extension rather than by length
- Tabs that are not closable no longer get a `•` prefix or grey styling
- Sidebar: default width is 180 (was 150) and the title is shown at the top
- Themed opener buttons use the ttk `selected` state for the selected tab and `alternate` for open tabs; the plain look still marks open tabs with `selected`
- `get_current_tab()` reads the notebook's live selection
- Destroying the manager runs every open tab's `cleanup()` and does not call the `on_tab_*` callbacks
- Errors are logged with `logging` instead of printed
- `ToastNotification.COLORS` only lists the status accent colours; toasts take their colours from the palette
- `TooltipWidget` uses `TkDefaultFont` and wraps at 280 pixels by default

**Fixed**

- Shortcuts no longer replace your app's bindings or each other, and removed tabs lose theirs
- Selecting tabs after they were reordered, image icons with more than one Tk root, menus with dict icons, the menu opener leaving menus behind, callback errors failing `open_tab()`/`close_tab()`, and several smaller issues

## Development

The project uses [uv](https://docs.astral.sh/uv/):

```bash
uv sync --group dev                     # create .venv with the dev tools
uv run pytest                           # run the tests (needs a display)
xvfb-run -a uv run pytest               # ... or with a virtual display
uv run ruff check flextabs tests        # lint
uv run ruff format flextabs tests       # format
```

The tests run on GitHub Actions for every push to `main` and every pull request.

**Releasing:** set `__version__` in `flextabs/__init__.py`, then publish a GitHub release tagged `v<version>` (for example `v0.3.0`). The publish workflow runs the tests, builds and checks the package, verifies the tag matches the version, and uploads to PyPI. Running the workflow by hand from the Actions tab does a dry run without uploading.

## API Reference

The full API reference is at [ms-32154.github.io/flextabs](https://ms-32154.github.io/flextabs/) (source: [docs/index.md](docs/index.md)).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome. Please open an issue to discuss larger changes, and include tests with pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Run `uv run pytest` and `uv run ruff check flextabs tests`
4. Commit your changes and open a pull request

When reporting a problem, please include your Python and Tk versions, operating system, a minimal example and the full traceback.

---

**FlexTabs** – Extending `ttk.Notebook` for powerful and flexible tab management in Tkinter.

© 2025 MS-32154. All rights reserved.
