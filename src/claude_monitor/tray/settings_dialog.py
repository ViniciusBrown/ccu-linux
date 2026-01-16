"""Settings dialog for tray configuration."""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from claude_monitor.core.plans import PLAN_LIMITS, PlanType
from claude_monitor.tray.settings import TraySettings

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Dialog for configuring tray settings."""

    settings_changed = pyqtSignal(object)  # Emits TraySettings

    def __init__(
        self,
        settings: TraySettings,
        autostart_available: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Initialize settings dialog.

        Args:
            settings: Current settings
            autostart_available: Whether autostart is available on this system
            parent: Parent widget
        """
        super().__init__(parent)
        self._settings = settings
        self._autostart_available = autostart_available

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Claude Monitor Tray Settings")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # General Settings Group
        general_group = QGroupBox("General")
        general_layout = QFormLayout(general_group)

        # Refresh rate
        self._refresh_spin = QSpinBox()
        self._refresh_spin.setRange(10, 300)
        self._refresh_spin.setSuffix(" seconds")
        self._refresh_spin.setToolTip("How often to refresh usage data")
        general_layout.addRow("Refresh Rate:", self._refresh_spin)

        layout.addWidget(general_group)

        # Plan Settings Group
        plan_group = QGroupBox("Plan")
        plan_layout = QFormLayout(plan_group)

        # Plan selector
        self._plan_combo = QComboBox()
        for plan_type in PlanType:
            display_name = PLAN_LIMITS[plan_type]["display_name"]
            self._plan_combo.addItem(display_name, plan_type.value)
        self._plan_combo.currentIndexChanged.connect(self._on_plan_changed)
        plan_layout.addRow("Plan Type:", self._plan_combo)

        # Custom limit
        self._custom_limit_spin = QSpinBox()
        self._custom_limit_spin.setRange(1000, 1_000_000)
        self._custom_limit_spin.setSingleStep(1000)
        self._custom_limit_spin.setSuffix(" tokens")
        self._custom_limit_spin.setToolTip("Token limit for custom plan")
        self._custom_limit_label = QLabel("Custom Limit:")
        plan_layout.addRow(self._custom_limit_label, self._custom_limit_spin)

        layout.addWidget(plan_group)

        # Thresholds Group
        threshold_group = QGroupBox("Thresholds")
        threshold_layout = QFormLayout(threshold_group)

        # Warning threshold
        self._warning_spin = QSpinBox()
        self._warning_spin.setRange(10, 100)
        self._warning_spin.setSuffix("%")
        self._warning_spin.setToolTip("Usage percentage for yellow icon")
        threshold_layout.addRow("Warning:", self._warning_spin)

        # Critical threshold
        self._critical_spin = QSpinBox()
        self._critical_spin.setRange(10, 100)
        self._critical_spin.setSuffix("%")
        self._critical_spin.setToolTip("Usage percentage for red icon")
        threshold_layout.addRow("Critical:", self._critical_spin)

        layout.addWidget(threshold_group)

        # Notifications Group
        notif_group = QGroupBox("Notifications")
        notif_layout = QFormLayout(notif_group)

        # Show notifications
        self._notifications_check = QCheckBox("Enable notifications")
        self._notifications_check.setToolTip("Show desktop notifications")
        notif_layout.addRow(self._notifications_check)

        # Notification threshold
        self._notif_threshold_spin = QSpinBox()
        self._notif_threshold_spin.setRange(10, 100)
        self._notif_threshold_spin.setSuffix("%")
        self._notif_threshold_spin.setToolTip("Usage percentage to trigger notification")
        notif_layout.addRow("Notify at:", self._notif_threshold_spin)

        layout.addWidget(notif_group)

        # Startup Group
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout(startup_group)

        # Autostart
        self._autostart_check = QCheckBox("Start with system")
        self._autostart_check.setToolTip("Launch tray app on login")
        if not self._autostart_available:
            self._autostart_check.setEnabled(False)
            self._autostart_check.setToolTip("Autostart not available on this system")
        startup_layout.addRow(self._autostart_check)

        layout.addWidget(startup_group)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_settings(self) -> None:
        """Load current settings into UI."""
        self._refresh_spin.setValue(self._settings.refresh_rate)

        # Set plan
        plan_index = self._plan_combo.findData(self._settings.plan)
        if plan_index >= 0:
            self._plan_combo.setCurrentIndex(plan_index)

        # Custom limit
        if self._settings.custom_limit_tokens:
            self._custom_limit_spin.setValue(self._settings.custom_limit_tokens)
        else:
            self._custom_limit_spin.setValue(44000)

        self._on_plan_changed()  # Update custom limit visibility

        # Thresholds
        self._warning_spin.setValue(int(self._settings.warning_threshold * 100))
        self._critical_spin.setValue(int(self._settings.critical_threshold * 100))

        # Notifications
        self._notifications_check.setChecked(self._settings.show_notifications)
        self._notif_threshold_spin.setValue(
            int(self._settings.notification_threshold * 100)
        )

        # Autostart
        self._autostart_check.setChecked(self._settings.autostart)

    def _on_plan_changed(self) -> None:
        """Handle plan selection change."""
        plan = self._plan_combo.currentData()
        is_custom = plan == "custom"

        self._custom_limit_label.setVisible(is_custom)
        self._custom_limit_spin.setVisible(is_custom)

    def _on_accept(self) -> None:
        """Handle OK button click."""
        # Validate thresholds
        warning = self._warning_spin.value()
        critical = self._critical_spin.value()

        if critical <= warning:
            critical = warning + 5
            self._critical_spin.setValue(min(100, critical))

        # Create updated settings
        new_settings = TraySettings(
            refresh_rate=self._refresh_spin.value(),
            plan=self._plan_combo.currentData(),
            custom_limit_tokens=(
                self._custom_limit_spin.value()
                if self._plan_combo.currentData() == "custom"
                else None
            ),
            warning_threshold=self._warning_spin.value() / 100.0,
            critical_threshold=self._critical_spin.value() / 100.0,
            autostart=self._autostart_check.isChecked(),
            show_notifications=self._notifications_check.isChecked(),
            notification_threshold=self._notif_threshold_spin.value() / 100.0,
        )

        self.settings_changed.emit(new_settings)
        self.accept()
