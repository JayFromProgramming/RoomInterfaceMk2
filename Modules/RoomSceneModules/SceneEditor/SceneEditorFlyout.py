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
        self.action_device_list = DeviceColumn(self, "Action Devices", api_action)
        self.available_device_list = DeviceColumn(self, "Available Devices")

        # Move both lists to the very right
        self.action_device_list.move(self.width() - self.action_device_list.width() - 10, 5)
        # Put the available devices to the left of the action devices
        self.available_device_list.move(self.action_device_list.x() - self.available_device_list.width() - 10, 5)



