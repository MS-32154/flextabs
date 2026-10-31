"""High-DPI support helpers."""

import ctypes
import sys


def enable_dpi_awareness() -> bool:
    """Make the process DPI aware on Windows, so Tk renders sharply.

    Without this, Windows scales Tk windows up as bitmaps on high-DPI screens,
    which looks blurry. Call it *before* creating the first ``tk.Tk()``.
    Returns True if DPI awareness was enabled. Does nothing elsewhere: macOS
    and Linux handle scaling without it.
    """
    if sys.platform != "win32":
        return False
    windll = getattr(ctypes, "windll", None)
    if windll is None:
        return False
    try:
        # Per-monitor DPI aware (Windows 8.1+)
        return windll.shcore.SetProcessDpiAwareness(2) == 0
    except AttributeError, OSError:
        pass
    try:
        # System DPI aware (Windows Vista+)
        return bool(windll.user32.SetProcessDPIAware())
    except AttributeError, OSError:
        return False
