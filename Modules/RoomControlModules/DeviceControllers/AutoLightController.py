import json

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton

from loguru import logger as logging

from Utils.RoomDevice import RoomDevice


class AutoLightController(RoomDevice):
    supported_types = ["light_controller"]

    def __init__(self, parent=None, device=None):
        super().__init__(parent.auth, parent, device, False)

        self.device_label = QLabel(self)
        self.device_label.setFont(parent.font)
        self.device_label.setFixedSize(135, 20)
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.device_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.device_label.setText(f"{device}")

        self.toggle_button = QPushButton(self)
        self.toggle_button.setFont(parent.font)
        self.toggle_button.setFixedSize(135, 30)
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey")
        self.toggle_button.setText("?????")
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_device)
        self.toggle_button.move(5, 40)

        self.device_text = QLabel(self)
        self.device_text.setFont(parent.font)
        self.device_text.setFixedSize(135, 20)
        self.device_text.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        self.device_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.device_text.setText("<pre>Status: ???</pre>")
        self.device_text.move(5, 20)

    def update_human_name(self, name):
        super().update_human_name(name)
        self.device_label.setText(name)

    def update_status(self):
        health = self.data["health"]
        if not health["online"]:
            self.device_text.setText(f"<pre>OFFLINE</pre>")
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")
        elif health["fault"]:
            self.device_text.setText(f"<pre>Online: FAULT</pre>")
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: orange;")
        elif self.state["on"]:
            match self.state["current_state"]:
                case 0:
                    self.device_text.setText(f"<pre>Online: IDLE</pre>")
                case 1:
                    self.device_text.setText(f"<pre>Online: MOTION</pre>")
                case 2:
                    self.device_text.setText(f"<pre>Online: ACTIVE</pre>")
        else:
            self.device_text.setText(f"<pre>Online: STANDBY</pre>")

    def parse_data(self, data):
        self.toggle_button.setText(f"{['Enable', 'Disable'][self.state['on']]}")
        button_color = "#4080FF" if self.state["on"] else "grey"
        self.toggle_button.setStyleSheet(f"color: black; font-size: 14px; font-weight: bold; background-color: {button_color};")
        self.update_status()

    def handle_failure(self, response):
        self.device_text.setText(f"<pre>Server Error</pre>")
        self.toggle_button.setText("Turn ???")
        self.device_text.setText(f"<pre>Network Error</pre>")
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")
