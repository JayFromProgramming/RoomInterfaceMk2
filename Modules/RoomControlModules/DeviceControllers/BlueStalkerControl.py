import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton

from Utils.RoomDevice import RoomDevice
from loguru import logger as logging


class BlueStalkerControl(RoomDevice):
    supported_types = ["BlueStalker", "satellite_BlueStalker"]

    def __init__(self, parent=None, device=None):
        super().__init__(parent.auth, parent, device, True)

        self.device_label.setFont(parent.font)
        self.device_label.setFixedSize(300, 20)
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.device_label.setStyleSheet(
            "color: black; font-size: 15px; font-weight: bold; border: none; background-color: transparent")
        self.device_label.setText(f"{device}")
        self.device_label.move(10, 0)

        self.info_text = QLabel(self)
        self.info_text.setFixedSize(200, 75)
        self.info_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.info_text.setStyleSheet(
            "color: black; font-size: 14px; font-weight: bold; border: none; background-color: transparent")
        self.info_text.setText("<pre>Last Scan: UNKNOWN\nOccupants: N/A\nHealth: N/A</pre>")
        self.info_text.move(10, 20)
        self.info_text.setFont(parent.font)

        self.toggle_button = QPushButton(self)
        self.toggle_button.setFixedSize(90, 30)
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey")
        self.toggle_button.setText("?????")
        self.toggle_button.move(self.width() - self.toggle_button.width() - 10, 5)
        self.toggle_button.clicked.connect(self.toggle_device)
        self.toggle_button.setFont(parent.font)

    def update_human_name(self, name):
        super().update_human_name(name)
        self.device_label.setText(f"{name}")

    @staticmethod
    def parse_health(health):
        if not health["online"]:
            return f"Offline: {health['reason']}"
        elif health["fault"]:
            return f"Fault: {health['reason']}"
        else:
            return "Watching"

    def parse_data(self, data):
        try:
            last_scan = data['info']["last_scan"]
            last_scan = datetime.datetime.fromtimestamp(last_scan).strftime('%H:%M:%S')
            occupants = self.state["occupants"]
            health = self.parse_health(data['health'])

            self.info_text.setText(f"<pre>Last Scan: {last_scan}\nOccupants: {occupants}\nHealth: {health}</pre>")
            # self.toggle_button.setText("Disable" if self.state["on"] else "Enable")
        except Exception as e:
            self.info_text.setText(f"<pre>Last Scan: UNKNOWN\nOccupants: N/A\nHealth: N/A</pre>")
            logging.error(f"Failed to parse BlueStalker data: {e}")

    def toggle_device(self):
        command = {"on": not self.state["on"]}
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: blue;")
        self.send_command(command)
