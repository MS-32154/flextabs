#!/usr/bin/env python3
"""
FlexTabs Complete Feature Demo
=============================

This demo showcases ALL features of the FlexTabs library:
- Different opener types (toolbar, sidebar, menu)
- Various tab configurations and behaviors
- Close modes and confirmation dialogs
- Keyboard shortcuts and event handling
- Runtime tab management
- Toast notifications and error handling
- Custom tab content with advanced features

Run this script to see FlexTabs in action!
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
from datetime import datetime

# Import FlexTabs components
from .tab_manager import TabManager
from .tab_base import TabConfig, TabContent
from .enums import CloseMode, CloseConfirmationType


# =============================================================================
# CUSTOM TAB CONTENT CLASSES - Showcase different content types
# =============================================================================


class DashboardTab(TabContent):
    """Main dashboard with system info and controls."""

    def setup_content(self):
        # Header
        header = ttk.Frame(self.frame)
        header.pack(fill="x", padx=10, pady=5)

        ttk.Label(header, text="📊 Dashboard", font=("Arial", 16, "bold")).pack(
            side="left"
        )

        ttk.Label(
            header,
            text=f"Started: {datetime.now().strftime('%H:%M:%S')}",
            foreground="gray",
        ).pack(side="right")

        # Stats section
        stats_frame = ttk.LabelFrame(self.frame, text="System Stats", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)

        self.stats_text = tk.Text(
            stats_frame, height=6, width=50, background="#f8f9fa", relief="flat"
        )
        self.stats_text.pack(fill="x")

        # Control buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="🔄 Refresh Stats", command=self.refresh_stats).pack(
            side="left", padx=(0, 5)
        )

        ttk.Button(
            btn_frame, text="📝 Open Text Editor", command=self.open_text_editor
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame, text="📊 Open Data Viewer", command=self.open_data_viewer
        ).pack(side="left", padx=5)

        # Initialize stats
        self.refresh_stats()

    def refresh_stats(self):
        """Update dashboard statistics."""
        manager = self.get_manager()
        if not manager:
            return

        open_tabs = manager.get_open_tabs()
        current_tab = manager.get_current_tab()

        stats = f"""
📈 Active Tabs: {len(open_tabs)}
🎯 Current Tab: {current_tab or 'None'}
📁 Open Tabs: {', '.join(open_tabs) if open_tabs else 'None'}
🕒 Last Update: {datetime.now().strftime('%H:%M:%S')}
💾 Memory Usage: {random.randint(45, 78)}% (simulated)
⚡ Performance: {'Excellent' if len(open_tabs) < 5 else 'Good' if len(open_tabs) < 8 else 'Fair'}
        """.strip()

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)

    def open_text_editor(self):
        """Open text editor tab dynamically."""
        manager = self.get_manager()
        if manager and not manager.is_tab_open("text_editor"):
            manager.open_tab("text_editor")

    def open_data_viewer(self):
        """Open data viewer tab dynamically."""
        manager = self.get_manager()
        if manager and not manager.is_tab_open("data_viewer"):
            manager.open_tab("data_viewer")

    def on_tab_focus(self):
        """Refresh stats when tab gains focus."""
        self.refresh_stats()


class TextEditorTab(TabContent):
    """Advanced text editor with file operations."""

    def setup_content(self):
        # Toolbar
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill="x", padx=5, pady=2)

        ttk.Button(toolbar, text="📂 Open", command=self.open_file, width=8).pack(
            side="left", padx=2
        )
        ttk.Button(toolbar, text="💾 Save", command=self.save_file, width=8).pack(
            side="left", padx=2
        )
        ttk.Button(toolbar, text="🆕 New", command=self.new_file, width=8).pack(
            side="left", padx=2
        )

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5)

        ttk.Button(toolbar, text="🔍 Find", command=self.find_text, width=8).pack(
            side="left", padx=2
        )

        # Status bar for file info
        self.status_var = tk.StringVar(value="Ready | Lines: 0 | Characters: 0")
        status_bar = ttk.Label(
            toolbar, textvariable=self.status_var, foreground="gray", font=("Arial", 8)
        )
        status_bar.pack(side="right", padx=5)

        # Text editor with scrollbar
        text_frame = ttk.Frame(self.frame)
        text_frame.pack(fill="both", expand=True, padx=5, pady=2)

        self.text_widget = tk.Text(
            text_frame,
            wrap="word",
            undo=True,
            font=("Consolas", 11),
            background="#fefefe",
        )
        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.text_widget.yview
        )
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        self.text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind events for real-time stats
        self.text_widget.bind("<KeyRelease>", self.update_stats)
        self.text_widget.bind("<Button-1>", self.update_stats)

        # Sample content
        sample_text = """# FlexTabs Text Editor Demo

Welcome to the FlexTabs text editor! This tab demonstrates:

✨ File operations (Open, Save, New)
📊 Real-time statistics 
🔍 Text search functionality
🎨 Syntax highlighting ready
⌨️  Keyboard shortcuts
📝 Undo/Redo support

Try typing some text and watch the status bar update!

## Features Available:
- Full text editing capabilities
- File management
- Real-time character/line counting
- Find functionality
- Auto-save capabilities (coming soon)

Feel free to modify this text and explore the features!
"""
        self.text_widget.insert(1.0, sample_text)
        self.current_file = None
        self.modified = False
        self.update_stats()

    def update_stats(self, event=None):
        """Update status bar with current document stats."""
        content = self.text_widget.get(1.0, tk.END)
        lines = len(content.split("\n")) - 1  # Subtract 1 for extra newline
        chars = len(content) - 1  # Subtract 1 for extra newline
        words = len([word for word in content.split() if word])

        cursor_pos = self.text_widget.index(tk.INSERT)

        filename = self.current_file.split("/")[-1] if self.current_file else "Untitled"
        status = f"{filename} {'*' if self.modified else ''} | Lines: {lines} | Words: {words} | Chars: {chars} | Pos: {cursor_pos}"
        self.status_var.set(status)

        self.modified = True

    def open_file(self):
        """Open a file dialog and load file content."""
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                self.text_widget.delete(1.0, tk.END)
                self.text_widget.insert(1.0, content)
                self.current_file = file_path
                self.modified = False
                self.update_stats()

                manager = self.get_manager()
                if manager:
                    manager.show_notification(
                        f"📂 Opened: {file_path.split('/')[-1]}", "success"
                    )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def save_file(self):
        """Save current content to file."""
        if not self.current_file:
            self.current_file = filedialog.asksaveasfilename(
                title="Save File",
                defaultextension=".txt",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("Python files", "*.py"),
                    ("All files", "*.*"),
                ],
            )

        if self.current_file:
            try:
                content = self.text_widget.get(1.0, tk.END)
                with open(self.current_file, "w", encoding="utf-8") as file:
                    file.write(content)
                self.modified = False
                self.update_stats()

                manager = self.get_manager()
                if manager:
                    manager.show_notification(
                        f"💾 Saved: {self.current_file.split('/')[-1]}", "success"
                    )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def new_file(self):
        """Create a new file."""
        if self.modified:
            if not messagebox.askyesno(
                "New File", "Current file has unsaved changes. Continue?"
            ):
                return

        self.text_widget.delete(1.0, tk.END)
        self.current_file = None
        self.modified = False
        self.update_stats()

    def find_text(self):
        """Simple find dialog."""
        search_term = tk.simpledialog.askstring("Find", "Enter text to find:")
        if search_term:
            # Simple find implementation
            content = self.text_widget.get(1.0, tk.END)
            if search_term in content:
                start_pos = content.find(search_term)
                if start_pos != -1:
                    line = content[:start_pos].count("\n") + 1
                    col = start_pos - content.rfind("\n", 0, start_pos) - 1
                    self.text_widget.mark_set(tk.INSERT, f"{line}.{col}")
                    self.text_widget.see(tk.INSERT)

                    manager = self.get_manager()
                    if manager:
                        manager.show_notification(f"🔍 Found: '{search_term}'", "info")
            else:
                manager = self.get_manager()
                if manager:
                    manager.show_notification(
                        f"❌ Not found: '{search_term}'", "warning"
                    )

    def on_tab_close(self):
        """Ask to save before closing if modified."""
        if self.modified:
            result = messagebox.askyesnocancel(
                "Save Changes", "The document has unsaved changes. Save before closing?"
            )
            if result is True:  # Yes - save and close
                self.save_file()
                return True
            elif result is False:  # No - close without saving
                return True
            else:  # Cancel - don't close
                return False
        return True


class DataViewerTab(TabContent):
    """Data visualization and analysis tab."""

    def setup_content(self):
        # Control panel
        control_frame = ttk.LabelFrame(self.frame, text="Data Controls", padding=5)
        control_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            control_frame, text="📊 Generate Data", command=self.generate_data
        ).pack(side="left", padx=2)
        ttk.Button(control_frame, text="📈 Show Chart", command=self.show_chart).pack(
            side="left", padx=2
        )
        ttk.Button(control_frame, text="📋 Export CSV", command=self.export_data).pack(
            side="left", padx=2
        )

        # Data display
        data_frame = ttk.LabelFrame(self.frame, text="Data View", padding=5)
        data_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview for tabular data
        columns = ("ID", "Name", "Value", "Category", "Timestamp")
        self.tree = ttk.Treeview(
            data_frame, columns=columns, show="headings", height=10
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            data_frame, orient="vertical", command=self.tree.yview
        )
        h_scrollbar = ttk.Scrollbar(
            data_frame, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Pack widgets
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        data_frame.grid_rowconfigure(0, weight=1)
        data_frame.grid_columnconfigure(0, weight=1)

        # Statistics panel
        stats_frame = ttk.LabelFrame(self.frame, text="Statistics", padding=5)
        stats_frame.pack(fill="x", padx=10, pady=5)

        self.stats_label = ttk.Label(
            stats_frame, text="No data loaded", foreground="gray"
        )
        self.stats_label.pack()

        # Initialize with sample data
        self.data = []
        self.generate_data()

    def generate_data(self):
        """Generate sample data."""
        categories = ["Sales", "Marketing", "Development", "Support", "HR"]
        names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]

        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.data = []

        # Generate new data
        for i in range(random.randint(20, 50)):
            data_point = {
                "id": f"ID{i+1:03d}",
                "name": random.choice(names),
                "value": random.randint(100, 9999),
                "category": random.choice(categories),
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
            self.data.append(data_point)

            # Insert into treeview
            self.tree.insert(
                "",
                "end",
                values=(
                    data_point["id"],
                    data_point["name"],
                    data_point["value"],
                    data_point["category"],
                    data_point["timestamp"],
                ),
            )

        self.update_statistics()

        manager = self.get_manager()
        if manager:
            manager.show_notification(
                f"📊 Generated {len(self.data)} data points", "success"
            )

    def update_statistics(self):
        """Update statistics display."""
        if not self.data:
            self.stats_label.config(text="No data loaded")
            return

        values = [d["value"] for d in self.data]
        categories = [d["category"] for d in self.data]

        avg_value = sum(values) / len(values)
        max_value = max(values)
        min_value = min(values)
        unique_categories = len(set(categories))

        stats_text = (
            f"📊 Records: {len(self.data)} | "
            f"📈 Avg: {avg_value:.1f} | "
            f"⬆️ Max: {max_value} | "
            f"⬇️ Min: {min_value} | "
            f"🏷️ Categories: {unique_categories}"
        )

        self.stats_label.config(text=stats_text)

    def show_chart(self):
        """Show a simple chart (simulation)."""
        if not self.data:
            manager = self.get_manager()
            if manager:
                manager.show_notification("❌ No data to chart", "warning")
            return

        # Simulate chart display
        chart_window = tk.Toplevel(self.frame)
        chart_window.title("Data Chart")
        chart_window.geometry("400x300")

        tk.Label(
            chart_window, text="📊 Data Visualization", font=("Arial", 14, "bold")
        ).pack(pady=20)

        # Simple text-based chart simulation
        chart_text = tk.Text(chart_window, height=10, width=50)
        chart_text.pack(padx=20, pady=10)

        # Create simple ASCII chart
        categories = {}
        for d in self.data:
            cat = d["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(d["value"])

        chart_content = "Data by Category:\n\n"
        for cat, values in categories.items():
            avg_val = sum(values) / len(values)
            bar_length = int(avg_val / 100)  # Scale down for display
            bar = "█" * bar_length
            chart_content += f"{cat:12} | {bar} ({avg_val:.1f})\n"

        chart_text.insert(1.0, chart_content)
        chart_text.config(state="disabled")

    def export_data(self):
        """Export data to CSV."""
        if not self.data:
            manager = self.get_manager()
            if manager:
                manager.show_notification("❌ No data to export", "warning")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )

        if file_path:
            try:
                with open(file_path, "w", newline="") as csvfile:
                    import csv

                    writer = csv.DictWriter(
                        csvfile,
                        fieldnames=["id", "name", "value", "category", "timestamp"],
                    )
                    writer.writeheader()
                    writer.writerows(self.data)

                manager = self.get_manager()
                if manager:
                    manager.show_notification(
                        f"📋 Exported to: {file_path.split('/')[-1]}", "success"
                    )
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export data: {e}")


class SettingsTab(TabContent):
    """Application settings and configuration."""

    def setup_content(self):
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(header_frame, text="⚙️ Settings", font=("Arial", 16, "bold")).pack(
            side="left"
        )

        # Tab Manager Settings
        tab_settings = ttk.LabelFrame(
            self.frame, text="Tab Manager Settings", padding=10
        )
        tab_settings.pack(fill="x", padx=10, pady=5)

        # Close mode setting
        ttk.Label(tab_settings, text="Close Mode:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.close_mode_var = tk.StringVar(value="active_only")
        close_mode_frame = ttk.Frame(tab_settings)
        close_mode_frame.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)

        modes = [
            ("Active Only", "active_only"),
            ("Any Visible", "any_visible"),
            ("Both", "both"),
        ]
        for text, value in modes:
            ttk.Radiobutton(
                close_mode_frame,
                text=text,
                variable=self.close_mode_var,
                value=value,
                command=self.update_close_mode,
            ).pack(side="left", padx=5)

        # Confirmation settings
        ttk.Label(tab_settings, text="Close Confirmation:").grid(
            row=1, column=0, sticky="w", pady=2
        )
        self.confirmation_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            tab_settings,
            text="Enable confirmation dialogs",
            variable=self.confirmation_var,
            command=self.update_confirmation,
        ).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=2)

        # Keyboard shortcuts
        ttk.Label(tab_settings, text="Keyboard Shortcuts:").grid(
            row=2, column=0, sticky="w", pady=2
        )
        self.shortcuts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            tab_settings, text="Enable keyboard shortcuts", variable=self.shortcuts_var
        ).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=2)

        # Theme Settings
        theme_settings = ttk.LabelFrame(self.frame, text="Appearance", padding=10)
        theme_settings.pack(fill="x", padx=10, pady=5)

        ttk.Label(theme_settings, text="Theme:").grid(
            row=0, column=0, sticky="w", pady=2
        )
        self.theme_var = tk.StringVar(value="default")
        theme_combo = ttk.Combobox(
            theme_settings,
            textvariable=self.theme_var,
            values=["default", "clam", "alt", "classic"],
        )
        theme_combo.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=2)
        theme_combo.bind("<<ComboboxSelected>>", self.change_theme)

        # Notification Settings
        notif_settings = ttk.LabelFrame(self.frame, text="Notifications", padding=10)
        notif_settings.pack(fill="x", padx=10, pady=5)

        self.show_notifications_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            notif_settings,
            text="Show toast notifications",
            variable=self.show_notifications_var,
        ).pack(anchor="w")

        self.notification_duration_var = tk.IntVar(value=2000)
        ttk.Label(notif_settings, text="Notification duration (ms):").pack(
            anchor="w", pady=(5, 0)
        )
        ttk.Scale(
            notif_settings,
            from_=1000,
            to=5000,
            orient="horizontal",
            variable=self.notification_duration_var,
            length=200,
        ).pack(anchor="w")

        # Test buttons
        test_frame = ttk.LabelFrame(self.frame, text="Test Features", padding=10)
        test_frame.pack(fill="x", padx=10, pady=5)

        btn_frame = ttk.Frame(test_frame)
        btn_frame.pack(fill="x")

        ttk.Button(
            btn_frame, text="📢 Test Notification", command=self.test_notification
        ).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="❌ Test Error", command=self.test_error).pack(
            side="left", padx=2
        )
        ttk.Button(
            btn_frame, text="📊 Show Tab Stats", command=self.show_tab_stats
        ).pack(side="left", padx=2)

        # About section
        about_frame = ttk.LabelFrame(self.frame, text="About", padding=10)
        about_frame.pack(fill="x", padx=10, pady=5)

        about_text = """FlexTabs Demo v1.0
A comprehensive demonstration of the FlexTabs library features.

🎯 Features Demonstrated:
• Multiple opener types (toolbar, sidebar, menu)
• Advanced tab content with real functionality  
• Keyboard shortcuts and event handling
• Toast notifications and error handling
• Runtime tab management
• Settings and configuration options

Created with ❤️ using FlexTabs library."""

        ttk.Label(about_frame, text=about_text, justify="left").pack(anchor="w")

    def update_close_mode(self):
        """Update tab manager close mode."""
        manager = self.get_manager()
        if manager:
            manager.set_close_mode(self.close_mode_var.get())
            manager.show_notification(
                f"Close mode: {self.close_mode_var.get()}", "info"
            )

    def update_confirmation(self):
        """Update confirmation setting."""
        manager = self.get_manager()
        if manager:
            manager.close_confirmation = self.confirmation_var.get()
            status = "enabled" if self.confirmation_var.get() else "disabled"
            manager.show_notification(f"Close confirmation {status}", "info")

    def change_theme(self, event=None):
        """Change application theme."""
        try:
            style = ttk.Style()
            style.theme_use(self.theme_var.get())

            manager = self.get_manager()
            if manager:
                manager.show_notification(
                    f"Theme changed to: {self.theme_var.get()}", "success"
                )
        except Exception as e:
            manager = self.get_manager()
            if manager:
                manager.show_notification(f"Theme error: {e}", "error")

    def test_notification(self):
        """Test notification system."""
        manager = self.get_manager()
        if manager:
            import random

            messages = [
                ("🎉 Test successful!", "success"),
                ("⚠️ This is a warning", "warning"),
                ("ℹ️ Information message", "info"),
                ("❌ Error simulation", "error"),
            ]
            message, msg_type = random.choice(messages)
            duration = self.notification_duration_var.get()
            manager.show_notification(message, msg_type, duration)

    def test_error(self):
        """Test error handling."""
        manager = self.get_manager()
        if manager:
            try:
                # Simulate an error
                raise ValueError("This is a simulated error for testing!")
            except Exception as e:
                manager.show_notification(f"💥 Caught error: {e}", "error")

    def show_tab_stats(self):
        """Display comprehensive tab statistics."""
        manager = self.get_manager()
        if not manager:
            return

        open_tabs = manager.get_open_tabs()
        current_tab = manager.get_current_tab()
        all_configs = list(manager.tab_configs.keys())

        stats_window = tk.Toplevel(self.frame)
        stats_window.title("Tab Statistics")
        stats_window.geometry("400x300")

        stats_text = tk.Text(stats_window, wrap="word", padx=10, pady=10)
        stats_text.pack(fill="both", expand=True)

        content = f"""📊 TAB MANAGER STATISTICS

📈 Current Status:
• Total Configured Tabs: {len(all_configs)}
• Currently Open Tabs: {len(open_tabs)}
• Active Tab: {current_tab or 'None'}

📁 Open Tabs:
{chr(10).join(f'  • {tab_id}' for tab_id in open_tabs) if open_tabs else '  (None)'}

🔧 Available Tabs:
{chr(10).join(f'  • {tab_id}' for tab_id in all_configs)}

⚙️ Configuration:
• Close Mode: {manager.get_close_mode().value}
• Close Confirmation: {'Enabled' if manager.close_confirmation else 'Disabled'}
• Keyboard Shortcuts: {'Enabled' if manager.enable_keyboard_shortcuts else 'Disabled'}

🕒 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        stats_text.insert(1.0, content)
        stats_text.config(state="disabled")


class HelpTab(TabContent):
    """Help and documentation tab."""

    def setup_content(self):
        # Create scrollable text widget
        text_frame = ttk.Frame(self.frame)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.help_text = tk.Text(
            text_frame,
            wrap="word",
            padx=15,
            pady=15,
            font=("Arial", 10),
            background="#fafafa",
        )
        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.help_text.yview
        )
        self.help_text.configure(yscrollcommand=scrollbar.set)

        self.help_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Insert help content
        help_content = """
🚀 FLEXTABS COMPLETE FEATURE GUIDE

Welcome to FlexTabs! This tab demonstrates every feature available in the library.

═══════════════════════════════════════════════════════════════════

📖 TAB TYPES & CONTENT

🏠 Dashboard Tab
• System overview and statistics
• Real-time tab state monitoring  
• Quick access buttons to other tabs
• Auto-refreshing content

📝 Text Editor Tab
• Full-featured text editing
• File operations (Open, Save, New)
• Real-time statistics (lines, words, characters)
• Find functionality
• Unsaved changes protection

📊 Data Viewer Tab
• Tabular data display with TreeView
• Data generation and statistics
• Chart visualization (simulated)
• CSV export functionality

⚙️ Settings Tab
• Runtime configuration changes
• Theme switching
• Close mode selection
• Notification preferences
• Feature testing tools

❓ Help Tab (This tab!)
• Complete feature documentation
• Keyboard shortcuts reference
• Usage examples and tips

═══════════════════════════════════════════════════════════════════

⌨️ KEYBOARD SHORTCUTS

Global Shortcuts:
• Ctrl+W         → Close current tab
• Ctrl+Tab       → Next tab
• Ctrl+Shift+Tab → Previous tab
• Ctrl+1-9       → Switch to tab by number

Tab-Specific Shortcuts:
• Ctrl+F4        → Open Dashboard (custom shortcut)
• F1             → Open Help tab (custom shortcut)

Text Editor Shortcuts:
• Ctrl+O         → Open file
• Ctrl+S         → Save file
• Ctrl+N         → New file
• Ctrl+F         → Find text

═══════════════════════════════════════════════════════════════════

🎛️ OPENER TYPES

The demo shows different ways to open tabs:

📋 Sidebar Opener (Current)
• Vertical button layout
• Always visible
• Can be positioned left or right
• Optional title display

🔧 Toolbar Opener
• Horizontal or vertical layout
• Can be positioned on any side
• Compact button style
• Good for limited space

📑 Menu Opener
• Integrates with application menu bar
• Dropdown menu access
• Saves screen real estate
• Traditional desktop app feel

═══════════════════════════════════════════════════════════════════

🎨 CLOSE MODES & BEHAVIOR

Close Button Modes:
• Right-click only
• Double-click only  
• Both right-click and double-click

Close Behavior Modes:
• Active Only   → Only close the currently selected tab
• Any Visible   → Close any tab by clicking
• Both         → Active + Ctrl+click for any tab

Confirmation Types:
• None         → Close immediately
• Yes/No       → Simple confirmation dialog
• Warning      → Warning about potential data loss
• Info         → Information message before closing

═══════════════════════════════════════════════════════════════════

🔧 ADVANCED FEATURES

Runtime Tab Management:
• Add new tab configurations dynamically
• Remove tab configurations
• Open/close tabs programmatically
• Query tab states and information

Event Callbacks:
• on_tab_opened  → Called when a tab is opened
• on_tab_closed  → Called when a tab is closed
• on_tab_switched → Called when switching between tabs
• on_tab_error   → Called when an error occurs

Tab Content Lifecycle:
• setup_content()  → Initialize tab content
• on_tab_focus()   → Tab gains focus
• on_tab_blur()    → Tab loses focus  
• on_tab_close()   → Before tab closes (can prevent)
• cleanup()        → Clean up resources

State Management:
• Track which tabs are open
• Maintain tab order and indices
• Handle tab-specific data
• Error tracking per tab

═══════════════════════════════════════════════════════════════════

🎯 TOAST NOTIFICATIONS

FlexTabs includes a built-in notification system:

Types:
• Info     → Blue theme, general information
• Success  → Green theme, successful operations
• Warning  → Yellow theme, warnings and alerts
• Error    → Red theme, error messages

Features:
• Auto-dismiss after configurable duration
• Click to dismiss manually
• Positioned relative to main window
• Non-blocking and non-modal

═══════════════════════════════════════════════════════════════════

💡 TIPS & BEST PRACTICES

Tab Content Design:
• Inherit from TabContent base class
• Always implement setup_content()
• Use cleanup() for resource management
• Handle errors gracefully in lifecycle methods

Performance:
• Tabs are created only when first opened
• Content is destroyed when tab is closed
• Use on_tab_focus/blur for expensive operations
• Lazy load data when possible

User Experience:
• Provide meaningful tab titles and tooltips
• Use appropriate close confirmation for important data
• Show progress indicators for long operations
• Give feedback through notifications

Error Handling:
• Always handle exceptions in tab content
• Use the manager's notification system
• Provide helpful error messages
• Log errors for debugging

Memory Management:
• Clean up resources in cleanup() method
• Avoid circular references to tab manager
• Use weak references when storing manager reference
• Destroy unused widgets properly

═══════════════════════════════════════════════════════════════════

🎪 DEMO SPECIFIC FEATURES

This demo application showcases:

Interactive Dashboard:
• Live tab statistics
• Quick navigation buttons
• System information display
• Auto-refreshing content

Functional Text Editor:
• Real file operations
• Live document statistics
• Find functionality
• Unsaved changes protection

Data Management:
• Dynamic data generation
• Statistics calculation
• Export capabilities
• Visualization tools

Settings Integration:
• Runtime configuration changes
• Theme switching
• Preference management
• Feature testing

═══════════════════════════════════════════════════════════════════

🔍 TROUBLESHOOTING

Common Issues:

Tab Won't Close:
• Check if tab is marked as closable=False
• Verify on_tab_close() returns True
• Check close mode configuration

Keyboard Shortcuts Not Working:
• Ensure enable_keyboard_shortcuts=True
• Check if shortcuts conflict with system shortcuts
• Verify focus is on the application

Content Not Loading:
• Check for exceptions in setup_content()
• Verify content_class is correct subclass
• Look for initialization errors

Memory Issues:
• Implement proper cleanup() methods
• Avoid storing large objects in tab content
• Use weak references appropriately

═══════════════════════════════════════════════════════════════════

📚 FURTHER RESOURCES

For more information about FlexTabs:
• Check the source code documentation
• Review the TabContent base class
• Examine the different opener implementations
• Study the TabManager configuration options

Happy tabbing! 🎉
        """

        self.help_text.insert(1.0, help_content)
        self.help_text.config(state="disabled")


# =============================================================================
# MAIN DEMO APPLICATION
# =============================================================================


class FlexTabsDemo:
    """Complete FlexTabs feature demonstration."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FlexTabs Complete Feature Demo")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Configure style
        style = ttk.Style()
        style.theme_use("clam")

        self.setup_menu()
        self.setup_tabs()
        self.setup_status_bar()

        # Bind window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Auto-open dashboard
        self.root.after(100, lambda: self.tab_manager.open_tab("dashboard"))

    def setup_menu(self):
        """Setup application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Tab Manager", command=self.new_tab_manager)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(
            label="Dashboard", command=lambda: self.tab_manager.open_tab("dashboard")
        )
        view_menu.add_command(
            label="Text Editor",
            command=lambda: self.tab_manager.open_tab("text_editor"),
        )
        view_menu.add_command(
            label="Data Viewer",
            command=lambda: self.tab_manager.open_tab("data_viewer"),
        )
        view_menu.add_separator()
        view_menu.add_command(
            label="Settings", command=lambda: self.tab_manager.open_tab("settings")
        )
        view_menu.add_command(
            label="Help", command=lambda: self.tab_manager.open_tab("help")
        )

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Close All Tabs", command=self.close_all_tabs)
        tools_menu.add_command(label="Show Tab Stats", command=self.show_tab_stats)
        tools_menu.add_separator()
        tools_menu.add_command(
            label="Test Notification", command=self.test_notification
        )

        # Demo menu (for switching opener types)
        demo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Demo", menu=demo_menu)
        demo_menu.add_command(
            label="Switch to Toolbar", command=lambda: self.switch_opener("toolbar")
        )
        demo_menu.add_command(
            label="Switch to Sidebar", command=lambda: self.switch_opener("sidebar")
        )
        demo_menu.add_command(
            label="Switch to Menu", command=lambda: self.switch_opener("menu")
        )

    def setup_tabs(self):
        """Setup the main tab manager."""
        # Define all tab configurations
        tab_configs = [
            TabConfig(
                id="dashboard",
                title="🏠 Dashboard",
                content_class=DashboardTab,
                tooltip="System overview and tab management",
                keyboard_shortcut="<Control-F4>",
                closable=False,  # Dashboard cannot be closed
            ),
            TabConfig(
                id="text_editor",
                title="📝 Text Editor",
                content_class=TextEditorTab,
                tooltip="Advanced text editor with file operations",
                data={"file_types": [".txt", ".py", ".md"]},
            ),
            TabConfig(
                id="data_viewer",
                title="📊 Data Viewer",
                content_class=DataViewerTab,
                tooltip="Data visualization and analysis tools",
            ),
            TabConfig(
                id="settings",
                title="⚙️ Settings",
                content_class=SettingsTab,
                tooltip="Application settings and preferences",
            ),
            TabConfig(
                id="help",
                title="❓ Help",
                content_class=HelpTab,
                tooltip="Complete feature documentation",
                keyboard_shortcut="<F1>",
            ),
        ]

        # Sidebar opener configuration
        opener_config = {
            "position": "left",
            "width": 180,
            "title": "📂 Tabs",
            "style": {"relief": "solid", "borderwidth": 1},
            "button_style": {"width": 20},
        }

        # Create tab manager with comprehensive configuration
        self.tab_manager = TabManager(
            parent=self.root,
            tab_configs=tab_configs,
            opener_type="sidebar",
            opener_config=opener_config,
            close_button_style="right_click",
            close_mode=CloseMode.ACTIVE_ONLY,
            close_confirmation=False,
            close_confirmation_type=CloseConfirmationType.YESNO,
            enable_keyboard_shortcuts=True,
            notebook_config={"padding": 5},
        )

        # Set up event callbacks
        self.tab_manager.on_tab_opened = self.on_tab_opened
        self.tab_manager.on_tab_closed = self.on_tab_closed
        self.tab_manager.on_tab_switched = self.on_tab_switched
        self.tab_manager.on_tab_error = self.on_tab_error

        self.tab_manager.pack(fill="both", expand=True)

    def setup_status_bar(self):
        """Setup application status bar."""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side="bottom", fill="x")

        # Status variables
        self.status_text = tk.StringVar(value="Ready")
        self.tab_count_text = tk.StringVar(value="Tabs: 0")
        self.time_text = tk.StringVar()

        # Status widgets
        ttk.Label(self.status_frame, textvariable=self.status_text).pack(
            side="left", padx=5
        )

        ttk.Separator(self.status_frame, orient="vertical").pack(
            side="left", fill="y", padx=5
        )
        ttk.Label(self.status_frame, textvariable=self.tab_count_text).pack(
            side="left", padx=5
        )

        ttk.Label(self.status_frame, textvariable=self.time_text).pack(
            side="right", padx=5
        )

        # Update time periodically
        self.update_time()

        # Initial status update
        self.update_status()

    def update_time(self):
        """Update time display."""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_text.set(current_time)
        self.root.after(1000, self.update_time)

    def update_status(self, message="Ready"):
        """Update status bar information."""
        self.status_text.set(message)
        open_tabs = len(self.tab_manager.get_open_tabs())
        self.tab_count_text.set(f"Tabs: {open_tabs}")

    # Event callbacks
    def on_tab_opened(self, tab_id: str):
        """Handle tab opened event."""
        config = self.tab_manager.tab_configs.get(tab_id)
        title = config.title if config else tab_id
        self.update_status(f"Opened: {title}")
        print(f"🟢 Tab opened: {tab_id}")

    def on_tab_closed(self, tab_id: str):
        """Handle tab closed event."""
        config = self.tab_manager.tab_configs.get(tab_id)
        title = config.title if config else tab_id
        self.update_status(f"Closed: {title}")
        print(f"🔴 Tab closed: {tab_id}")

    def on_tab_switched(self, new_tab_id: str, old_tab_id: str):
        """Handle tab switch event."""
        if new_tab_id:
            config = self.tab_manager.tab_configs.get(new_tab_id)
            title = config.title if config else new_tab_id
            self.update_status(f"Active: {title}")
            print(f"🔄 Switched to: {new_tab_id} (from: {old_tab_id})")

    def on_tab_error(self, tab_id: str, error: Exception):
        """Handle tab error event."""
        self.update_status(f"Error in {tab_id}: {str(error)}")
        print(f"❌ Error in tab {tab_id}: {error}")

    # Menu actions
    def new_tab_manager(self):
        """Create a new tab manager window."""
        new_demo = FlexTabsDemo()
        new_demo.run()

    def close_all_tabs(self):
        """Close all open tabs."""
        closed_count = self.tab_manager.close_all_tabs()
        self.tab_manager.show_notification(f"Closed {closed_count} tabs", "info")

    def show_tab_stats(self):
        """Show comprehensive tab statistics."""
        open_tabs = self.tab_manager.get_open_tabs()
        current_tab = self.tab_manager.get_current_tab()

        stats_msg = f"Open: {len(open_tabs)}, Current: {current_tab or 'None'}"
        messagebox.showinfo(
            "Tab Statistics",
            f"📊 Tab Statistics\n\n"
            f"Open tabs: {len(open_tabs)}\n"
            f"Current tab: {current_tab or 'None'}\n"
            f"Tab list: {', '.join(open_tabs) if open_tabs else 'None'}",
        )

    def test_notification(self):
        """Test notification system."""
        messages = [
            ("🎉 Feature demo is awesome!", "success"),
            ("⚠️ This is just a test", "warning"),
            ("ℹ️ FlexTabs rocks!", "info"),
            ("❌ Simulated error", "error"),
        ]
        message, msg_type = random.choice(messages)
        self.tab_manager.show_notification(message, msg_type)

    def switch_opener(self, opener_type: str):
        """Switch to a different opener type (demo feature)."""
        try:
            # This would require recreating the tab manager
            # For demo purposes, just show a notification
            self.tab_manager.show_notification(
                f"🔄 Would switch to {opener_type} opener (requires restart)", "info"
            )
        except Exception as e:
            self.tab_manager.show_notification(f"❌ Switch failed: {e}", "error")

    def on_closing(self):
        """Handle application closing."""
        # Check for unsaved changes in text editor
        text_tab_content = self.tab_manager.get_tab_content("text_editor")
        if (
            text_tab_content
            and hasattr(text_tab_content, "modified")
            and text_tab_content.modified
        ):
            if not messagebox.askyesno(
                "Exit", "Text editor has unsaved changes. Exit anyway?"
            ):
                return

        self.tab_manager.cleanup()
        self.root.destroy()

    def run(self):
        """Start the application."""
        print("🚀 Starting FlexTabs Complete Demo...")
        print("📖 Features demonstrated:")
        print("   • Multiple opener types")
        print("   • Advanced tab content")
        print("   • Keyboard shortcuts")
        print("   • Event handling")
        print("   • Runtime configuration")
        print("   • Toast notifications")
        print("   • Error handling")
        print("\n⌨️  Try these shortcuts:")
        print("   • Ctrl+W: Close current tab")
        print("   • Ctrl+Tab: Next tab")
        print("   • Ctrl+F4: Dashboard")
        print("   • F1: Help")
        print("\n🎯 Right-click tabs to close them!")
        print("=" * 50)

        self.root.mainloop()


# =============================================================================
# ADDITIONAL DEMO CLASSES (Advanced usage examples)
# =============================================================================


class CustomTabContent(TabContent):
    """Template for creating custom tab content."""

    def setup_content(self):
        """Override this method to create your tab content."""
        ttk.Label(self.frame, text=f"Custom content for {self.tab_id}").pack(pady=20)

        # Example: Add a close button inside the tab
        if self.config.closable:
            manager = self.get_manager()
            if manager:
                close_btn = manager.add_close_button(self.frame, self.tab_id)
                close_btn.pack(pady=10)

    def on_tab_focus(self):
        """Called when tab gains focus."""
        print(f"✨ {self.tab_id} gained focus")

    def on_tab_blur(self):
        """Called when tab loses focus."""
        print(f"💤 {self.tab_id} lost focus")

    def on_tab_close(self):
        """Called before tab closes. Return False to prevent closing."""
        return messagebox.askyesno("Close Tab", f"Really close {self.config.title}?")

    def cleanup(self):
        """Clean up resources when tab is destroyed."""
        print(f"🧹 Cleaning up {self.tab_id}")
        super().cleanup()


# Example: Dynamic tab creation function
def create_dynamic_tab(manager: TabManager, tab_id: str, title: str):
    """Helper function to create tabs dynamically."""
    try:
        config = TabConfig(
            id=tab_id,
            title=title,
            content_class=CustomTabContent,
            tooltip=f"Dynamically created tab: {title}",
        )
        manager.add_tab_config(config)
        manager.open_tab(tab_id)
        return True
    except Exception as e:
        manager.show_notification(f"Failed to create tab: {e}", "error")
        return False


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Import required modules
    import tkinter.simpledialog

    try:
        # Create and run the demo
        demo = FlexTabsDemo()
        demo.run()

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("📦 Make sure FlexTabs library is installed and in your Python path")
        print("💡 Place this demo file in the same directory as the flextabs package")

    except Exception as e:
        print(f"💥 Demo Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("👋 FlexTabs Demo finished. Thanks for trying it!")
