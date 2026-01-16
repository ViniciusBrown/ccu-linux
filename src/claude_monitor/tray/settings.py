"""Tray-specific settings management."""

import json
import logging
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional

logger = logging.getLogger(__name__)


@dataclass
class TraySettings:
    """Settings for the system tray application."""

    refresh_rate: int = 60  # seconds
    plan: Literal["pro", "max5", "max20", "custom"] = "custom"
    custom_limit_tokens: Optional[int] = None
    warning_threshold: float = 0.70  # 70%
    critical_threshold: float = 0.90  # 90%
    autostart: bool = False
    show_notifications: bool = True
    notification_threshold: float = 0.90  # Notify at 90%

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "refresh_rate": self.refresh_rate,
            "plan": self.plan,
            "custom_limit_tokens": self.custom_limit_tokens,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "autostart": self.autostart,
            "show_notifications": self.show_notifications,
            "notification_threshold": self.notification_threshold,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraySettings":
        """Create settings from dictionary."""
        return cls(
            refresh_rate=data.get("refresh_rate", 60),
            plan=data.get("plan", "custom"),
            custom_limit_tokens=data.get("custom_limit_tokens"),
            warning_threshold=data.get("warning_threshold", 0.70),
            critical_threshold=data.get("critical_threshold", 0.90),
            autostart=data.get("autostart", False),
            show_notifications=data.get("show_notifications", True),
            notification_threshold=data.get("notification_threshold", 0.90),
        )


class TraySettingsManager:
    """Manages tray settings persistence."""

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """Initialize settings manager.

        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = config_dir or Path.home() / ".claude-monitor"
        self.settings_file = self.config_dir / "tray_settings.json"
        self._settings: Optional[TraySettings] = None

    def load(self) -> TraySettings:
        """Load settings from file.

        Returns:
            TraySettings instance
        """
        if self._settings is not None:
            return self._settings

        if not self.settings_file.exists():
            self._settings = TraySettings()
            return self._settings

        try:
            with open(self.settings_file) as f:
                data = json.load(f)

            self._settings = TraySettings.from_dict(data)
            logger.debug(f"Loaded tray settings from {self.settings_file}")
            return self._settings

        except Exception as e:
            logger.warning(f"Failed to load tray settings: {e}")
            self._settings = TraySettings()
            return self._settings

    def save(self, settings: TraySettings) -> bool:
        """Save settings to file.

        Args:
            settings: TraySettings instance to save

        Returns:
            True if successful, False otherwise
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            data = settings.to_dict()
            data["timestamp"] = datetime.now().isoformat()

            temp_file = self.settings_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.settings_file)

            self._settings = settings
            logger.debug(f"Saved tray settings to {self.settings_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save tray settings: {e}")
            return False

