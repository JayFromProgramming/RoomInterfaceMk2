import json
import time

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWidgets import QLabel, QPushButton

from loguru import logger as logging

from Utils.RoomDevice import RoomDevice
from Utils.UtilMethods import has_internet, network_error_to_string


class ToggleDevice(RoomDevice):
    supported_types = ["satellite_MotionDetector"]

    def __init__(self, parent=None, device=None, priority=0):
        super().__init__(parent.auth, parent, device, False, priority)

        self.device_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.device_label.setText(f"[{device}]")

        self.device_text = QLabel(self)
        self.device_text.setFont(parent.font)
        self.device_text.setFixedSize(135, 50)
        self.device_text.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        self.device_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.device_text.setText("<pre>Status: ???</pre>")
        self.device_text.move(5, 21)

    def update_human_name(self, name):
        super().update_human_name(name)
        self.device_label.setText(name)

    def parse_data(self, data):
        motion_detected = data["state"].get("motion_detected", False)
        last_motion_time = data["state"].get("last_motion_time", 0)
        if not isinstance(last_motion_time, int):
            last_motion_time = int(last_motion_time)
        last_motion_text = time.strftime('%Y-%m-%d\n%H:%M:%S', time.localtime(last_motion_time))
        if not motion_detected:
            self.device_text.setText(f"<pre>Last Motion\n{last_motion_text}</pre>")
        else:
            self.device_text.setText("<pre>Motion Detected</pre>")

    def handle_failure(self, response):
        has_network = has_internet()
        error_message = network_error_to_string(response, has_network)
        self.device_text.setText(f"<pre>{error_message}</pre>")