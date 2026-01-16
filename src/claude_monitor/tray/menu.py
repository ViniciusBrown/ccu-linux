"""Context menu builder for system tray."""

import logging
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu

logger = logging.getLogger(__name__)


class TrayMenuBuilder(QObject):
    """Builds and manages the system tray context menu."""

    # Signals
    view_stats_triggered = pyqtSignal()
    refresh_triggered = pyqtSignal()
    settings_triggered = pyqtSignal()
    quit_triggered = pyqtSignal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialize menu builder.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._menu: Optional[QMenu] = None
        self._actions: dict = {}

    def build_menu(self) -> QMenu:
        """Build the context menu.

        Returns:
            QMenu instance
        """
        self._menu = QMenu()

        # View Detailed Stats
        view_action = QAction("View Detailed Stats", self._menu)
        view_action.triggered.connect(self.view_stats_triggered.emit)
        self._menu.addAction(view_action)
        self._actions["view_stats"] = view_action

        self._menu.addSeparator()

        # Refresh Now
        refresh_action = QAction("Refresh Now", self._menu)
        refresh_action.triggered.connect(self.refresh_triggered.emit)
        self._menu.addAction(refresh_action)
        self._actions["refresh"] = refresh_action

        self._menu.addSeparator()

        # Settings
        settings_action = QAction("Settings...", self._menu)
        settings_action.triggered.connect(self.settings_triggered.emit)
        self._menu.addAction(settings_action)
        self._actions["settings"] = settings_action

        self._menu.addSeparator()

        # Quit
        quit_action = QAction("Quit", self._menu)
        quit_action.triggered.connect(self.quit_triggered.emit)
        self._menu.addAction(quit_action)
        self._actions["quit"] = quit_action

        logger.debug("Context menu built")
        return self._menu
