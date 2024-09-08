import json
import time

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWidgets import QLabel, QPushButton

from loguru import logger as logging

from Utils.RoomDevice import RoomDevice
from Utils.UtilMethods import has_internet


class ToggleDevice(RoomDevice):
    supported_types = ["VoiceMonkeyDevice", "abstract_toggle_device", "satellite_Relay"]

    def __init__(self, parent=None, device=None, priority=0):
        super().__init__(parent.auth, parent, device, False, priority)

        # self.device_label.setFont(parent.font)
        # self.device_label.setFixedSize(135, 20)
        # self.device_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.device_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.device_label.setText(f"[{device}]")

        self.toggle_button = QPushButton(self)
        self.toggle_button.setFont(parent.font)
        self.toggle_button.setFixedSize(135, 30)
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey")
        self.toggle_button.setText("Turn ???")
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_device)
        self.toggle_button.move(5, 40)

        self.device_text = QLabel(self)
        self.device_text.setFont(parent.font)
        self.device_text.setFixedSize(135, 20)
        self.device_text.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        self.device_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.device_text.setText("<pre>Status: ???</pre>")
        self.device_text.move(5, 21)

    def update_human_name(self, name):
        super().update_human_name(name)
        self.device_label.setText(name)

    def update_status(self):
        health = self.data["health"]
        if not health["online"]:
            self.device_text.setText(f"<pre>DEVICE OFFLINE</pre>")
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")
        elif health["fault"]:
            self.device_text.setText(f"<pre>Online: FAULT</pre>")
            self.toggle_button.setStyleSheet(
                "color: black; font-size: 14px; font-weight: bold; background-color: orange;")
        else:
            if "info" not in self.data or self.data["info"] is None:
                self.device_text.setText(f"<pre>Online: ???</pre>")
                return
            if "power" in self.data["info"] and self.state["on"]:
                self.device_text.setText(f"<pre>DRAW: {self.data['info']['power']}W</pre>")
            elif self.data["auto_state"]["is_auto"]:
                self.device_text.setText(f"<pre>Online: AUTO</pre>")
            else:
                self.device_text.setText(f"<pre>Online: MANUAL</pre>")

    def parse_data(self, data):
        if self.state is None:
            self.device_text.setText("<pre>DEVICE UNKNOWN</pre>")
            return
        if not self.toggling:
            self.toggle_button.setText(f"Turn {['On', 'Off'][self.state['on']]}")
            button_color = "#4080FF" if self.state["on"] else "grey"
            self.toggle_button.setStyleSheet(
                f"color: black; font-size: 14px; font-weight: bold; background-color: {button_color};")
            self.update_status()
        elif self.toggle_time < time.time() - 5:  # If the toggle has
            self.toggling = False
        else:
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold;"
                                             " background-color: blue;")

    def handle_failure(self, response):
        has_network = has_internet()
        if response.error() == QNetworkReply.NetworkError.ConnectionRefusedError:
            self.device_text.setText(f"<pre>SERVER DOWN</pre>")
        elif response.error() == QNetworkReply.NetworkError.OperationCanceledError and has_network:
            self.device_text.setText(f"<pre>SERVER OFFLINE</pre>")
        elif response.error() == QNetworkReply.NetworkError.InternalServerError:
            self.device_text.setText(f"<pre>SERVER ERROR</pre>")
        elif response.error() == QNetworkReply.NetworkError.OperationCanceledError and not has_network:
            self.device_text.setText(f"<pre>NETWORK ERROR</pre>")
        elif response.error() == QNetworkReply.NetworkError.HostNotFoundError and not has_network:
            self.device_text.setText(f"<pre>NO NETWORK</pre>")
        elif response.error() == QNetworkReply.NetworkError.HostNotFoundError and has_network:
            self.device_text.setText(f"<pre>SERVER NOT FOUND</pre>")
        elif response.error() == QNetworkReply.NetworkError.TemporaryNetworkFailureError:
            self.device_text.setText(f"<pre>NET FAILURE</pre>")
        elif response.error() == QNetworkReply.NetworkError.UnknownNetworkError and not has_network:
            self.device_text.setText(f"<pre>NET FAILURE</pre>")
        else:
            self.device_text.setText(f"<pre>UNKNOWN ERROR</pre>")
        self.toggle_button.setText("Turn ???")
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")
