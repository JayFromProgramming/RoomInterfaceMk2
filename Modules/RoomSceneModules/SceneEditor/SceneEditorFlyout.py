import json

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton, QDialog, QMessageBox, QProgressDialog, QApplication
from loguru import logger as logging

from Modules.RoomSceneModules.SceneEditor.DeviceActionEditor import DeviceActionEditor
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
        self.setFixedSize(1024, 600)
        self.setWindowTitle(f"Scene Editor: {data['scene_id']}")
        # self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint)

        self.selected_trigger_list = TriggerColumn(self, "Selected Triggers")
        self.selected_trigger_list.setFixedSize(400, round((self.height() - 100) / 2))
        self.selected_trigger_list.move(10, 5)
        self.selected_trigger_list.add_trigger(data['trigger_name'], {'trigger_type': data['trigger_type'],
                                                                      'trigger_value': data['trigger_value']})

        self.available_trigger_list = TriggerColumn(self, "Available Triggers")
        self.available_trigger_list.setFixedSize(400, round((self.height() - 100) / 2))
        self.available_trigger_list.move(10, self.selected_trigger_list.y() + self.selected_trigger_list.height() + 10)

        if data['api_action'] is not None and len(data['api_action']) > 0:
            api_action = json.loads(data["api_action"])
        else:
            api_action = {}

        self.action_device_list = DeviceColumn(self, "Selected Devices", api_action)
        self.action_device_list.placeholder_label.hide()

        # Get the list of available devices from the master schema

        self.available_device_list = DeviceColumn(self, "Available Devices")

        # Move both lists to the very right
        self.action_device_list.move(self.width() - self.action_device_list.width() - 10, 5)
        # Put the available devices to the left of the action devices
        self.available_device_list.move(self.action_device_list.x() - self.available_device_list.width() - 10, 5)

        # self.action_editor = DeviceActionEditor(self)

        self.schema_getter = QNetworkAccessManager()
        self.schema_getter.finished.connect(self.handle_schema_response)

        self.scene_saver = QNetworkAccessManager()
        self.scene_saver.finished.connect(self.handle_scene_save_response)

        # self.processing_request_dialog = QProgressDialog()
        # # self.processing_request_dialog.setFixedSize(400, 200)
        # self.processing_request_dialog.setWindowTitle("Processing Request")
        # self.processing_request_dialog.setLabelText("Please Wait...")
        # self.processing_request_dialog.setCancelButton(None)
        # # Set the progress to be indeterminate
        # self.processing_request_dialog.setRange(0, 0)
        # self.processing_request_dialog.hide()

        self.save_button = QPushButton(self)
        self.save_button.setFont(self.font)
        self.save_button.setFixedSize(195, 30)
        self.save_button.setText("Save Scene")
        self.save_button.move(10, self.available_trigger_list.y() + self.available_trigger_list.height() + 10)
        self.save_button.setStyleSheet("background-color: green; border: none; border-radius: 10px")
        self.save_button.show()
        self.save_button.clicked.connect(self.save_scene)

        self.test_button = QPushButton(self)
        self.test_button.setFont(self.font)
        self.test_button.setFixedSize(195, 30)
        self.test_button.setText("Test Scene")
        self.test_button.move(10, self.save_button.y() + self.save_button.height() + 10)
        self.test_button.setStyleSheet("background-color: #4080FF; border: none; border-radius: 10px")
        self.test_button.show()

        self.cancel_button = QPushButton(self)
        self.cancel_button.setFont(self.font)
        self.cancel_button.setFixedSize(195, 30)
        self.cancel_button.setText("Cancel Changes")
        self.cancel_button.move(self.save_button.x() + self.save_button.width() + 10, self.save_button.y())
        self.cancel_button.setStyleSheet("background-color: orange; border: none; border-radius: 10px")
        self.cancel_button.show()
        self.cancel_button.clicked.connect(self.close)

        self.delete_button = QPushButton(self)
        self.delete_button.setFont(self.font)
        self.delete_button.setFixedSize(195, 30)
        self.delete_button.setText("Delete Scene")
        self.delete_button.move(self.cancel_button.x(),
                                self.cancel_button.y() + self.cancel_button.height() + 10)
        self.delete_button.setStyleSheet("background-color: red; border: none; border-radius: 10px")
        self.delete_button.show()

        self.get_schema()

        # Check if the main window is full screen, if so make this window full screen on top of it
        active_window = QApplication.instance().activeWindow()
        if active_window.isFullScreen():
            self.setWindowState(Qt.WindowState.WindowFullScreen)

    def get_schema(self):
        try:
            request = QNetworkRequest(QUrl(f"http://{self.host}/get_schema"))
            request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
            self.schema_getter.get(request)
        except Exception as e:
            logging.error(f"Error getting schema: {e}")
            logging.exception(e)

    def handle_schema_response(self, reply):
        try:
            self.available_device_list.placeholder_label.hide()
            data = reply.readAll()
            try:
                data = json.loads(str(data, 'utf-8'))
            except Exception as e:
                logging.error(f"Error parsing network response: {e}")
                logging.error(f"Data: {data}")
                # self.loading_label.setText(f"Error Loading Room Control Schema, Retrying...\n{e}")
                return
            for device, value in data.items():
                # Check if the device is already in the action list
                if self.action_device_list.has_device(device):
                    continue
                self.available_device_list.add_device(device, value['group'])
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)

    def transfer_device(self, source_column, tile):
        try:
            if source_column == self.available_device_list:
                self.action_device_list.add_device(self.available_device_list.remove_device(tile.device))
            else:
                self.available_device_list.add_device(self.action_device_list.remove_device(tile.device))
        except Exception as e:
            logging.error(f"Error transferring device: {e}")
            logging.exception(e)

    def handle_scene_save_response(self, reply):
        try:
            data = reply.readAll()
            data = json.loads(str(data, 'utf-8'))
            if data["result"] == "success":
                self.parent.reload()
                # self.processing_request_dialog.hide()
                self.close()
            else:
                # self.processing_request_dialog.hide()
                exception_window = QMessageBox()
                exception_window.setFixedSize(400, 200)
                exception_window.setWindowTitle("Error Saving Scene")
                exception_window.setText(f"Server Error While Saving Scene")
                exception_window.setInformativeText(data['result'])
                exception_window.setIcon(QMessageBox.Icon.Critical)
                exception_window.show()
                exception_window.exec()
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)

    def save_scene(self):
        try:
            new_action_data = {}
            for tile in self.action_device_list.device_labels:
                new_action_data[tile.device] = tile.action_data
            print(new_action_data)
            request = QNetworkRequest(QUrl(f"http://{self.host}/update_scene/{self.starting_data['scene_id']}"))
            request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
            payload = {"scene_data": new_action_data}
            self.scene_saver.post(request, bytes(json.dumps(payload), 'utf-8'))
            # self.processing_request_dialog.show()
        except Exception as e:
            exception_window = QDialog(self)
            exception_window.setFixedSize(400, 200)
            exception_window.setWindowTitle("Error Saving Scene")
            exception_window.show()
            logging.error(f"Error saving scene: {e}")
            logging.exception(e)
