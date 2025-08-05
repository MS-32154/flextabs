import pytest
import tkinter as tk
from tkinter import ttk
from unittest.mock import Mock, patch

from flextabs.enums import TabPosition, CloseMode, CloseConfirmationType
from flextabs.widgets import TooltipWidget, ToastNotification
from flextabs.tab_base import TabConfig, TabContent
from flextabs.openers import ToolbarOpener, SidebarOpener, MenuOpener
from flextabs.tab_manager import TabManager


class MockTabContent(TabContent):
    """Mock tab content for testing."""

    def setup_content(self):
        self.label = ttk.Label(self.frame, text=f"Content for {self.tab_id}")
        self.label.pack()
        self.setup_called = True
        self.focus_called = False
        self.blur_called = False
        self.close_called = False

    def on_tab_focus(self):
        self.focus_called = True

    def on_tab_blur(self):
        self.blur_called = True

    def on_tab_close(self):
        self.close_called = True
        return True


class FailingTabContent(TabContent):
    """Tab content that fails during setup."""

    def setup_content(self):
        raise ValueError("Intentional setup failure")


class NonClosableTabContent(TabContent):
    """Tab content that prevents closing."""

    def setup_content(self):
        self.label = ttk.Label(self.frame, text="Non-closable content")
        self.label.pack()

    def on_tab_close(self):
        return False


@pytest.fixture
def root():
    """Create tkinter root for tests."""
    root = tk.Tk()
    root.withdraw()  # Hide the window
    yield root
    root.destroy()


@pytest.fixture
def sample_tab_configs():
    """Sample tab configurations for testing."""
    return [
        TabConfig("tab1", "Tab One", MockTabContent, tooltip="First tab"),
        TabConfig("tab2", "Tab Two", MockTabContent, closable=False),
        TabConfig("tab3", "Tab Three", MockTabContent, keyboard_shortcut="<Control-3>"),
    ]


class TestEnums:
    """Test enum classes."""

    def test_tab_position_enum(self):
        assert TabPosition.TOP.value == "top"
        assert TabPosition.BOTTOM.value == "bottom"
        assert TabPosition.LEFT.value == "left"
        assert TabPosition.RIGHT.value == "right"

    def test_close_mode_enum(self):
        assert CloseMode.ACTIVE_ONLY.value == "active_only"
        assert CloseMode.ANY_VISIBLE.value == "any_visible"
        assert CloseMode.BOTH.value == "both"

    def test_close_confirmation_type_enum(self):
        assert CloseConfirmationType.NONE.value == "none"
        assert CloseConfirmationType.YESNO.value == "yesno"
        assert CloseConfirmationType.WARNING.value == "warning"
        assert CloseConfirmationType.INFO.value == "info"


class TestTabConfig:
    """Test TabConfig dataclass."""

    def test_valid_config(self):
        config = TabConfig("test", "Test Tab", MockTabContent)
        assert config.id == "test"
        assert config.title == "Test Tab"
        assert config.content_class == MockTabContent
        assert config.closable is True
        assert config.tooltip is None

    def test_config_with_options(self):
        config = TabConfig(
            "test",
            "Test",
            MockTabContent,
            icon="icon.png",
            tooltip="Test tooltip",
            closable=False,
            keyboard_shortcut="<Control-t>",
            data={"key": "value"},
        )
        assert config.icon == "icon.png"
        assert config.tooltip == "Test tooltip"
        assert config.closable is False
        assert config.keyboard_shortcut == "<Control-t>"
        assert config.data == {"key": "value"}

    def test_invalid_config_empty_id(self):
        with pytest.raises(ValueError, match="Tab ID and title cannot be empty"):
            TabConfig("", "Test", MockTabContent)

    def test_invalid_config_empty_title(self):
        with pytest.raises(ValueError, match="Tab ID and title cannot be empty"):
            TabConfig("test", "", MockTabContent)

    def test_invalid_config_wrong_class(self):
        with pytest.raises(
            ValueError, match="content_class must be a subclass of TabContent"
        ):
            TabConfig("test", "Test", str)


class TestTabContent:
    """Test TabContent base class."""

    def test_successful_initialization(self, root):
        frame = ttk.Frame(root)
        config = TabConfig("test", "Test", MockTabContent)
        manager = Mock()

        content = MockTabContent(frame, "test", config, manager)

        assert content.tab_id == "test"
        assert content.config == config
        assert hasattr(content, "setup_called")
        assert content.setup_called is True

    def test_failed_initialization(self, root):
        frame = ttk.Frame(root)
        config = TabConfig("test", "Test", FailingTabContent)
        manager = Mock()

        with pytest.raises(RuntimeError, match="Failed to initialize tab content"):
            FailingTabContent(frame, "test", config, manager)

    def test_cleanup(self, root):
        frame = ttk.Frame(root)
        config = TabConfig("test", "Test", MockTabContent)
        manager = Mock()

        content = MockTabContent(frame, "test", config, manager)
        content.cleanup()
        # Should not raise an error

    def test_manager_reference(self, root):
        frame = ttk.Frame(root)
        config = TabConfig("test", "Test", MockTabContent)
        manager = Mock()

        content = MockTabContent(frame, "test", config, manager)
        assert content.get_manager() == manager


class TestTooltipWidget:
    """Test TooltipWidget class."""

    def test_tooltip_creation(self, root):
        button = ttk.Button(root, text="Test")
        tooltip = TooltipWidget(button, "Test tooltip")

        assert tooltip.widget == button
        assert tooltip.text == "Test tooltip"
        assert tooltip.delay == 500

    def test_tooltip_update_text(self, root):
        button = ttk.Button(root, text="Test")
        tooltip = TooltipWidget(button, "Original")

        tooltip.update_text("Updated")
        assert tooltip.text == "Updated"

    def test_tooltip_show_hide(self, root):
        button = ttk.Button(root, text="Test")
        button.pack()
        root.update()

        tooltip = TooltipWidget(button, "Test tooltip", delay=1)

        # Simulate enter event
        event = Mock()
        tooltip._on_enter(event)
        root.after(5, lambda: tooltip._hide_tooltip())
        root.update()


class TestToastNotification:
    """Test ToastNotification class."""

    @patch("tkinter.Toplevel")
    def test_toast_creation(self, mock_toplevel, root):
        mock_toast = Mock()
        mock_toplevel.return_value = mock_toast

        ToastNotification.show(root, "Test message")

    def test_toast_colors(self):
        colors = ToastNotification.COLORS
        assert "info" in colors
        assert "warning" in colors
        assert "error" in colors
        assert "success" in colors


class TestToolbarOpener:
    """Test ToolbarOpener class."""

    def test_toolbar_creation(self, root, sample_tab_configs):
        opener = ToolbarOpener(root, {"position": "top", "layout": "horizontal"})
        opener.setup_opener(sample_tab_configs)

        assert hasattr(opener, "toolbar")
        assert hasattr(opener, "buttons")
        assert len(opener.buttons) == 3

    def test_vertical_layout(self, root, sample_tab_configs):
        opener = ToolbarOpener(root, {"position": "left", "layout": "vertical"})
        opener.setup_opener(sample_tab_configs)

        assert hasattr(opener, "toolbar")
        assert hasattr(opener, "buttons")

    def test_update_tab_state(self, root, sample_tab_configs):
        opener = ToolbarOpener(root, {})
        opener.setup_opener(sample_tab_configs)

        # Should not raise error
        opener.update_tab_state("tab1", True)
        opener.update_tab_state("tab1", False)


class TestSidebarOpener:
    """Test SidebarOpener class."""

    def test_sidebar_creation(self, root, sample_tab_configs):
        opener = SidebarOpener(
            root, {"position": "left", "width": 200, "title": "Tabs"}
        )
        opener.setup_opener(sample_tab_configs)

        assert hasattr(opener, "sidebar")
        assert hasattr(opener, "buttons")
        assert len(opener.buttons) == 3

    def test_right_sidebar(self, root, sample_tab_configs):
        opener = SidebarOpener(root, {"position": "right"})
        opener.setup_opener(sample_tab_configs)

        assert hasattr(opener, "sidebar")


class TestMenuOpener:
    """Test MenuOpener class."""

    def test_menu_creation(self, root, sample_tab_configs):
        opener = MenuOpener(root, {"menu_title": "Test Tabs"})
        opener.setup_opener(sample_tab_configs)

        assert hasattr(opener, "tabs_menu")
        assert hasattr(root, "menubar")

    def test_menu_refresh(self, root, sample_tab_configs):
        opener = MenuOpener(root, {})
        opener.setup_opener(sample_tab_configs)

        # Add another config and refresh
        new_config = TabConfig("tab4", "Tab Four", MockTabContent)
        opener.refresh_opener(sample_tab_configs + [new_config])


class TestTabManager:
    """Test TabManager class."""

    def test_basic_initialization(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        assert manager.tab_configs is not None
        assert len(manager.tab_configs) == 3
        assert hasattr(manager, "notebook")
        assert hasattr(manager, "opener")

    def test_initialization_with_options(self, root, sample_tab_configs):
        manager = TabManager(
            root,
            sample_tab_configs,
            opener_type="toolbar",
            opener_config={"position": "top"},
            close_confirmation=True,
            close_confirmation_type="yesno",
            close_mode="any_visible",
        )

        assert manager.close_confirmation is True
        assert manager.close_confirmation_type == CloseConfirmationType.YESNO
        assert manager.close_mode == CloseMode.ANY_VISIBLE

    def test_invalid_opener_type(self, root, sample_tab_configs):
        with pytest.raises(RuntimeError):
            TabManager(root, sample_tab_configs, opener_type="invalid")

    def test_open_tab(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        result = manager.open_tab("tab1")
        assert result is True
        assert manager.is_tab_open("tab1") is True
        assert "tab1" in manager.get_open_tabs()

    def test_open_nonexistent_tab(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        result = manager.open_tab("nonexistent")
        assert result is False

    def test_close_tab(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        # Open then close
        manager.open_tab("tab1")
        result = manager.close_tab("tab1")

        assert result is True
        assert manager.is_tab_open("tab1") is False

    def test_close_non_closable_tab(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        # tab2 is not closable
        manager.open_tab("tab2")
        result = manager.close_tab("tab2")

        assert result is False
        assert manager.is_tab_open("tab2") is True

    def test_close_with_content_prevention(self, root):
        config = TabConfig("test", "Test", NonClosableTabContent)
        manager = TabManager(root, [config])

        manager.open_tab("test")
        result = manager.close_tab("test")

        assert result is False
        assert manager.is_tab_open("test") is True

    def test_select_tab(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        # Open multiple tabs
        manager.open_tab("tab1")
        manager.open_tab("tab2")

        result = manager.select_tab("tab1")
        assert result is True

    def test_close_all_tabs(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        # Open multiple tabs
        manager.open_tab("tab1")
        manager.open_tab("tab3")  # Skip tab2 as it's not closable

        closed_count = manager.close_all_tabs()
        assert closed_count == 2
        assert len(manager.get_open_tabs()) == 0

    def test_add_tab_config_runtime(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        new_config = TabConfig("new_tab", "New Tab", MockTabContent)
        manager.add_tab_config(new_config)

        assert "new_tab" in manager.tab_configs
        assert manager.open_tab("new_tab") is True

    def test_add_duplicate_tab_config(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        duplicate_config = TabConfig("tab1", "Duplicate", MockTabContent)

        with pytest.raises(ValueError, match="Tab with ID 'tab1' already exists"):
            manager.add_tab_config(duplicate_config)

    def test_remove_tab_config(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        # Open tab first
        manager.open_tab("tab1")
        assert manager.is_tab_open("tab1") is True

        # Remove config (should close tab)
        result = manager.remove_tab_config("tab1")
        assert result is True
        assert "tab1" not in manager.tab_configs
        assert manager.is_tab_open("tab1") is False

    def test_remove_nonexistent_config(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        result = manager.remove_tab_config("nonexistent")
        assert result is False

    def test_get_tab_content(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        manager.open_tab("tab1")
        content = manager.get_tab_content("tab1")

        assert content is not None
        assert isinstance(content, MockTabContent)
        assert content.tab_id == "tab1"

    def test_event_callbacks(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        opened_tabs = []
        closed_tabs = []
        switched_tabs = []

        manager.on_tab_opened = lambda tab_id: opened_tabs.append(tab_id)
        manager.on_tab_closed = lambda tab_id: closed_tabs.append(tab_id)
        manager.on_tab_switched = lambda new_id, old_id: switched_tabs.append(
            (new_id, old_id)
        )

        # Test events
        manager.open_tab("tab1")
        manager.open_tab("tab3")
        manager.select_tab("tab1")
        manager.close_tab("tab1")

        assert "tab1" in opened_tabs
        assert "tab3" in opened_tabs
        assert "tab1" in closed_tabs

    def test_close_mode_changes(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        # Test enum and string modes
        manager.set_close_mode(CloseMode.ANY_VISIBLE)
        assert manager.get_close_mode() == CloseMode.ANY_VISIBLE

        manager.set_close_mode("both")
        assert manager.get_close_mode() == CloseMode.BOTH

    def test_notification_system(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        # Should not raise error
        manager.show_notification("Test message", "info")
        manager.show_notification("Warning", "warning", 1000)

    def test_cleanup(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        # Open some tabs
        manager.open_tab("tab1")
        manager.open_tab("tab3")

        # Cleanup should not raise errors
        manager.cleanup()

        # Should be safe to call multiple times
        manager.cleanup()

    def test_failed_tab_content_creation(self, root):
        config = TabConfig("failing", "Failing Tab", FailingTabContent)
        manager = TabManager(root, [config])

        result = manager.open_tab("failing")
        assert result is False

    @patch("tkinter.messagebox.askyesno")
    def test_close_confirmation(self, mock_askyesno, root, sample_tab_configs):
        mock_askyesno.return_value = True

        manager = TabManager(
            root,
            sample_tab_configs,
            close_confirmation=True,
            close_confirmation_type="yesno",
        )

        manager.open_tab("tab1")
        result = manager.close_tab("tab1")

        assert result is True
        mock_askyesno.assert_called_once()

    @patch("tkinter.messagebox.askyesno")
    def test_close_confirmation_denied(self, mock_askyesno, root, sample_tab_configs):
        mock_askyesno.return_value = False

        manager = TabManager(
            root,
            sample_tab_configs,
            close_confirmation=True,
            close_confirmation_type="yesno",
        )

        manager.open_tab("tab1")
        result = manager.close_tab("tab1")

        assert result is False
        assert manager.is_tab_open("tab1") is True

    def test_keyboard_shortcuts(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs, enable_keyboard_shortcuts=True)

        # Open some tabs for navigation testing
        manager.open_tab("tab1")
        manager.open_tab("tab3")

        # Test keyboard navigation methods
        manager._next_tab()
        manager._prev_tab()
        manager._select_tab_by_index(0)
        manager._close_current_tab()

        # Should not raise errors

    def test_disabled_keyboard_shortcuts(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs, enable_keyboard_shortcuts=False)

        # Should still initialize properly
        assert hasattr(manager, "notebook")

    def test_add_close_button(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        manager.open_tab("tab1")
        content = manager.get_tab_content("tab1")

        close_btn = manager.add_close_button(content.frame, "tab1")
        assert close_btn is not None
        assert isinstance(close_btn, ttk.Button)

    def test_add_close_button_non_closable(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        manager.open_tab("tab2")  # tab2 is not closable
        content = manager.get_tab_content("tab2")

        with pytest.raises(ValueError, match="Tab 'tab2' is not closable"):
            manager.add_close_button(content.frame, "tab2")


class TestOpenerCleanup:
    """Test opener cleanup functionality."""

    def test_toolbar_opener_cleanup(self, root, sample_tab_configs):
        opener = ToolbarOpener(root, {})
        opener.setup_opener(sample_tab_configs)

        # Should not raise error
        opener.cleanup()

    def test_sidebar_opener_cleanup(self, root, sample_tab_configs):
        opener = SidebarOpener(root, {})
        opener.setup_opener(sample_tab_configs)

        # Should not raise error
        opener.cleanup()

    def test_menu_opener_cleanup(self, root, sample_tab_configs):
        opener = MenuOpener(root, {})
        opener.setup_opener(sample_tab_configs)

        # Should not raise error
        opener.cleanup()


class TestErrorHandling:
    """Test error handling throughout the system."""

    def test_tab_manager_error_callback(self, root, sample_tab_configs):
        manager = TabManager(root, sample_tab_configs)

        errors = []
        manager.on_tab_error = lambda tab_id, error: errors.append((tab_id, error))

        # Create a mock content that will fail on focus
        manager.open_tab("tab1")
        content = manager.get_tab_content("tab1")

        # Mock a method to raise an error
        original_focus = content.on_tab_focus
        content.on_tab_focus = Mock(side_effect=Exception("Test error"))

        # Trigger the error
        manager.select_tab("tab1")
        root.update()

        # Restore original method
        content.on_tab_focus = original_focus

        # Check if error was handled
        assert len(errors) > 0

    def test_opener_safe_tab_opening(self, root, sample_tab_configs):
        opener = ToolbarOpener(root, {})
        opener.setup_opener(sample_tab_configs)

        # Mock tab manager to raise error
        opener.tab_manager = Mock()
        opener.tab_manager.open_tab = Mock(side_effect=Exception("Test error"))

        # Should not raise error, should show messagebox instead
        with patch("tkinter.messagebox.showerror") as mock_error:
            opener._open_tab_safe("tab1")
            mock_error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
