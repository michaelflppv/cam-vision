"""Monochrome slider widget with value labels and interpretation.

Provides a styled slider with parameter name, current value display,
and contextual interpretation labels (e.g., "Strict", "Balanced", "Lenient").
"""

from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QSlider, QVBoxLayout, QWidget

from ..styles import fonts, tokens


class MonochromeSlider(QWidget):
    """Custom slider with labels and interpretation text.

    Features:
    - Parameter name label
    - Current value display
    - Interpretation label (context-aware)
    - Black square handle, black fill
    - Optional tick marks

    Signals:
        valueChanged: Emitted when slider value changes (float value)
    """

    valueChanged = Signal(float)

    def __init__(
        self,
        name: str,
        minimum: float = 0.0,
        maximum: float = 1.0,
        step: float = 0.01,
        default: float = 0.5,
        interpretation_func: Optional[Callable[[float], str]] = None,
        parent=None,
    ):
        """Initialize the monochrome slider.

        Args:
            name: Parameter name displayed as label
            minimum: Minimum value
            maximum: Maximum value
            step: Step size
            default: Default value
            interpretation_func: Function that returns interpretation text for a value
            parent: Parent widget
        """
        super().__init__(parent)
        self._name = name
        self._minimum = minimum
        self._maximum = maximum
        self._step = step
        self._interpretation_func = interpretation_func

        # Calculate integer range for QSlider (Qt uses int internally)
        self._int_minimum = 0
        self._int_maximum = int((maximum - minimum) / step)

        self._setup_ui()
        self.set_value(default)

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_TIGHT)

        # Parameter name label
        self.name_label = QLabel(self._name)
        font = QFont(fonts.get_system_font_name(), tokens.FONT_SIZE_NORMAL)
        font.setWeight(QFont.Weight.DemiBold)
        self.name_label.setFont(font)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self._int_minimum)
        self.slider.setMaximum(self._int_maximum)
        self.slider.valueChanged.connect(self._on_slider_changed)

        # Value label (centered, shows current value)
        self.value_label = QLabel()
        self.value_label.setAlignment(Qt.AlignCenter)
        value_font = QFont(fonts.get_system_font_name(), tokens.FONT_SIZE_NORMAL)
        value_font.setWeight(QFont.Weight.Bold)
        self.value_label.setFont(value_font)

        # Interpretation label (context-aware)
        self.interpretation_label = QLabel()
        self.interpretation_label.setAlignment(Qt.AlignCenter)
        self.interpretation_label.setObjectName("caption")

        # Add widgets to layout
        layout.addWidget(self.name_label)
        layout.addWidget(self.slider)
        layout.addWidget(self.value_label)
        if self._interpretation_func:
            layout.addWidget(self.interpretation_label)

    def _on_slider_changed(self, int_value: int):
        """Handle slider value change.

        Args:
            int_value: Integer slider value
        """
        real_value = self._int_to_float(int_value)
        self._update_labels(real_value)
        self.valueChanged.emit(real_value)

    def _int_to_float(self, int_value: int) -> float:
        """Convert integer slider value to float.

        Args:
            int_value: Integer value from QSlider

        Returns:
            Corresponding float value
        """
        return self._minimum + (int_value * self._step)

    def _float_to_int(self, float_value: float) -> int:
        """Convert float value to integer slider position.

        Args:
            float_value: Float value

        Returns:
            Corresponding integer position
        """
        return int((float_value - self._minimum) / self._step)

    def _update_labels(self, value: float):
        """Update value and interpretation labels.

        Args:
            value: Current slider value
        """
        # Update value label
        self.value_label.setText(f"{value:.2f}")

        # Update interpretation label if function provided
        if self._interpretation_func:
            interpretation = self._interpretation_func(value)
            self.interpretation_label.setText(interpretation)

    def set_value(self, value: float):
        """Set the slider value programmatically.

        Args:
            value: New value (will be clamped to min/max)
        """
        clamped = max(self._minimum, min(self._maximum, value))
        int_value = self._float_to_int(clamped)
        self.slider.setValue(int_value)
        self._update_labels(clamped)

    def get_value(self) -> float:
        """Get the current slider value.

        Returns:
            Current float value
        """
        return self._int_to_float(self.slider.value())

    def set_enabled(self, enabled: bool):
        """Enable or disable the slider.

        Args:
            enabled: True to enable, False to disable
        """
        self.slider.setEnabled(enabled)
        self.name_label.setEnabled(enabled)
        self.value_label.setEnabled(enabled)
        if self._interpretation_func:
            self.interpretation_label.setEnabled(enabled)
