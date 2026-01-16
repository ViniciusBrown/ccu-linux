"""Simplified tray application that reads from status file."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtCore import QTimer, pyqtSlot
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from claude_monitor.tray.icons import IconState, TrayIconManager
from claude_monitor.tray.menu import TrayMenuBuilder
from claude_monitor.tray.settings import TraySettings, TraySettingsManager
from claude_monitor.tray.stats_window import StatsWindow
from claude_monitor.tray.settings_dialog import SettingsDialog
from claude_monitor.tray.autostart import AutostartManager
from claude_monitor.tray.status_generator import write_status_file, read_status_file, STATUS_FILE

logger = logging.getLogger(__name__)


class TrayApplication(QApplication):
    """Simple system tray app that reads status from file."""

    def __init__(self, argv: list) -> None:
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)

        # Load settings
        self._settings_manager = TraySettingsManager()
        self._settings = self._settings_manager.load()
        self._autostart_manager = AutostartManager()

        # Components
        self._icon_manager = TrayIconManager(
            warning_threshold=self._settings.warning_threshold,
            critical_threshold=self._settings.critical_threshold,
        )
        self._menu_builder = TrayMenuBuilder()

        # Windows
        self._stats_window: Optional[StatsWindow] = None

        # Status data
        self._status: Optional[Dict[str, Any]] = None

        # Setup tray
        self._tray_icon = QSystemTrayIcon(self)
        self._setup_tray()
        self._connect_signals()

        # Refresh timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)

    def _setup_tray(self) -> None:
        """Setup tray icon."""
        self._tray_icon.setIcon(self._icon_manager.get_icon(IconState.LOADING))
        self._tray_icon.setToolTip("Claude Monitor\nLoading...")
        self._tray_icon.setContextMenu(self._menu_builder.build_menu())
        self._tray_icon.activated.connect(self._on_activated)

    def _connect_signals(self) -> None:
        """Connect menu signals."""
        self._menu_builder.view_stats_triggered.connect(self._show_stats)
        self._menu_builder.refresh_triggered.connect(self._refresh)
        self._menu_builder.settings_triggered.connect(self._show_settings)
        self._menu_builder.quit_triggered.connect(self._quit)

    def start(self) -> None:
        """Start the app."""
        logger.info("Starting tray app")
        self._tray_icon.show()
        self._refresh()  # Initial refresh
        self._timer.start(self._settings.refresh_rate * 1000)

    def _refresh(self) -> None:
        """Refresh status data."""
        logger.debug("Refreshing status")

        # Generate fresh status file
        plan = self._settings.plan
        write_status_file(plan)

        # Read status
        self._status = read_status_file()

        if self._status and "error" not in self._status:
            self._update_from_status()
        else:
            self._show_error()

        # Update stats window if open
        if self._stats_window and self._stats_window.isVisible():
            self._stats_window.update_status(self._status)

    def _update_from_status(self) -> None:
        """Update tray from status data."""
        if not self._status:
            return

        session = self._status.get("session", {})
        tokens_pct = session.get("tokens_pct", 0)

        # Update icon
        ratio = tokens_pct / 100.0
        self._tray_icon.setIcon(self._icon_manager.get_icon_for_usage(ratio))

        # Update tooltip
        tokens = session.get("tokens", 0)
        limit = self._status.get("token_limit", 0)
        cost = session.get("cost", 0)
        reset = self._format_reset(session.get("reset_time", ""))

        tooltip = (
            f"Claude Monitor\n"
            f"Tokens: {self._fmt_num(tokens)} / {self._fmt_num(limit)} ({tokens_pct}%)\n"
            f"Cost: ${cost:.2f}\n"
            f"{reset}"
        )
        self._tray_icon.setToolTip(tooltip)

    def _show_error(self) -> None:
        """Show error state."""
        self._tray_icon.setIcon(self._icon_manager.get_icon(IconState.ERROR))
        error = self._status.get("error", "Unknown error") if self._status else "No data"
        self._tray_icon.setToolTip(f"Claude Monitor\nError: {error}")

    def _format_reset(self, reset_time: str) -> str:
        """Format reset time."""
        if not reset_time:
            return ""
        try:
            if "+" in reset_time:
                reset_time = reset_time.split("+")[0]
            end = datetime.fromisoformat(reset_time)
            now = datetime.now()
            if end > now:
                delta = end - now
                hours = int(delta.total_seconds() // 3600)
                mins = int((delta.total_seconds() % 3600) // 60)
                return f"Resets in {hours}h {mins}m"
        except:
            pass
        return ""

    def _fmt_num(self, n: int) -> str:
        """Format number."""
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}k"
        return str(n)

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_stats()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            self._refresh()

    def _show_stats(self) -> None:
        """Show stats window."""
        if not self._stats_window:
            self._stats_window = StatsWindow()
        self._stats_window.update_status(self._status)
        self._stats_window.show()
        self._stats_window.raise_()
        self._stats_window.activateWindow()

    def _show_settings(self) -> None:
        """Show settings dialog."""
        dialog = SettingsDialog(
            settings=self._settings,
            autostart_available=self._autostart_manager.is_available(),
        )
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()

    @pyqtSlot(object)
    def _on_settings_changed(self, new_settings: TraySettings) -> None:
        """Handle settings change."""
        self._settings = new_settings
        self._settings_manager.save(new_settings)

        # Update thresholds
        self._icon_manager.update_thresholds(
            new_settings.warning_threshold,
            new_settings.critical_threshold,
        )

        # Update timer
        self._timer.setInterval(new_settings.refresh_rate * 1000)

        # Update autostart
        self._autostart_manager.set_enabled(new_settings.autostart)

        # Refresh now
        self._refresh()

    def _quit(self) -> None:
        """Quit the app."""
        logger.info("Quitting")
        self._timer.stop()
        self._tray_icon.hide()
        self.quit()
