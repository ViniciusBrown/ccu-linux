"""Simple stats window that displays status from JSON."""

from datetime import datetime
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class UsageRow(QWidget):
    """Usage row with progress bar."""

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)

        self._title = QLabel(title)
        self._title.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 13px;")
        layout.addWidget(self._title)

        self._subtitle = QLabel("")
        self._subtitle.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self._subtitle)

        row = QHBoxLayout()
        row.setSpacing(16)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._bar.setStyleSheet("""
            QProgressBar { background: #3a3a3a; border: none; border-radius: 4px; }
            QProgressBar::chunk { background: #5c9ce6; border-radius: 4px; }
        """)
        row.addWidget(self._bar, 1)

        self._pct = QLabel("0%")
        self._pct.setStyleSheet("color: #888888; font-size: 12px;")
        self._pct.setFixedWidth(60)
        self._pct.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(self._pct)

        layout.addLayout(row)

    def update(self, pct: int, subtitle: str = "") -> None:
        self._bar.setValue(min(100, max(0, pct)))
        self._pct.setText(f"{pct}%")
        self._subtitle.setText(subtitle)


class StatsWindow(QWidget):
    """Stats window styled like Claude.ai usage page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Claude Usage")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setFixedWidth(420)
        self.setStyleSheet("""
            QWidget { background: #2a2a2a; color: #e0e0e0; font-family: sans-serif; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # Title
        title = QLabel("Plan usage limits")
        title.setStyleSheet("font-weight: bold; font-size: 15px;")
        layout.addWidget(title)

        self._plan_label = QLabel("Plan: --")
        self._plan_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._plan_label)
        layout.addSpacing(12)

        # Token usage
        self._token_row = UsageRow("Token Usage")
        layout.addWidget(self._token_row)

        # Cost usage
        self._cost_row = UsageRow("Cost Usage")
        layout.addWidget(self._cost_row)

        # Message usage
        self._msg_row = UsageRow("Message Usage")
        layout.addWidget(self._msg_row)

        # Separator
        layout.addSpacing(8)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #3a3a3a;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        layout.addSpacing(8)

        # Time to reset
        self._reset_label = QLabel("Time to reset: --")
        self._reset_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self._reset_label)

        # Last updated
        layout.addSpacing(12)
        self._updated_label = QLabel("Last updated: --")
        self._updated_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self._updated_label)

    def update_status(self, status: Optional[Dict[str, Any]]) -> None:
        """Update from status dict."""
        if not status or "error" in status:
            self._plan_label.setText("Plan: Error")
            return

        plan = status.get("plan", "unknown")
        self._plan_label.setText(f"Plan: {plan}")

        session = status.get("session", {})

        # Tokens
        tokens = session.get("tokens", 0)
        token_limit = status.get("token_limit", 1)
        token_pct = session.get("tokens_pct", 0)
        self._token_row.update(token_pct, f"{self._fmt(tokens)} / {self._fmt(token_limit)}")

        # Cost
        cost = session.get("cost", 0)
        cost_limit = status.get("cost_limit", 1)
        cost_pct = session.get("cost_pct", 0)
        self._cost_row.update(cost_pct, f"${cost:.2f} / ${cost_limit:.2f}")

        # Messages
        msgs = session.get("messages", 0)
        msg_limit = status.get("message_limit", 1)
        msg_pct = session.get("messages_pct", 0)
        self._msg_row.update(msg_pct, f"{msgs} / {msg_limit}")

        # Reset time
        reset_time = session.get("reset_time", "")
        self._reset_label.setText(f"Time to reset: {self._fmt_reset(reset_time)}")

        # Updated
        ts = status.get("timestamp", "")
        self._updated_label.setText(f"Last updated: {self._fmt_time(ts)}")

    def _fmt(self, n: int) -> str:
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}k"
        return str(n)

    def _fmt_reset(self, reset_time: str) -> str:
        if not reset_time:
            return "--"
        try:
            if "+" in reset_time:
                reset_time = reset_time.split("+")[0]
            end = datetime.fromisoformat(reset_time)
            now = datetime.now()
            if end > now:
                delta = end - now
                h = int(delta.total_seconds() // 3600)
                m = int((delta.total_seconds() % 3600) // 60)
                return f"{h}h {m}m"
        except:
            pass
        return "--"

    def _fmt_time(self, ts: str) -> str:
        if not ts:
            return "--"
        try:
            dt = datetime.fromisoformat(ts)
            return dt.strftime("%H:%M:%S")
        except:
            return "--"
