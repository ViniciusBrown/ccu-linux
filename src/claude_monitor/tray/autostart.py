"""XDG autostart management for Linux systems."""

import logging
import shutil
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DESKTOP_ENTRY_TEMPLATE = """[Desktop Entry]
Type=Application
Name=Claude Monitor Tray
Comment=System tray monitor for Claude Code usage
Exec={exec_path}
Icon=utilities-system-monitor
Terminal=false
Categories=Utility;Monitor;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""


class AutostartManager:
    """Manages XDG autostart for the tray application."""

    APP_NAME = "claude-monitor-tray"
    DESKTOP_FILE_NAME = "claude-monitor-tray.desktop"

    def __init__(self, autostart_dir: Optional[Path] = None) -> None:
        """Initialize autostart manager.

        Args:
            autostart_dir: Override autostart directory path
        """
        self.autostart_dir = autostart_dir or self._get_autostart_dir()
        self.desktop_file = self.autostart_dir / self.DESKTOP_FILE_NAME

    def _get_autostart_dir(self) -> Path:
        """Get XDG autostart directory.

        Returns:
            Path to autostart directory
        """
        xdg_config = Path.home() / ".config"
        return xdg_config / "autostart"

    def is_available(self) -> bool:
        """Check if autostart is available on this system.

        Returns:
            True if autostart can be configured
        """
        # Only available on Linux with XDG support
        if sys.platform != "linux":
            return False

        # Check if we can create the autostart directory
        try:
            self.autostart_dir.mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, PermissionError):
            return False

    def is_enabled(self) -> bool:
        """Check if autostart is currently enabled.

        Returns:
            True if autostart is enabled
        """
        return self.desktop_file.exists()

    def enable(self) -> bool:
        """Enable autostart.

        Returns:
            True if successful
        """
        try:
            # Ensure directory exists
            self.autostart_dir.mkdir(parents=True, exist_ok=True)

            # Find the executable path
            exec_path = self._get_exec_path()

            # Write desktop entry
            content = DESKTOP_ENTRY_TEMPLATE.format(exec_path=exec_path)
            self.desktop_file.write_text(content)

            logger.info(f"Enabled autostart: {self.desktop_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to enable autostart: {e}")
            return False

    def disable(self) -> bool:
        """Disable autostart.

        Returns:
            True if successful
        """
        try:
            if self.desktop_file.exists():
                self.desktop_file.unlink()
                logger.info(f"Disabled autostart: {self.desktop_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to disable autostart: {e}")
            return False

    def set_enabled(self, enabled: bool) -> bool:
        """Set autostart state.

        Args:
            enabled: Whether to enable autostart

        Returns:
            True if successful
        """
        if enabled:
            return self.enable()
        else:
            return self.disable()

    def _get_exec_path(self) -> str:
        """Get the executable path for the tray app.

        Returns:
            Path to execute the tray app
        """
        # Try to find the installed script
        exec_path = shutil.which(self.APP_NAME)
        if exec_path:
            return exec_path

        # Fall back to python -m
        return f"{sys.executable} -m claude_monitor.tray"
