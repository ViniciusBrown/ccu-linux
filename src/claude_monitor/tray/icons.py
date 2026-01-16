"""Tray icon generation with color-coded status indicators."""

import logging
from enum import Enum
from typing import Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

logger = logging.getLogger(__name__)


class IconState(Enum):
    """Icon state representing usage level."""

    NORMAL = "normal"  # Green - under warning threshold
    WARNING = "warning"  # Yellow - between warning and critical
    CRITICAL = "critical"  # Red - above critical threshold
    LOADING = "loading"  # Gray - data loading
    ERROR = "error"  # Gray with X - error state


class TrayIconManager:
    """Manages tray icon generation with color-coded status."""

    # Color definitions
    COLORS: Dict[IconState, QColor] = {
        IconState.NORMAL: QColor(76, 175, 80),  # Green
        IconState.WARNING: QColor(255, 193, 7),  # Yellow/Amber
        IconState.CRITICAL: QColor(244, 67, 54),  # Red
        IconState.LOADING: QColor(158, 158, 158),  # Gray
        IconState.ERROR: QColor(117, 117, 117),  # Dark Gray
    }

    ICON_SIZE = 22  # Standard system tray icon size

    def __init__(
        self,
        warning_threshold: float = 0.70,
        critical_threshold: float = 0.90,
    ) -> None:
        """Initialize icon manager.

        Args:
            warning_threshold: Usage ratio for warning state (0.0-1.0)
            critical_threshold: Usage ratio for critical state (0.0-1.0)
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self._icon_cache: Dict[IconState, QIcon] = {}

    def get_icon_for_usage(self, usage_ratio: float) -> QIcon:
        """Get appropriate icon based on usage ratio.

        Args:
            usage_ratio: Current usage as ratio (0.0-1.0)

        Returns:
            QIcon with appropriate color
        """
        state = self._get_state_for_ratio(usage_ratio)
        return self.get_icon(state)

    def get_icon(self, state: IconState) -> QIcon:
        """Get icon for a specific state.

        Args:
            state: IconState enum value

        Returns:
            QIcon for the state
        """
        if state not in self._icon_cache:
            self._icon_cache[state] = self._create_icon(state)
        return self._icon_cache[state]

    def _get_state_for_ratio(self, ratio: float) -> IconState:
        """Determine icon state based on usage ratio.

        Args:
            ratio: Usage ratio (0.0-1.0)

        Returns:
            IconState for the ratio
        """
        if ratio < 0:
            return IconState.ERROR
        elif ratio >= self.critical_threshold:
            return IconState.CRITICAL
        elif ratio >= self.warning_threshold:
            return IconState.WARNING
        else:
            return IconState.NORMAL

    def _create_icon(self, state: IconState) -> QIcon:
        """Create a Claude Code style icon with '>_' prompt.

        Args:
            state: IconState to create icon for

        Returns:
            QIcon with Claude Code style terminal prompt
        """
        pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Get color for state
        color = self.COLORS.get(state, self.COLORS[IconState.LOADING])

        # Draw rounded rectangle background (dark)
        bg_color = QColor(30, 30, 30)
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        margin = 1
        painter.drawRoundedRect(
            margin,
            margin,
            self.ICON_SIZE - 2 * margin,
            self.ICON_SIZE - 2 * margin,
            4,
            4,
        )

        # Draw ">_" prompt in state color
        pen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)

        # Draw ">" chevron
        cx, cy = self.ICON_SIZE // 2, self.ICON_SIZE // 2
        painter.drawLine(4, cy - 4, 9, cy)
        painter.drawLine(9, cy, 4, cy + 4)

        # Draw "_" underscore/cursor
        painter.drawLine(11, cy + 4, 18, cy + 4)

        # Draw X overlay for error state
        if state == IconState.ERROR:
            pen = QPen(QColor(244, 67, 54))
            pen.setWidth(2)
            painter.setPen(pen)
            offset = 5
            painter.drawLine(
                cx - offset, cy - offset, cx + offset, cy + offset
            )
            painter.drawLine(
                cx - offset, cy + offset, cx + offset, cy - offset
            )

        painter.end()

        return QIcon(pixmap)

    def update_thresholds(
        self,
        warning_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
    ) -> None:
        """Update threshold values.

        Args:
            warning_threshold: New warning threshold (0.0-1.0)
            critical_threshold: New critical threshold (0.0-1.0)
        """
        if warning_threshold is not None:
            self.warning_threshold = warning_threshold
        if critical_threshold is not None:
            self.critical_threshold = critical_threshold

