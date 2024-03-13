import json

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton, QDialog
from loguru import logger as logging

from Modules.RoomSceneModules.SceneEditor.DeviceColumn import DeviceColumn
from Modules.RoomSceneModules.SceneEditor.TriggerColumn import TriggerColumn


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

        self.trigger_list = TriggerColumn(self)
        self.trigger_list.move(10, 5)
        # print(data)

        self.trigger_list.add_trigger(data['trigger_name'], {'trigger_type': data['trigger_type'],
                                                             'trigger_value': data['trigger_value']})

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

        self.save_button = QPushButton(self)
        self.save_button.setFont(self.font)
        self.save_button.setFixedSize(180, 40)
        self.save_button.setText("Save Scene")
        self.save_button.move(10, self.trigger_list.height() + 10)
        self.save_button.setStyleSheet("background-color: green; border: none; border-radius: 10px")
        self.save_button.show()
        self.save_button.clicked.connect(self.save_scene)

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

    def transfer_device(self, source_column, tile):
        if source_column == self.available_device_list:
            self.action_device_list.add_device(self.available_device_list.remove_device(tile.device))
        else:
            self.available_device_list.add_device(self.action_device_list.remove_device(tile.device))

    def save_scene(self):
        # trigger = self.trigger_list.get_trigger()
        # devices = self.action_device_list.get_devices()
        # self.parent.save_scene(self.starting_data["scene_id"], trigger, devices)
        self.close()
