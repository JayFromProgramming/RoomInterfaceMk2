import json

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton, QDialog
from loguru import logger as logging

from Modules.RoomSceneModules.SceneEditor.DeviceColumn import DeviceColumn


class SceneEditorFlyout(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__()
        self.parent = parent
        self.host = parent.host
        self.auth = parent.auth
        self.starting_data = data
        self.font = self.parent.font

        # This is a flyout (popup) that will be used to edit a scene
        self.setStyleSheet("background-color: transparent")
        self.setFixedSize(800, 500)
        self.setWindowTitle(f"Scene Editor: {data['scene_id']}")
        # self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint)
        api_action = json.loads(data["api_action"])
        self.action_device_list = DeviceColumn(self, "Selected Devices", api_action)

        # Get the list of available devices from the master schema

        self.available_device_list = DeviceColumn(self, "Available Devices")

        # Move both lists to the very right
        self.action_device_list.move(self.width() - self.action_device_list.width() - 10, 5)
        # Put the available devices to the left of the action devices
        self.available_device_list.move(self.action_device_list.x() - self.available_device_list.width() - 10, 5)

        self.schema_getter = QNetworkAccessManager()
        self.schema_getter.finished.connect(self.handle_schema_response)

        self.get_schema()

    def get_schema(self):
        request = QNetworkRequest(QUrl(f"http://{self.host}/get_schema"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        self.schema_getter.get(request)

    def handle_schema_response(self, reply):
        try:
            data = reply.readAll()
            try:
                data = json.loads(str(data, 'utf-8'))
            except Exception as e:
                logging.error(f"Error parsing network response: {e}")
                logging.error(f"Data: {data}")
                # self.loading_label.setText(f"Error Loading Room Control Schema, Retrying...\n{e}")
                return
            for device in data.keys():
                # Check if the device is already in the action list
                if self.action_device_list.has_device(device):
                    continue
                self.available_device_list.add_device(device)
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
