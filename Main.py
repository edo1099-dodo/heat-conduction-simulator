"""
Main.py
Main GUI window and simulation engine for two-body heat conduction.
"""

import os
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from AboutWindow import AboutWindow
from Body import Body
from GraphWindow import GraphWindow

# Material presets: display name -> specific heat capacity in J/(kg*°C)
# "Custom" keeps the default assignment value (0.40) for rapid demonstration.
MATERIAL_PRESETS = {
    "Custom": None,
    "Lead (128)": 128.0,
    "Copper (385)": 385.0,
    "Iron (450)": 450.0,
    "Glass (840)": 840.0,
    "Aluminum (900)": 900.0,
    "Water (4186)": 4186.0,
}

MIN_TEMP = 0.0
MAX_TEMP = 200.0
SIMULATION_DT = 0.05  # seconds per simulation step (50 ms timer -> 20 FPS)
EQUILIBRIUM_TOLERANCE = 0.25  # °C difference for auto-stop


def load_shared_stylesheet(widget: QWidget) -> None:
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as css_file:
            widget.setStyleSheet(css_file.read())


class HeatTransfer(QWidget):
    def __init__(self):
        super().__init__()

        # Secondary windows
        self.graph_window = None
        self.about_window = None

        # Physics & simulation state
        self.body1 = None
        self.body2 = None
        self.dt = SIMULATION_DT
        self.elapsed_time = 0.0

        # Experiment history lists (shared with GraphWindow)
        self.time_history = []
        self.body1_temp_history = []
        self.body2_temp_history = []

        # Simulation timer
        self.simulation_timer = QTimer(self)
        self.simulation_timer.setInterval(int(self.dt * 1000))
        self.simulation_timer.timeout.connect(self.timer_method)

        self.setupUI()
        load_shared_stylesheet(self)

        # Initialize visual body colors and flow indicator from initial slider values
        self.left_temperature_changed()
        self.right_temperature_changed()

    def setupUI(self):
        self.setWindowTitle("Heat Transfer Simulator")
        self.setMinimumSize(780, 520)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(14)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Heat Conduction Between Two Bodies")
        title_label.setObjectName("titleLabel")
        self.elapsed_time_label = QLabel("Time: 0.00 s")
        self.elapsed_time_label.setObjectName("sectionLabel")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.elapsed_time_label)
        root_layout.addLayout(header_layout)

        # Main 3-column layout: Left Body | Center Bridge & Controls | Right Body
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(16)

        left_card = self._build_left_body_panel()
        center_card = self._build_center_panel()
        right_card = self._build_right_body_panel()

        columns_layout.addWidget(left_card, stretch=5)
        columns_layout.addWidget(center_card, stretch=4)
        columns_layout.addWidget(right_card, stretch=5)

        root_layout.addLayout(columns_layout, stretch=1)

        # Bottom status line
        self.status_label = QLabel("Adjust temperatures using the sliders, then press Start.")
        self.status_label.setObjectName("statusLabel")
        root_layout.addWidget(self.status_label)

    def _build_left_body_panel(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        heading = QLabel("Body 1 (Left)")
        heading.setObjectName("sectionLabel")
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)

        # Slider + Colored Body block
        visual_layout = QHBoxLayout()
        visual_layout.setSpacing(12)

        self.left_temp_slider = QSlider(Qt.Vertical)
        self.left_temp_slider.setRange(int(MIN_TEMP), int(MAX_TEMP))
        self.left_temp_slider.setValue(200)
        self.left_temp_slider.setMinimumHeight(180)
        self.left_temp_slider.valueChanged.connect(self.left_temperature_changed)

        self.left_body_box = QFrame()
        self.left_body_box.setMinimumSize(130, 180)

        visual_layout.addWidget(self.left_temp_slider)
        visual_layout.addWidget(self.left_body_box, stretch=1)
        layout.addLayout(visual_layout)

        # Parameter grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        # Temperature (read-only display; modified only via slider)
        self.left_temp_display = QDoubleSpinBox()
        self.left_temp_display.setRange(-1000.0, 10000.0)
        self.left_temp_display.setDecimals(1)
        self.left_temp_display.setSuffix(" °C")
        self.left_temp_display.setValue(200.0)
        self.left_temp_display.setReadOnly(True)
        self.left_temp_display.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.left_mass_spinbox = QDoubleSpinBox()
        self.left_mass_spinbox.setRange(0.01, 10000.0)
        self.left_mass_spinbox.setDecimals(2)
        self.left_mass_spinbox.setSingleStep(1.0)
        self.left_mass_spinbox.setSuffix(" kg")
        self.left_mass_spinbox.setValue(10.00)

        self.left_heat_cap_spinbox = QDoubleSpinBox()
        self.left_heat_cap_spinbox.setRange(0.01, 10000.0)
        self.left_heat_cap_spinbox.setDecimals(2)
        self.left_heat_cap_spinbox.setSingleStep(0.10)
        self.left_heat_cap_spinbox.setSuffix(" J/kg°C")
        self.left_heat_cap_spinbox.setValue(0.40)
        self.left_heat_cap_spinbox.valueChanged.connect(self._on_left_heat_cap_manual_edit)

        self.left_material_combo = QComboBox()
        self.left_material_combo.addItems(MATERIAL_PRESETS.keys())
        self.left_material_combo.currentTextChanged.connect(self._apply_left_material_preset)

        self.left_heater_spinbox = QDoubleSpinBox()
        self.left_heater_spinbox.setRange(0.0, 500.0)
        self.left_heater_spinbox.setDecimals(1)
        self.left_heater_spinbox.setSingleStep(5.0)
        self.left_heater_spinbox.setSuffix(" W")
        self.left_heater_spinbox.setValue(0.0)

        grid.addWidget(QLabel("Temp.:"), 0, 0)
        grid.addWidget(self.left_temp_display, 0, 1)
        grid.addWidget(QLabel("Mass:"), 1, 0)
        grid.addWidget(self.left_mass_spinbox, 1, 1)
        grid.addWidget(QLabel("H. Cap.:"), 2, 0)
        grid.addWidget(self.left_heat_cap_spinbox, 2, 1)
        grid.addWidget(QLabel("Material:"), 3, 0)
        grid.addWidget(self.left_material_combo, 3, 1)
        grid.addWidget(QLabel("Heater:"), 4, 0)
        grid.addWidget(self.left_heater_spinbox, 4, 1)

        layout.addLayout(grid)
        return card

    def _build_right_body_panel(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        heading = QLabel("Body 2 (Right)")
        heading.setObjectName("sectionLabel")
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)

        # Colored Body block + Slider on the right
        visual_layout = QHBoxLayout()
        visual_layout.setSpacing(12)

        self.right_body_box = QFrame()
        self.right_body_box.setMinimumSize(130, 180)

        self.right_temp_slider = QSlider(Qt.Vertical)
        self.right_temp_slider.setRange(int(MIN_TEMP), int(MAX_TEMP))
        self.right_temp_slider.setValue(0)
        self.right_temp_slider.setMinimumHeight(180)
        self.right_temp_slider.valueChanged.connect(self.right_temperature_changed)

        visual_layout.addWidget(self.right_body_box, stretch=1)
        visual_layout.addWidget(self.right_temp_slider)
        layout.addLayout(visual_layout)

        # Parameter grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        self.right_temp_display = QDoubleSpinBox()
        self.right_temp_display.setRange(-1000.0, 10000.0)
        self.right_temp_display.setDecimals(1)
        self.right_temp_display.setSuffix(" °C")
        self.right_temp_display.setValue(0.0)
        self.right_temp_display.setReadOnly(True)
        self.right_temp_display.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.right_mass_spinbox = QDoubleSpinBox()
        self.right_mass_spinbox.setRange(0.01, 10000.0)
        self.right_mass_spinbox.setDecimals(2)
        self.right_mass_spinbox.setSingleStep(1.0)
        self.right_mass_spinbox.setSuffix(" kg")
        self.right_mass_spinbox.setValue(10.00)

        self.right_heat_cap_spinbox = QDoubleSpinBox()
        self.right_heat_cap_spinbox.setRange(0.01, 10000.0)
        self.right_heat_cap_spinbox.setDecimals(2)
        self.right_heat_cap_spinbox.setSingleStep(0.10)
        self.right_heat_cap_spinbox.setSuffix(" J/kg°C")
        self.right_heat_cap_spinbox.setValue(0.40)
        self.right_heat_cap_spinbox.valueChanged.connect(self._on_right_heat_cap_manual_edit)

        self.right_material_combo = QComboBox()
        self.right_material_combo.addItems(MATERIAL_PRESETS.keys())
        self.right_material_combo.currentTextChanged.connect(self._apply_right_material_preset)

        self.right_heater_spinbox = QDoubleSpinBox()
        self.right_heater_spinbox.setRange(0.0, 500.0)
        self.right_heater_spinbox.setDecimals(1)
        self.right_heater_spinbox.setSingleStep(5.0)
        self.right_heater_spinbox.setSuffix(" W")
        self.right_heater_spinbox.setValue(0.0)

        grid.addWidget(QLabel("Temp.:"), 0, 0)
        grid.addWidget(self.right_temp_display, 0, 1)
        grid.addWidget(QLabel("Mass:"), 1, 0)
        grid.addWidget(self.right_mass_spinbox, 1, 1)
        grid.addWidget(QLabel("H. Cap.:"), 2, 0)
        grid.addWidget(self.right_heat_cap_spinbox, 2, 1)
        grid.addWidget(QLabel("Material:"), 3, 0)
        grid.addWidget(self.right_material_combo, 3, 1)
        grid.addWidget(QLabel("Heater:"), 4, 0)
        grid.addWidget(self.right_heater_spinbox, 4, 1)

        layout.addLayout(grid)
        return card

    def _build_center_panel(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(12)

        cond_label = QLabel("Conductivity (σ)")
        cond_label.setObjectName("sectionLabel")
        cond_label.setAlignment(Qt.AlignCenter)

        self.conductivity_spinbox = QDoubleSpinBox()
        self.conductivity_spinbox.setRange(0.01, 1000.0)
        self.conductivity_spinbox.setDecimals(2)
        self.conductivity_spinbox.setSingleStep(0.25)
        self.conductivity_spinbox.setSuffix(" J/s°C")
        self.conductivity_spinbox.setValue(1.00)

        # Visual conductive bridge connecting the two bodies
        bridge_bar = QFrame()
        bridge_bar.setObjectName("bridgeBar")
        bridge_bar.setFixedHeight(22)

        self.heat_flow_label = QLabel("Heat Flow: ──▶")
        self.heat_flow_label.setObjectName("flowLabel")
        self.heat_flow_label.setAlignment(Qt.AlignCenter)

        self.auto_stop_checkbox = QCheckBox("Auto-stop at equilibrium")
        self.auto_stop_checkbox.setChecked(True)

        # Start / Stop toggle button
        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.setObjectName("startStopButton")
        self.start_stop_button.setCheckable(True)
        self.start_stop_button.toggled.connect(self.start_stop_button_method)

        self.graphs_button = QPushButton("Graphs")
        self.graphs_button.clicked.connect(self.open_graph_window)

        self.about_button = QPushButton("About")
        self.about_button.clicked.connect(self.open_about_window)

        layout.addWidget(cond_label)
        layout.addWidget(self.conductivity_spinbox)
        layout.addSpacing(8)
        layout.addWidget(bridge_bar)
        layout.addWidget(self.heat_flow_label)
        layout.addStretch()
        layout.addWidget(self.auto_stop_checkbox)
        layout.addWidget(self.start_stop_button)
        layout.addWidget(self.graphs_button)
        layout.addWidget(self.about_button)

        return card

    # --- Visual helpers ---

    @staticmethod
    def _temperature_to_red_channel(temperature: float) -> int:
        clamped = max(MIN_TEMP, min(MAX_TEMP, temperature))
        return int(round((clamped / MAX_TEMP) * 255))

    def _update_body_color(self, body_box: QFrame, temperature: float):
        red = self._temperature_to_red_channel(temperature)
        body_box.setStyleSheet(
            f"background-color: rgb({red}, 0, 0);"
            "border: 2px solid #1e293b;"
            "border-radius: 8px;"
        )

    def _update_heat_flow_indicator(self):
        t1 = self.left_temp_display.value()
        t2 = self.right_temp_display.value()
        diff = t1 - t2
        if abs(diff) < 0.05:
            self.heat_flow_label.setText("Thermal Equilibrium (═)")
        elif diff > 0:
            self.heat_flow_label.setText(f"Heat Flow: ──▶  ({diff:.1f} °C)")
        else:
            self.heat_flow_label.setText(f"Heat Flow: ◀──  ({abs(diff):.1f} °C)")

    def _set_inputs_enabled(self, enabled: bool):
        self.left_temp_slider.setEnabled(enabled)
        self.right_temp_slider.setEnabled(enabled)
        self.left_mass_spinbox.setEnabled(enabled)
        self.right_mass_spinbox.setEnabled(enabled)
        self.left_heat_cap_spinbox.setEnabled(enabled)
        self.right_heat_cap_spinbox.setEnabled(enabled)
        self.left_material_combo.setEnabled(enabled)
        self.right_material_combo.setEnabled(enabled)

    # --- Material preset callbacks ---

    def _apply_left_material_preset(self, material_name: str):
        preset_value = MATERIAL_PRESETS.get(material_name)
        if preset_value is not None:
            self.left_heat_cap_spinbox.blockSignals(True)
            self.left_heat_cap_spinbox.setValue(preset_value)
            self.left_heat_cap_spinbox.blockSignals(False)

    def _apply_right_material_preset(self, material_name: str):
        preset_value = MATERIAL_PRESETS.get(material_name)
        if preset_value is not None:
            self.right_heat_cap_spinbox.blockSignals(True)
            self.right_heat_cap_spinbox.setValue(preset_value)
            self.right_heat_cap_spinbox.blockSignals(False)

    def _on_left_heat_cap_manual_edit(self):
        if self.left_material_combo.currentText() != "Custom":
            self.left_material_combo.blockSignals(True)
            self.left_material_combo.setCurrentText("Custom")
            self.left_material_combo.blockSignals(False)

    def _on_right_heat_cap_manual_edit(self):
        if self.right_material_combo.currentText() != "Custom":
            self.right_material_combo.blockSignals(True)
            self.right_material_combo.setCurrentText("Custom")
            self.right_material_combo.blockSignals(False)

    # --- Core simulation callbacks ---

    def left_temperature_changed(self):
        temp = float(self.left_temp_slider.value())
        self.left_temp_display.setValue(temp)
        self._update_body_color(self.left_body_box, temp)
        self._update_heat_flow_indicator()

    def right_temperature_changed(self):
        temp = float(self.right_temp_slider.value())
        self.right_temp_display.setValue(temp)
        self._update_body_color(self.right_body_box, temp)
        self._update_heat_flow_indicator()

    def start_stop_button_method(self, checked: bool):
        if checked:
            # Start a new experiment: initialize fresh bodies and reset history lists
            t1 = self.left_temp_display.value()
            t2 = self.right_temp_display.value()

            self.body1 = Body(
                mass=self.left_mass_spinbox.value(),
                heat_capacity=self.left_heat_cap_spinbox.value(),
                temperature=t1,
            )
            self.body2 = Body(
                mass=self.right_mass_spinbox.value(),
                heat_capacity=self.right_heat_cap_spinbox.value(),
                temperature=t2,
            )

            self.elapsed_time = 0.0
            self.time_history = [0.0]
            self.body1_temp_history = [self.body1.temperature]
            self.body2_temp_history = [self.body2.temperature]
            self.elapsed_time_label.setText("Time: 0.00 s")

            self.start_stop_button.setText("Stop")
            self._set_inputs_enabled(False)
            self.status_label.setText("Simulation running...")
            self.simulation_timer.start()
        else:
            # Stop the simulation
            self.simulation_timer.stop()
            self.start_stop_button.setText("Start")
            self._set_inputs_enabled(True)
            if not self.status_label.text().startswith("Equilibrium reached"):
                self.status_label.setText("Simulation stopped.")

    def timer_method(self):
        # 1. Physics equations for heat conduction + optional heaters
        t1 = self.body1.temperature
        t2 = self.body2.temperature
        sigma = self.conductivity_spinbox.value()

        i1 = sigma * (t2 - t1)
        i2 = sigma * (t1 - t2)

        heater1_watts = self.left_heater_spinbox.value()
        heater2_watts = self.right_heater_spinbox.value()

        delta_q1 = (i1 + heater1_watts) * self.dt
        delta_q2 = (i2 + heater2_watts) * self.dt

        # 2. Update body temperatures via Body.add_heat
        new_t1 = self.body1.add_heat(delta_q1)
        new_t2 = self.body2.add_heat(delta_q2)

        # 3. Record experiment history
        self.elapsed_time += self.dt
        self.time_history.append(self.elapsed_time)
        self.body1_temp_history.append(new_t1)
        self.body2_temp_history.append(new_t2)

        # 4. Update UI displays, sliders, and colors
        self.elapsed_time_label.setText(f"Time: {self.elapsed_time:.2f} s")

        self.left_temp_display.setValue(new_t1)
        self.right_temp_display.setValue(new_t2)

        self.left_temp_slider.blockSignals(True)
        self.left_temp_slider.setValue(int(round(max(MIN_TEMP, min(MAX_TEMP, new_t1)))))
        self.left_temp_slider.blockSignals(False)

        self.right_temp_slider.blockSignals(True)
        self.right_temp_slider.setValue(int(round(max(MIN_TEMP, min(MAX_TEMP, new_t2)))))
        self.right_temp_slider.blockSignals(False)

        self._update_body_color(self.left_body_box, new_t1)
        self._update_body_color(self.right_body_box, new_t2)
        self._update_heat_flow_indicator()

        # 5. Bonus: Auto-stop when thermal equilibrium is reached (with heaters off)
        if (
            self.auto_stop_checkbox.isChecked()
            and heater1_watts == 0.0
            and heater2_watts == 0.0
            and abs(new_t1 - new_t2) <= EQUILIBRIUM_TOLERANCE
        ):
            self.status_label.setText(
                f"Equilibrium reached at {((new_t1 + new_t2) / 2):.1f} °C after {self.elapsed_time:.2f} s."
            )
            self.start_stop_button.setChecked(False)

    # --- Secondary windows ---

    def open_graph_window(self):
        if self.graph_window is None:
            self.graph_window = GraphWindow(self)
        self.graph_window.show()
        self.graph_window.raise_()
        self.graph_window.activateWindow()

    def open_about_window(self):
        if self.about_window is None:
            self.about_window = AboutWindow()
        self.about_window.show()
        self.about_window.raise_()
        self.about_window.activateWindow()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HeatTransfer()
    window.show()
    sys.exit(app.exec())
