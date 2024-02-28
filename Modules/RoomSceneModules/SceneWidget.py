import re

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging


class SceneWidget(QLabel):

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.parent = parent
        self.data = data
        self.font = self.parent.font
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")
        self.setFixedSize(500, 75)

        self.device_names = {}
        self.description = data["action"]

        # Network managers
        self.scene_caller = QNetworkAccessManager()
        self.scene_caller.finished.connect(self.handle_scene_response)
        self.device_name_getter = QNetworkAccessManager()
        self.device_name_getter.finished.connect(self.handle_device_name_response)

        # Labels
        self.scene_name_label = QLabel(self)
        self.scene_name_label.setFont(self.font)
        self.scene_name_label.setFixedSize(135, 20)
        self.scene_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.scene_name_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.scene_name_label.setText(f"{data['name']}")
        self.scene_name_label.move(5, 0)

        self.scene_description_label = QLabel(self)
        self.scene_description_label.setFont(self.font)
        self.scene_description_label.setFixedSize(490, 50)
        self.scene_description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.scene_description_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.scene_description_label.move(5, 20)
        self.scene_description_label.setWordWrap(True)
        self.scene_description_label.setText(f"<pre>{self.description}</pre>")
        self.request_names()

    def request_names(self):
        # Find all the device names in the action
        # Send a request for each device name
        regex = r"\[(.*?)\]"
        matches = re.findall(regex, self.description)
        for match in matches:
            request = QNetworkRequest(QUrl(f"http://{self.parent.host}/name/{match}"))
            request.setRawHeader(b"Cookie", bytes("auth=" + self.parent.auth, 'utf-8'))
            self.device_name_getter.get(request)

    def render_description(self):
        # Render the description with the device names replaced with the actual names
        regex = r"\[(.*?)\]"
        matches = re.findall(regex, self.description)
        rendered_description = self.description
        for match in matches:
            rendered_description = rendered_description.replace(f"[{match}]", self.device_names.get(match, match))
        self.scene_description_label.setText(f"<pre>{rendered_description}</pre>")

    def handle_scene_response(self, reply):
        pass

    def handle_device_name_response(self, reply):
        try:
            data = reply.readAll()
            device = reply.request().url().toString().split("/")[-1]
            self.device_names[device] = str(data, 'utf-8')
            self.render_description()
        except Exception as e:
            logging.error(f"Error handling device name response: {e}")
            logging.exception(e)
