"""System tray component for Claude Code Usage Monitor.

This package provides a PyQt6-based system tray application for monitoring
Claude Code token usage in real-time.
"""

from typing import Tuple

PYQT_AVAILABLE = False
PYQT_ERROR: str = ""


def check_dependencies() -> Tuple[bool, str]:
    """Check if PyQt6 is available.

    Returns:
        Tuple of (is_available, error_message)
    """
    global PYQT_AVAILABLE, PYQT_ERROR

    try:
        from PyQt6.QtWidgets import QApplication  # noqa: F401

        PYQT_AVAILABLE = True
        PYQT_ERROR = ""
        return True, ""
    except ImportError as e:
        PYQT_AVAILABLE = False
        PYQT_ERROR = str(e)
        return False, (
            "PyQt6 is required for the system tray application.\n"
            "Install it with: pip install 'claude-monitor[tray]'\n"
            f"Error: {e}"
        )


__all__ = [
    "check_dependencies",
    "PYQT_AVAILABLE",
    "PYQT_ERROR",
]
