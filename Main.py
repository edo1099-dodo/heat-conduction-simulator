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

# Material presets: specific heat capacity in J/(kg*°C)
# Custom keeps 0.40 as default for fast demonstration
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
SIMULATION_DT = 0.05  # seconds per timer tick (50 ms)
EQUILIBRIUM_TOLERANCE = 0.25  # °C


def load_stylesheet(widget):
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

        # Simulation state
        self.body1 = None
        self.body2 = None
        self.dt = SIMULATION_DT
        self.elapsed_time = 0.0

        # Data lists for graphing and CSV export
        self.time_history = []
        self.body1_temp_history = []
        self.body2_temp_history = []

        # Simulation timer
        self.simulation_timer = QTimer(self)
        self.simulation_timer.setInterval(int(self.dt * 1000))
        self.simulation_timer.timeout.connect(self.timer_method)

        self.setupUI()
        load_stylesheet(self)

        self.left_temperature_changed()
        self.right_temperature_changed()

    def setupUI(self):
        self.setWindowTitle("Heat Transfer Simulator")
        self.setMinimumSize(780, 520)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(14)

        # Header bar
        header_layout = QHBoxLayout()
        title_label = QLabel("Heat Conduction Between Two Bodies")
        title_label.setObjectName("titleLabel")
        self.elapsed_time_label = QLabel("Time: 0.00 s")
        self.elapsed_time_label.setObjectName("sectionLabel")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.elapsed_time_label)
        root_layout.addLayout(header_layout)

        # Main 3-column layout
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(16)

        left_card = self.build_left_body_panel()
        center_card = self.build_center_panel()
        right_card = self.build_right_body_panel()

        columns_layout.addWidget(left_card, stretch=5)
        columns_layout.addWidget(center_card, stretch=4)
        columns_layout.addWidget(right_card, stretch=5)

        root_layout.addLayout(columns_layout, stretch=1)

        self.status_label = QLabel("Adjust temperatures using the sliders, then press Start.")
        self.status_label.setObjectName("statusLabel")
        root_layout.addWidget(self.status_label)

    def build_left_body_panel(self):
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        heading = QLabel("Body 1 (Left)")
        heading.setObjectName("sectionLabel")
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)

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

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        # Read-only temperature display (changed only with the slider)
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
        self.left_heat_cap_spinbox.valueChanged.connect(self.on_left_heat_cap_edited)

        self.left_material_combo = QComboBox()
        self.left_material_combo.addItems(MATERIAL_PRESETS.keys())
        self.left_material_combo.currentTextChanged.connect(self.apply_left_material)

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

    def build_right_body_panel(self):
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        heading = QLabel("Body 2 (Right)")
        heading.setObjectName("sectionLabel")
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)

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
        self.right_heat_cap_spinbox.valueChanged.connect(self.on_right_heat_cap_edited)

        self.right_material_combo = QComboBox()
        self.right_material_combo.addItems(MATERIAL_PRESETS.keys())
        self.right_material_combo.currentTextChanged.connect(self.apply_right_material)

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

    def build_center_panel(self):
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

        bridge_bar = QFrame()
        bridge_bar.setObjectName("bridgeBar")
        bridge_bar.setFixedHeight(22)

        self.heat_flow_label = QLabel("Heat Flow: ──▶")
        self.heat_flow_label.setObjectName("flowLabel")
        self.heat_flow_label.setAlignment(Qt.AlignCenter)

        self.auto_stop_checkbox = QCheckBox("Auto-stop at equilibrium")
        self.auto_stop_checkbox.setChecked(True)

        # Toggle button for Start / Stop
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

    # Map temperature [0, 200] across the full red channel [0, 255]
    def temp_to_red(self, temperature):
        clamped = max(MIN_TEMP, min(MAX_TEMP, temperature))
        return int(round((clamped / MAX_TEMP) * 255))

    def update_body_color(self, body_box, temperature):
        red = self.temp_to_red(temperature)
        body_box.setStyleSheet(
            f"background-color: rgb({red}, 0, 0);"
            "border: 2px solid #1e293b;"
            "border-radius: 8px;"
        )

    def update_heat_flow_indicator(self):
        t1 = self.left_temp_display.value()
        t2 = self.right_temp_display.value()
        diff = t1 - t2
        if abs(diff) < 0.05:
            self.heat_flow_label.setText("Thermal Equilibrium (═)")
        elif diff > 0:
            self.heat_flow_label.setText(f"Heat Flow: ──▶  ({diff:.1f} °C)")
        else:
            self.heat_flow_label.setText(f"Heat Flow: ◀──  ({abs(diff):.1f} °C)")

    def set_inputs_enabled(self, enabled):
        self.left_temp_slider.setEnabled(enabled)
        self.right_temp_slider.setEnabled(enabled)
        self.left_mass_spinbox.setEnabled(enabled)
        self.right_mass_spinbox.setEnabled(enabled)
        self.left_heat_cap_spinbox.setEnabled(enabled)
        self.right_heat_cap_spinbox.setEnabled(enabled)
        self.left_material_combo.setEnabled(enabled)
        self.right_material_combo.setEnabled(enabled)

    def apply_left_material(self, material_name):
        preset_value = MATERIAL_PRESETS.get(material_name)
        if preset_value is not None:
            self.left_heat_cap_spinbox.blockSignals(True)
            self.left_heat_cap_spinbox.setValue(preset_value)
            self.left_heat_cap_spinbox.blockSignals(False)

    def apply_right_material(self, material_name):
        preset_value = MATERIAL_PRESETS.get(material_name)
        if preset_value is not None:
            self.right_heat_cap_spinbox.blockSignals(True)
            self.right_heat_cap_spinbox.setValue(preset_value)
            self.right_heat_cap_spinbox.blockSignals(False)

    def on_left_heat_cap_edited(self):
        if self.left_material_combo.currentText() != "Custom":
            self.left_material_combo.blockSignals(True)
            self.left_material_combo.setCurrentText("Custom")
            self.left_material_combo.blockSignals(False)

    def on_right_heat_cap_edited(self):
        if self.right_material_combo.currentText() != "Custom":
            self.right_material_combo.blockSignals(True)
            self.right_material_combo.setCurrentText("Custom")
            self.right_material_combo.blockSignals(False)

    def left_temperature_changed(self):
        temp = float(self.left_temp_slider.value())
        self.left_temp_display.setValue(temp)
        self.update_body_color(self.left_body_box, temp)
        self.update_heat_flow_indicator()

    def right_temperature_changed(self):
        temp = float(self.right_temp_slider.value())
        self.right_temp_display.setValue(temp)
        self.update_body_color(self.right_body_box, temp)
        self.update_heat_flow_indicator()

    def start_stop_button_method(self, checked):
        if checked:
            t1 = self.left_temp_display.value()
            t2 = self.right_temp_display.value()

            self.body1 = Body(
                self.left_mass_spinbox.value(),
                self.left_heat_cap_spinbox.value(),
                t1,
            )
            self.body2 = Body(
                self.right_mass_spinbox.value(),
                self.right_heat_cap_spinbox.value(),
                t2,
            )

            # Reset history lists for the new experiment
            self.elapsed_time = 0.0
            self.time_history = [0.0]
            self.body1_temp_history = [self.body1.temperature]
            self.body2_temp_history = [self.body2.temperature]
            self.elapsed_time_label.setText("Time: 0.00 s")

            self.start_stop_button.setText("Stop")
            self.set_inputs_enabled(False)
            self.status_label.setText("Simulation running...")
            self.simulation_timer.start()
        else:
            self.simulation_timer.stop()
            self.start_stop_button.setText("Start")
            self.set_inputs_enabled(True)
            if not self.status_label.text().startswith("Equilibrium reached"):
                self.status_label.setText("Simulation stopped.")

    def timer_method(self):
        t1 = self.body1.temperature
        t2 = self.body2.temperature
        sigma = self.conductivity_spinbox.value()

        # Heat transfer equations
        i1 = sigma * (t2 - t1)
        i2 = sigma * (t1 - t2)

        heater1_watts = self.left_heater_spinbox.value()
        heater2_watts = self.right_heater_spinbox.value()

        delta_q1 = (i1 + heater1_watts) * self.dt
        delta_q2 = (i2 + heater2_watts) * self.dt

        new_t1 = self.body1.add_heat(delta_q1)
        new_t2 = self.body2.add_heat(delta_q2)

        # Save values for graphing
        self.elapsed_time += self.dt
        self.time_history.append(self.elapsed_time)
        self.body1_temp_history.append(new_t1)
        self.body2_temp_history.append(new_t2)

        # Update UI values, sliders, and colors
        self.elapsed_time_label.setText(f"Time: {self.elapsed_time:.2f} s")

        self.left_temp_display.setValue(new_t1)
        self.right_temp_display.setValue(new_t2)

        self.left_temp_slider.blockSignals(True)
        self.left_temp_slider.setValue(int(round(max(MIN_TEMP, min(MAX_TEMP, new_t1)))))
        self.left_temp_slider.blockSignals(False)

        self.right_temp_slider.blockSignals(True)
        self.right_temp_slider.setValue(int(round(max(MIN_TEMP, min(MAX_TEMP, new_t2)))))
        self.right_temp_slider.blockSignals(False)

        self.update_body_color(self.left_body_box, new_t1)
        self.update_body_color(self.right_body_box, new_t2)
        self.update_heat_flow_indicator()

        # Auto-stop at equilibrium when heaters are off
        if (
            self.auto_stop_checkbox.isChecked()
            and heater1_watts == 0.0
            and heater2_watts == 0.0
            and abs(new_t1 - new_t2) <= EQUILIBRIUM_TOLERANCE
        ):
            avg_temp = (new_t1 + new_t2) / 2
            self.status_label.setText(
                f"Equilibrium reached at {avg_temp:.1f} °C after {self.elapsed_time:.2f} s."
            )
            self.start_stop_button.setChecked(False)

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
