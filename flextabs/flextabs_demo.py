import tkinter as tk
from tkinter import ttk, messagebox
import os
import tempfile
import random

# Import your tab manager components
from .tab_manager import TabManager
from .tab_base import TabConfig, TabContent
from .enums import CloseMode, CloseConfirmationType


def create_demo_icons():
    """Create compact demo icon files to show difference from emoji."""
    icons_dir = tempfile.mkdtemp(prefix="tab_icons_")
    try:
        from PIL import Image, ImageDraw

        # Opener icons (rectangular, for buttons)
        opener_configs = [
            ("home_opener.png", "#3498db", "rect"),
            ("settings_opener.png", "#95a5a6", "gear"),
            ("data_opener.png", "#9b59b6", "chart"),
            ("tools_opener.png", "#f39c12", "tool"),
        ]

        # Tab icons (square, for notebook tabs)
        tab_configs = [
            ("home_tab.png", "#2980b9", "house"),
            ("settings_tab.png", "#7f8c8d", "cog"),
            ("data_tab.png", "#8e44ad", "graph"),
            ("tools_tab.png", "#e67e22", "wrench"),
        ]

        def draw_simple_icon(draw, size, icon_type, color):
            w, h = size
            if icon_type == "rect":
                draw.rectangle(
                    [2, 2, w - 3, h - 3], outline="white", width=1, fill=color
                )
            elif icon_type in ["gear", "cog"]:
                # Simple gear shape
                draw.ellipse([3, 3, w - 4, h - 4], outline="white", width=1, fill=color)
                draw.rectangle([w // 2 - 1, 1, w // 2 + 1, h - 2], fill="white")
                draw.rectangle([1, h // 2 - 1, w - 2, h // 2 + 1], fill="white")
            elif icon_type in ["chart", "graph"]:
                # Simple bar chart
                draw.rectangle([2, h - 4, 5, h - 1], fill="white")
                draw.rectangle([6, h - 7, 9, h - 1], fill="white")
                draw.rectangle([10, h - 5, 13, h - 1], fill="white")
            elif icon_type in ["tool", "wrench"]:
                # Simple tool shape
                draw.rectangle([3, 2, 6, h - 3], fill="white")
                draw.rectangle([2, h - 5, 7, h - 2], fill="white")
            else:
                draw.rectangle([2, 2, w - 3, h - 3], outline="white", width=1)

        # Create opener icons (20x16)
        for filename, color, shape in opener_configs:
            img = Image.new("RGB", (20, 16), color)
            draw = ImageDraw.Draw(img)
            draw_simple_icon(draw, (20, 16), shape, color)
            img.save(os.path.join(icons_dir, filename))

        # Create tab icons (16x16)
        for filename, color, shape in tab_configs:
            img = Image.new("RGB", (16, 16), color)
            draw = ImageDraw.Draw(img)
            draw_simple_icon(draw, (16, 16), shape, color)
            img.save(os.path.join(icons_dir, filename))

        print(f"📁 Created demo icons in: {icons_dir}")
        return icons_dir

    except ImportError:
        print("⚠️ PIL not available, using emoji icons only")
        return None


# Sample tab content classes
class HomeTab(TabContent):
    def setup_content(self):
        ttk.Label(
            self.frame,
            text="🏠 Welcome to Tab Manager Demo",
            font=("Arial", 16, "bold"),
        ).pack(pady=20)

        info = """Features demonstrated:
• Multiple opener types (sidebar, toolbar, menu)
• Icon support (emoji + image files)
• Keyboard shortcuts (Ctrl+1-9, Ctrl+W, Ctrl+Tab)
• Close confirmation dialogs
• Toast notifications
• Runtime tab management"""

        ttk.Label(self.frame, text=info, justify="left").pack(pady=10)

        # Demo buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=20)

        ttk.Button(
            btn_frame,
            text="🎉 Success Toast",
            command=lambda: self.show_toast("success"),
        ).pack(side="left", padx=2)
        ttk.Button(
            btn_frame,
            text="⚠️ Warning Toast",
            command=lambda: self.show_toast("warning"),
        ).pack(side="left", padx=2)
        ttk.Button(
            btn_frame, text="❌ Error Toast", command=lambda: self.show_toast("error")
        ).pack(side="left", padx=2)

        btn_frame2 = ttk.Frame(self.frame)
        btn_frame2.pack(pady=5)

        ttk.Button(
            btn_frame2, text="⭐ Add Dynamic Tab", command=self.add_dynamic_tab
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame2, text="🗑️ Remove Random Tab", command=self.remove_random_tab
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame2, text="📊 Toast Queue Demo", command=self.toast_queue_demo
        ).pack(side="left", padx=5)

    def show_toast(self, toast_type):
        manager = self.get_manager()
        if manager:
            messages = {
                "success": "✅ Operation completed successfully!",
                "warning": "⚠️ This is a warning message",
                "error": "❌ An error occurred during processing",
                "info": "ℹ️ Here's some information for you",
            }
            manager.show_notification(
                messages.get(toast_type, "Demo notification"), toast_type
            )

    def add_dynamic_tab(self):
        manager = self.get_manager()
        if manager:
            tab_id = f"dynamic_{random.randint(1000, 9999)}"
            icons = ["⭐", "🚀", "💎", "🎯", "🔥", "⚡", "🎨", "🎪"]
            config = TabConfig(
                id=tab_id,
                title=f"Dynamic {tab_id[-4:]}",
                content_class=DataTab,
                icon=random.choice(icons),
                tooltip=f"Dynamically created tab {tab_id[-4:]}",
            )
            manager.add_tab_config(config)
            manager.open_tab(tab_id)
            manager.show_notification(f"Created tab: {config.title}", "success")

    def remove_random_tab(self):
        manager = self.get_manager()
        if manager:
            dynamic_tabs = [
                tid for tid in manager.tab_configs.keys() if tid.startswith("dynamic_")
            ]
            if dynamic_tabs:
                tab_id = random.choice(dynamic_tabs)
                title = manager.tab_configs[tab_id].title
                manager.remove_tab_config(tab_id)
                manager.show_notification(f"Removed tab: {title}", "info")
            else:
                manager.show_notification("No dynamic tabs to remove", "warning")

    def toast_queue_demo(self):
        manager = self.get_manager()
        if manager:
            toasts = [
                ("Starting process...", "info"),
                ("Processing data...", "info"),
                ("Warning: Large dataset", "warning"),
                ("Process completed!", "success"),
            ]
            for i, (msg, toast_type) in enumerate(toasts):
                # Stagger the toasts
                manager.after(
                    i * 800, lambda m=msg, t=toast_type: manager.show_notification(m, t)
                )


class SettingsTab(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text="⚙️ Settings Panel", font=("Arial", 14, "bold")).pack(
            pady=10
        )

        # Close mode settings
        mode_frame = ttk.LabelFrame(self.frame, text="Close Mode")
        mode_frame.pack(fill="x", padx=10, pady=5)

        self.close_mode_var = tk.StringVar(value="active_only")
        for mode in ["active_only", "any_visible", "both"]:
            ttk.Radiobutton(
                mode_frame,
                text=mode.replace("_", " ").title(),
                variable=self.close_mode_var,
                value=mode,
                command=self.update_close_mode,
            ).pack(anchor="w")

        # Icon settings
        icon_frame = ttk.LabelFrame(self.frame, text="Icon Settings")
        icon_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            icon_frame, text="Toggle Notebook Icons", command=self.toggle_icons
        ).pack(pady=2)
        ttk.Button(icon_frame, text="Refresh Icons", command=self.refresh_icons).pack(
            pady=2
        )
        ttk.Button(
            icon_frame, text="🎨 Icon vs Emoji Demo", command=self.demo_icon_types
        ).pack(pady=2)

        # Dynamic actions
        action_frame = ttk.LabelFrame(self.frame, text="Dynamic Actions")
        action_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            action_frame, text="🎲 Randomize Tab Order", command=self.randomize_tabs
        ).pack(pady=2)
        ttk.Button(
            action_frame, text="📢 Broadcast Message", command=self.broadcast_message
        ).pack(pady=2)

        # Close button
        ttk.Button(
            self.frame,
            text="Close This Tab",
            command=lambda: self.get_manager().close_tab(self.tab_id),
        ).pack(pady=10)

    def update_close_mode(self):
        manager = self.get_manager()
        if manager:
            manager.set_close_mode(self.close_mode_var.get())

    def toggle_icons(self):
        manager = self.get_manager()
        if manager:
            current = manager.show_notebook_icons
            manager.set_notebook_icon_settings(show_icons=not current)

    def refresh_icons(self):
        manager = self.get_manager()
        if manager:
            manager.refresh_tab_icons()
            manager.show_notification("Icons refreshed! 🔄", "success")

    def demo_icon_types(self):
        manager = self.get_manager()
        if manager:
            # Show difference between emoji and file icons
            manager.show_notification(
                "Emoji icons: 🎨 vs File icons: PNG", "info", 3000
            )

    def randomize_tabs(self):
        manager = self.get_manager()
        if manager:
            open_tabs = manager.get_open_tabs()
            if len(open_tabs) > 1:
                current = manager.get_current_tab()
                random.shuffle(open_tabs)
                # Close all and reopen in random order
                for tab_id in open_tabs:
                    if manager.tab_configs[tab_id].closable:
                        manager.close_tab(tab_id)

                for tab_id in open_tabs[:3]:  # Reopen first 3
                    manager.open_tab(tab_id)

                manager.show_notification("Tabs randomized! 🎲", "success")
            else:
                manager.show_notification("Need more tabs to randomize", "warning")

    def broadcast_message(self):
        manager = self.get_manager()
        if manager:
            messages = [
                "📢 System broadcast: All tabs updated",
                "🔄 Configuration synchronized",
                "✨ Performance optimized",
            ]
            msg = random.choice(messages)
            manager.show_notification(msg, "info", 2500)


class DataTab(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text="📊 Data Viewer", font=("Arial", 14, "bold")).pack(
            pady=10
        )

        # Create treeview for data display
        columns = ("Name", "Type", "Value")
        tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=8)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        # Sample data
        data = [
            (
                "tabs_open",
                "int",
                str(
                    len(self.get_manager().get_open_tabs()) if self.get_manager() else 0
                ),
            ),
            (
                "current_tab",
                "str",
                self.get_manager().get_current_tab() if self.get_manager() else "None",
            ),
            ("demo_status", "str", "Running"),
            ("features", "list", "Icons, Shortcuts, Notifications"),
        ]

        for item in data:
            tree.insert("", "end", values=item)

        tree.pack(pady=10, padx=10, fill="both", expand=True)

        # Refresh button
        ttk.Button(
            self.frame, text="Refresh Data", command=lambda: self.refresh_data(tree)
        ).pack(pady=5)

    def refresh_data(self, tree):
        for item in tree.get_children():
            tree.delete(item)

        manager = self.get_manager()
        data = [
            ("tabs_open", "int", str(len(manager.get_open_tabs()) if manager else 0)),
            ("current_tab", "str", manager.get_current_tab() if manager else "None"),
            ("timestamp", "str", str(tk.Tk().tk.call("clock", "seconds"))),
            ("close_mode", "str", str(manager.get_close_mode()) if manager else "None"),
        ]

        for item in data:
            tree.insert("", "end", values=item)


class HelpTab(TabContent):
    def setup_content(self):
        ttk.Label(
            self.frame, text="❓ Help & Shortcuts", font=("Arial", 14, "bold")
        ).pack(pady=10)

        help_text = """Keyboard Shortcuts:
• Ctrl+1-9: Switch to tab by number
• Ctrl+W: Close current tab
• Ctrl+Tab: Next tab
• Ctrl+Shift+Tab: Previous tab
• F1: Open help (this tab)

Mouse Controls:
• Right-click tab: Close tab
• Double-click tab: Close tab (if enabled)

Features:
• Multiple opener types (sidebar/toolbar/menu)
• Smart icon support (emoji + image files)
• Close confirmation dialogs
• Toast notifications
• Runtime tab management
• Keyboard shortcuts
• Tooltips and styling"""

        text_widget = tk.Text(self.frame, wrap="word", height=15, width=50)
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")

        scrollbar = ttk.Scrollbar(
            self.frame, orient="vertical", command=text_widget.yview
        )
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

    def on_tab_close(self):
        return messagebox.askyesno(
            "Close Help", "Are you sure you want to close the help tab?"
        )


class UnclosableTab(TabContent):
    def setup_content(self):
        ttk.Label(self.frame, text="🔒 System Tab", font=("Arial", 14, "bold")).pack(
            pady=20
        )
        ttk.Label(
            self.frame,
            text="This tab cannot be closed.\nIt demonstrates unclosable tab functionality.",
            justify="center",
        ).pack(pady=10)


def create_demo_app():
    root = tk.Tk()
    root.title("Tab Manager Comprehensive Demo")
    root.geometry("900x600")

    # Configure ttk style
    style = ttk.Style()
    style.theme_use("clam")

    # Create demo icons
    icons_dir = create_demo_icons()

    # Create tab configurations with mixed icon types
    tab_configs = [
        TabConfig(
            id="home",
            title="Home",
            content_class=HomeTab,
            # Mix emoji (opener) and file icon (tab) if available
            icon=(
                {
                    "opener": "🏠",  # Emoji for opener buttons
                    "tab": (
                        os.path.join(icons_dir, "home_tab.png") if icons_dir else "🏠"
                    ),
                }
                if icons_dir
                else "🏠"
            ),
            tooltip="Home dashboard with emoji/file icon demo",
            keyboard_shortcut="<F2>",
        ),
        TabConfig(
            id="settings",
            title="Settings",
            content_class=SettingsTab,
            icon=(
                {
                    "opener": (
                        os.path.join(icons_dir, "settings_opener.png")
                        if icons_dir
                        else "⚙️"
                    ),
                    "tab": "⚙️",  # Emoji for tab, file for opener
                }
                if icons_dir
                else "⚙️"
            ),
            tooltip="Settings with file/emoji icon demo",
            keyboard_shortcut="<F3>",
        ),
        TabConfig(
            id="data",
            title="Data",
            content_class=DataTab,
            icon=(
                {
                    "opener": "📊",
                    "tab": (
                        os.path.join(icons_dir, "data_tab.png") if icons_dir else "📊"
                    ),
                }
                if icons_dir
                else "📊"
            ),
            tooltip="Data viewer with dynamic updates",
            keyboard_shortcut="<F4>",
        ),
        TabConfig(
            id="help",
            title="Help",
            content_class=HelpTab,
            icon="❓",  # Pure emoji for both contexts
            tooltip="Help and keyboard shortcuts",
            keyboard_shortcut="<F1>",
        ),
        TabConfig(
            id="system",
            title="System",
            content_class=UnclosableTab,
            icon=(
                {
                    "opener": (
                        os.path.join(icons_dir, "tools_opener.png")
                        if icons_dir
                        else "🔒"
                    ),
                    "tab": "🔒",
                }
                if icons_dir
                else "🔒"
            ),
            tooltip="System tab (unclosable) - file icon in opener",
            closable=False,
        ),
    ]

    # Create main container
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Demo selector frame
    demo_frame = ttk.LabelFrame(main_frame, text="Demo Configuration")
    demo_frame.pack(fill="x", pady=(0, 10))

    # Opener type selection
    opener_var = tk.StringVar(value="sidebar")
    ttk.Label(demo_frame, text="Opener Type:").pack(side="left", padx=5)
    for opener_type in ["sidebar", "toolbar", "menu"]:
        ttk.Radiobutton(
            demo_frame, text=opener_type.title(), variable=opener_var, value=opener_type
        ).pack(side="left", padx=2)

    # Create button
    def create_tab_manager():
        # Clear existing widgets
        for widget in tab_container.winfo_children():
            widget.destroy()

        # Opener configurations
        opener_configs = {
            "sidebar": {"position": "left", "width": 150, "title": "Navigation"},
            "toolbar": {"position": "top", "layout": "horizontal"},
            "menu": {"menu_title": "Tabs"},
        }

        # Create tab manager
        manager = TabManager(
            parent=tab_container,
            tab_configs=tab_configs,
            opener_type=opener_var.get(),
            opener_config=opener_configs[opener_var.get()],
            close_confirmation=True,
            close_confirmation_type=CloseConfirmationType.YESNO,
            close_mode=CloseMode.ACTIVE_ONLY,
            enable_keyboard_shortcuts=True,
            show_notebook_icons=True,
            use_notebook_fallback_icons=True,
        )

        # Setup event callbacks with toasts
        def on_tab_opened(tab_id):
            print(f"Tab opened: {tab_id}")
            if tab_id.startswith("dynamic"):
                manager.show_notification(f"🚀 Opened: {tab_id[-4:]}", "success", 1500)

        def on_tab_closed(tab_id):
            print(f"Tab closed: {tab_id}")
            manager.show_notification(
                f"👋 Closed: {manager.tab_configs.get(tab_id, type('', (), {'title': tab_id})).title}",
                "info",
                1500,
            )

        def on_tab_switched(new_tab, old_tab):
            if new_tab and old_tab:
                print(f"Switched from {old_tab} to {new_tab}")
                # Show subtle switch notification occasionally
                if random.random() < 0.3:  # 30% chance
                    manager.after(
                        200,
                        lambda: manager.show_notification(
                            f"📋 Active: {manager.tab_configs[new_tab].title}",
                            "info",
                            1000,
                        ),
                    )

        manager.on_tab_opened = on_tab_opened
        manager.on_tab_closed = on_tab_closed
        manager.on_tab_switched = on_tab_switched

        manager.pack(fill="both", expand=True)

        # Auto-open home tab
        root.after(100, lambda: manager.open_tab("home"))

    ttk.Button(demo_frame, text="Create Tab Manager", command=create_tab_manager).pack(
        side="right", padx=5
    )

    # Tab container
    tab_container = ttk.Frame(main_frame)
    tab_container.pack(fill="both", expand=True)

    # Initial setup
    create_tab_manager()

    return root


if __name__ == "__main__":
    # Create and run the demo
    app = create_demo_app()

    print("Tab Manager Demo Started!")
    print("Try these features:")
    print("• Switch opener types using radio buttons")
    print("• Use keyboard shortcuts (F1-F4, Ctrl+W, Ctrl+Tab)")
    print("• Right-click tabs to close them")
    print("• Try closing the unclosable 'System' tab")
    print("• Add dynamic tabs from the Home tab")
    print("• Change settings in the Settings tab")

    app.mainloop()
