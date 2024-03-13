import json

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging


class DeviceTile(QLabel):

    def __init__(self, parent=None, device=None, action_data=None):
        super().__init__(parent)
        self.parent = parent
        self.auth = parent.auth
        self.host = parent.host
        self.device = device
        self.data = None
        self.type = "Unknown"
        self.action_data = action_data
        self.font = parent.font
        self.setFixedSize(280, 55)
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")

        self.device_label = QLabel(self)
        self.device_label.setFont(self.font)
        self.device_label.setFixedSize(280, 20)
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.device_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;"
                                        "background-color: transparent")
        self.device_label.setText(f"{device}")
        self.device_label.move(0, 0)

        self.action_text = QLabel(self)
        self.action_text.setFont(self.font)
        self.action_text.setFixedSize(280, 20)
        self.action_text.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.action_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;"
                                       "background-color: transparent")
        self.action_text.setText("<pre>Action: ???</pre>")
        self.action_text.move(0, 15)

        self.device_text = QLabel(self)
        self.device_text.setFont(self.font)
        self.device_text.setFixedSize(280, 20)
        self.device_text.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        self.device_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;"
                                       "background-color: transparent")
        self.device_text.setText("<pre>Status: ???</pre>")
        self.device_text.move(0, 35)

        self.parent.make_name_request(device)

        self.info_getter = QNetworkAccessManager()
        self.info_getter.finished.connect(self.handle_info_response)

        self.setToolTip(f"Double click to edit {device}")

        self.get_data()
        self.update_action_text()

    def update_device_text(self):
        self.device_text.setText(f"<pre>Type: {self.type}</pre>")

    def update_action_text(self):
        if self.action_data is None:
            self.action_text.setText("<pre>Actions: Not Set</pre>")
            return
        text = "<pre>Actions: "
        for key, action in self.action_data.items():
            text += f"{key}: {action}, "
        text = text[:-2]
        text += "</pre>"
        self.action_text.setText(text)

    def generate_action_data(self):
        """
        Use the devices current state to generate a dictionary of actions that would set the device to that state
        """
        pass

    def handle_info_response(self, reply):
        try:
            data = reply.readAll()
            if data == b"Device not found":
                self.device_text.setText("<pre>Status: Device not found</pre>")
                return
            self.data = json.loads(str(data, 'utf-8'))
            self.type = self.data["type"]
            self.update_device_text()
            if self.action_data is not None:
                self.update_action_text()
        except Exception as e:
            logging.error(f"Error handling network response for device {self.device}: {e}")
            logging.exception(e)

    def get_data(self):
        request = QNetworkRequest(QUrl(f"http://{self.host}/get/{self.device}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        self.info_getter.get(request)

    def update_human_name(self, name):
        self.device_label.setText(name)
