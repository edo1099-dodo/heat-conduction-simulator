"""
GraphWindow.py
Secondary window for plotting temperature vs. time graphs and exporting data to CSV.
"""

import csv
import os
import subprocess
import sys

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def load_shared_stylesheet(widget: QWidget) -> None:
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as css_file:
            widget.setStyleSheet(css_file.read())


class GraphWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.plotted_labels = set()
        self.setupUI()
        load_shared_stylesheet(self)

    def setupUI(self):
        self.setWindowTitle("Graph Window - Heat Conduction")
        self.resize(780, 500)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Left side: Matplotlib canvas inside a clean card
        plot_card = QFrame()
        plot_card.setObjectName("cardFrame")
        plot_layout = QVBoxLayout(plot_card)
        plot_layout.setContentsMargins(10, 10, 10, 10)

        self.figure = Figure(figsize=(6, 4.5), dpi=100)
        self.figure.patch.set_facecolor("#ffffff")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self._format_axes()

        plot_layout.addWidget(self.canvas)
        main_layout.addWidget(plot_card, stretch=3)

        # Right side: Controls panel
        controls_card = QFrame()
        controls_card.setObjectName("cardFrame")
        controls_layout = QVBoxLayout(controls_card)
        controls_layout.setContentsMargins(14, 16, 14, 16)
        controls_layout.setSpacing(12)
        controls_layout.setAlignment(Qt.AlignTop)

        select_label = QLabel("Select Curve to Plot:")
        select_label.setObjectName("sectionLabel")

        self.body_selector = QComboBox()
        self.body_selector.addItems(["Body 1", "Body 2", "Both Bodies"])

        self.draw_button = QPushButton("Draw")
        self.draw_button.setObjectName("primaryButton")
        self.draw_button.clicked.connect(self.draw_graph)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_graph)

        self.export_csv_button = QPushButton("Export to CSV")
        self.export_csv_button.clicked.connect(self.export_to_csv)

        controls_layout.addWidget(select_label)
        controls_layout.addWidget(self.body_selector)
        controls_layout.addSpacing(6)
        controls_layout.addWidget(self.draw_button)
        controls_layout.addWidget(self.clear_button)
        controls_layout.addSpacing(12)
        controls_layout.addWidget(self.export_csv_button)
        controls_layout.addStretch()

        main_layout.addWidget(controls_card, stretch=1)

    def _format_axes(self):
        self.ax.set_title("Temperature vs. Time", fontsize=12, fontweight="bold", pad=10)
        self.ax.set_xlabel("Time (s)", fontsize=10)
        self.ax.set_ylabel("Temperature (°C)", fontsize=10)
        self.ax.grid(True, linestyle="--", alpha=0.45)
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.figure.tight_layout()

    def _plot_series(self, time_data, temp_data, label: str, color: str):
        # Avoid duplicate legend labels if the same body is drawn again
        plot_label = label if label not in self.plotted_labels else "_nolegend_"
        self.ax.plot(time_data, temp_data, label=plot_label, color=color, linewidth=2.2)
        self.plotted_labels.add(label)

    def draw_graph(self):
        time_data = self.main_window.time_history
        body1_data = self.main_window.body1_temp_history
        body2_data = self.main_window.body2_temp_history

        if not time_data:
            QMessageBox.information(
                self,
                "No Simulation Data",
                "Run the simulation first to collect temperature data.",
            )
            return

        selection = self.body_selector.currentText()
        if selection == "Body 1":
            self._plot_series(time_data, body1_data, "Body 1", "#dc2626")
        elif selection == "Body 2":
            self._plot_series(time_data, body2_data, "Body 2", "#2563eb")
        else:
            self._plot_series(time_data, body1_data, "Body 1", "#dc2626")
            self._plot_series(time_data, body2_data, "Body 2", "#2563eb")

        self._format_axes()
        self.ax.legend(loc="best", frameon=True)
        self.canvas.draw()

    def clear_graph(self):
        self.ax.clear()
        self.plotted_labels.clear()
        self._format_axes()
        self.canvas.draw()

    def export_to_csv(self):
        time_data = self.main_window.time_history
        body1_data = self.main_window.body1_temp_history
        body2_data = self.main_window.body2_temp_history

        if not time_data:
            QMessageBox.information(
                self,
                "No Simulation Data",
                "There is no experiment data to export yet. Run the simulation first.",
            )
            return

        csv_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "heat_conduction_data.csv"
        )

        try:
            with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Time (s)", "Body 1 Temperature (°C)", "Body 2 Temperature (°C)"])
                for t, t1, t2 in zip(time_data, body1_data, body2_data):
                    writer.writerow([f"{t:.3f}", f"{t1:.4f}", f"{t2:.4f}"])
        except OSError as exc:
            QMessageBox.critical(self, "Export Error", f"Failed to write CSV file:\n{exc}")
            return

        self._open_file_in_default_app(csv_path)

    @staticmethod
    def _open_file_in_default_app(file_path: str):
        try:
            if sys.platform.startswith("win"):
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", file_path])
            else:
                subprocess.Popen(["xdg-open", file_path])
        except Exception as exc:
            QMessageBox.warning(
                None,
                "File Saved",
                f"CSV saved to:\n{file_path}\n\nCould not open automatically: {exc}",
            )
