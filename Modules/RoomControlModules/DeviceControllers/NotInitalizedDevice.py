import json

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton

from loguru import logger as logging

from Utils.RoomDevice import RoomDevice


class NotInitalizedDevice(RoomDevice):

    supported_types = []

    def __init__(self, parent=None, device=None, priority=0):
        super().__init__(parent.auth, parent, device, False, priority)

        # self.device_label.setFont(parent.font)
        # self.device_label.setFixedSize(135, 20)
        # self.device_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.device_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.device_label.setText(f"[{device}]")

        self.device_text = QLabel(self)
        self.device_text.setFont(parent.font)
        self.device_text.setFixedSize(135, 60)
        self.device_text.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.device_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none; background-color: transparent;")
        self.device_text.setText("<pre>UNSUPPORTED\n DEVICE TYPE</pre>")
        self.device_text.move(5, 15)

    def update_human_name(self, name):
        super().update_human_name(name)
        self.device_label.setText(name)

    def update_status(self):
        if self.not_found:
            self.device_text.setText(f"<pre>DEVICE NOT FOUND</pre>")
            return
        health = self.data["health"]
        if not health:
            self.device_text.setText(f"<pre>NO DATA\nDevice Type\nUnknown</pre>")
            return

    def parse_data(self, data):
        self.update_status()

    def handle_failure(self, response):
        self.device_text.setText(f"<pre>Server Error</pre>")
        # self.toggle_button.setText("Turn ???")
        self.device_text.setText(f"<pre>Network Error</pre>")
        # self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")
