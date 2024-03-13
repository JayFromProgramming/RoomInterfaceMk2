import re

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton
from loguru import logger as logging
from Modules.RoomSceneModules.SceneEditor.SceneEditorFlyout import SceneEditorFlyout


class SceneWidget(QLabel):

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.parent = parent
        self.host = parent.host
        self.auth = parent.auth
        self.data = data
        self.font = self.parent.font
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")
        self.setFixedSize(500, 90)

        self.device_names = {}
        self.description = data["action"]

        self.is_immediate = data["trigger_type"] == "immediate"

        # Network managers
        self.scene_caller = QNetworkAccessManager()
        self.scene_caller.finished.connect(self.handle_scene_response)
        self.device_name_getter = QNetworkAccessManager()
        self.device_name_getter.finished.connect(self.handle_device_name_response)

        # Labels
        self.scene_name_label = QLabel(self)
        self.scene_name_label.setFont(self.font)
        if len(data["trigger_name"]) > 11:
            self.scene_name_label.setFixedSize(405, 20)
            self.scene_name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        else:
            self.scene_name_label.setFixedSize(105, 20)
            self.scene_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.scene_name_label.setStyleSheet("color: black; font-size: 16px; font-weight: bold; border: none;")
        self.scene_name_label.setText(f"{data['trigger_name']}")
        self.scene_name_label.move(7, 5)

        self.scene_description_label = QLabel(self)
        self.scene_description_label.setFont(self.font)
        self.scene_description_label.setFixedSize(380, 60)
        self.scene_description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.scene_description_label.setStyleSheet("color: black; font-size: 13px; font-weight: bold; "
                                                   "border: 2px solid black; border-radius: 10px; background-color: transparent;")
        self.scene_description_label.move(115, 25)
        self.scene_description_label.setWordWrap(True)
        self.scene_description_label.setText(f"<pre>{self.description}</pre>")

        self.scene_trigger_label = QLabel(self)
        self.scene_trigger_label.setFont(self.font)
        self.scene_trigger_label.setFixedSize(100, 20)
        self.scene_trigger_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.scene_trigger_label.setStyleSheet("color: black; font-size: 12px; font-weight: bold; border: none;")
        self.scene_trigger_label.move(7, 60)

        self.scene_trigger = QPushButton(self)
        self.scene_trigger.setFixedSize(100, 30)
        self.scene_trigger.setStyleSheet("color: white; font-size: 14px; font-weight: bold; background-color: grey;"
                                         "border: none; border-radius: 10px")
        if data["trigger_type"] == "immediate":
            self.scene_trigger.setText("Trigger")
            self.scene_trigger_label.setText("<pre>Immediate</pre>")
        else:
            self.scene_trigger.setText("Disable" if data["active"] else "Enable")
            self.scene_trigger_label.setText(f"<pre>{data['trigger_type']}@{data['trigger_value']}</pre>")
        self.scene_trigger.setFont(self.font)
        self.scene_trigger.clicked.connect(self.trigger_scene)
        self.scene_trigger.move(7, 30)

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

    def trigger_scene(self):
        request = QNetworkRequest(QUrl(f"http://{self.parent.host}/set_scene/{self.data['trigger_id']}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.parent.auth, 'utf-8'))
        self.scene_trigger.setStyleSheet("background-color: blue;")
        self.scene_caller.get(request)

    def render_description(self):
        # Render the description with the device names replaced with the actual names
        regex = r"\[(.*?)\]"
        matches = re.findall(regex, self.description)
        rendered_description = self.description
        for match in matches:
            rendered_description = rendered_description.replace(f"[{match}]", self.device_names.get(match, match))
            # If the length of the rendered description is greater than 100 characters, add a newline
        rendered_description = "<br>".join(self.split_description(rendered_description))
        self.scene_description_label.setText(f"<pre>{rendered_description}</pre>")

    def split_description(self, description):
        # Split the description into multiple lines
        lines = []
        current_line = ""
        for action in description.split(", "):
            if len(current_line + action) > 50:
                lines.append(current_line[:-2])
                current_line = ""
            current_line += f"{action}, "
        lines.append(current_line)
        return lines

    def handle_scene_response(self, reply):
        try:
            self.scene_trigger.setStyleSheet(
                "background-color: grey; color: white; font-size: 14px; font-weight: bold;")
        except Exception as e:
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

    def mouseDoubleClickEvent(self, a0) -> None:
        try:
            flyout = SceneEditorFlyout(self.parent, self.data)
            flyout.exec()
        except Exception as e:
            logging.error(f"Error opening scene editor flyout: {e}")
            logging.exception(e)
