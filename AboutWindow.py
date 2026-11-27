"""
AboutWindow.py
About window with project illustration, engineering overview, and clickable GitHub link.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

GITHUB_REPO_URL = "https://github.com/edo1099-dodo/heat-conduction-simulator"


def load_shared_stylesheet(widget: QWidget) -> None:
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as css_file:
            widget.setStyleSheet(css_file.read())


class AboutWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUI()
        load_shared_stylesheet(self)

    def setupUI(self):
        self.setWindowTitle("About - Heat Conduction Simulator")
        self.setFixedSize(480, 520)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(18, 18, 18, 18)

        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignTop)

        # Banner image
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        banner_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "about_banner.png")
        if os.path.exists(banner_path):
            pixmap = QPixmap(banner_path).scaled(
                400, 175, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("[Heat Conduction Diagram]")
        card_layout.addWidget(image_label)

        title_label = QLabel("Heat Conduction Simulator")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_label)

        subtitle_label = QLabel("Physics on Computer — Thermal Conduction Between Two Bodies")
        subtitle_label.setObjectName("sectionLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        card_layout.addWidget(subtitle_label)

        description_label = QLabel(
            "An interactive physics simulation modeling conductive heat transfer "
            "between two solid bodies using discrete time-stepping:\n"
            "• I = σ · ΔT,   ΔQ = I · Δt,   ΔT = ΔQ / (m · c)\n"
            "• Includes real-time thermal color mapping, material presets, "
            "external heaters (W), equilibrium auto-stop, plotting, and CSV export."
        )
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignLeft)
        card_layout.addWidget(description_label)

        author_label = QLabel("Author: Edo Goldstein  |  Mechanical Engineering")
        author_label.setObjectName("statusLabel")
        author_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(author_label)

        # Clickable GitHub link
        github_label = QLabel(
            f'GitHub Repository: <a href="{GITHUB_REPO_URL}">{GITHUB_REPO_URL}</a>'
        )
        github_label.setAlignment(Qt.AlignCenter)
        github_label.setOpenExternalLinks(True)
        github_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        github_label.setWordWrap(True)
        card_layout.addWidget(github_label)

        card_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.setObjectName("primaryButton")
        close_button.clicked.connect(self.close)
        card_layout.addWidget(close_button, alignment=Qt.AlignCenter)

        outer_layout.addWidget(card)
