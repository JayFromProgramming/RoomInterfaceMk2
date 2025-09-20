import json

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton, QDialog, QMessageBox, QProgressDialog, QApplication, QInputDialog
from loguru import logger as logging

from Modules.RoomSceneModules.SceneEditor.DeviceActionEditor import DeviceActionEditor
from Modules.RoomSceneModules.SceneEditor.DeviceColumn import DeviceColumn
from Modules.RoomSceneModules.SceneEditor.TriggerColumn import TriggerColumn
from Utils.UtilMethods import get_host, get_auth


class SceneEditorFlyout(QDialog):
    def __init__(self, parent=None, scene_id=None, data=None):
        super().__init__()
        self.parent = parent
        self.scene_id = scene_id
        self.starting_data = data
        self.font = self.parent.font

        self.is_new = True if scene_id is None and data is None else False
        self.is_new_folder = True if scene_id is None and data is not None and data["data"] == "{\"folder\":\"\"}" else False
        self.has_set_name = False

        # If both the scene_id and data are None, we are creating a new scene
        if self.is_new:
            self.setWindowTitle("Create New Routine")
            self.starting_data = {
                "name": "Unnamed Scene",
                "description": "Double click to edit",
                "parent": self.parent.current_top_folder,
                "triggers": [],
                "data": None
            }
            logging.debug(f"Creating new scene in folder {self.starting_data['parent']}")
        elif self.is_new_folder:
            self.setWindowTitle("Creating New Folder")
            self.starting_data = {
                "name": "Unnamed Folder",
                "parent": data["parent"],
                "triggers": [],
                "data": None
            }

        # This is a flyout (popup) that will be used to edit a scene
        self.setStyleSheet("background-color: transparent")
        self.setFixedSize(1024, 600)
        self.setWindowTitle(f"Routine Editor: {self.starting_data['name']}")
        # self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint)

        self.title_label = QLabel(self)
        self.title_label.setFont(self.font)
        self.title_label.setFixedSize(1024, 20)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.title_label.setStyleSheet("color: #ffcd00; font-size: 16px; font-weight: bold; border: none;")
        self.title_label.setText(f"Editing Routine: {self.starting_data['name']}")
        self.title_label.mousePressEvent = self.titleClicked

        self.selected_trigger_list = TriggerColumn(self, "Selected Automatic Triggers")
        self.selected_trigger_list.setFixedSize(400, round((self.height() - 110) / 2) - 20)
        self.selected_trigger_list.move(10, 25)
        for trigger in self.starting_data['triggers']:
            self.selected_trigger_list.add_trigger(trigger['trigger_type'], trigger)
        self.selected_trigger_list.layout_widgets()

        self.available_trigger_list = TriggerColumn(self, "Available Automatic Triggers")
        self.available_trigger_list.setFixedSize(400, round((self.height() - 110) / 2))
        self.available_trigger_list.move(10, self.selected_trigger_list.y() + self.selected_trigger_list.height() + 10)
        self.available_trigger_list.load_default_triggers()

        if self.starting_data['data'] is not None and len(self.starting_data['data']) > 0:
            api_action = json.loads(self.starting_data["data"])
        else:
            api_action = {}

        self.action_device_list = DeviceColumn(self, "Selected Devices", api_action)
        self.action_device_list.placeholder_label.setText("No Devices Selected\nFor This Scene"
                                                          "\n---\nClick Devices To Add Them")

        # Get the list of available devices from the master schema

        self.available_device_list = DeviceColumn(self, "Available Devices")

        # Move both lists to the very right
        self.action_device_list.move(self.width() - self.action_device_list.width() - 10, 25)
        # Put the available devices to the left of the action devices
        self.available_device_list.move(self.action_device_list.x() - self.available_device_list.width() - 10, 25)

        # self.action_editor = DeviceActionEditor(self)

        self.schema_getter = QNetworkAccessManager()
        self.schema_getter.finished.connect(self.handle_schema_response)

        self.scene_request = QNetworkAccessManager()
        self.scene_request.finished.connect(self.handle_scene_response)

        self.save_button = QPushButton(self)
        self.save_button.setFont(self.font)
        self.save_button.setFixedSize(195, 30)
        self.save_button.setText(f"Save Routine{' As New' if self.is_new else ''}")
        self.save_button.move(10, self.available_trigger_list.y() + self.available_trigger_list.height() + 10)
        self.save_button.setStyleSheet("background-color: green; border: none; border-radius: 10px; font-style: bold; font-size: 12px")
        self.save_button.show()
        self.save_button.clicked.connect(self.save_scene)

        self.test_button = QPushButton(self)
        self.test_button.setFont(self.font)
        self.test_button.setFixedSize(195, 30)
        self.test_button.setText("Test Routine")
        self.test_button.move(10, self.save_button.y() + self.save_button.height() + 10)
        self.test_button.setStyleSheet("background-color: #4080FF; border: none; border-radius: 10px; font-style: bold; font-size: 12px")
        self.test_button.show()

        self.cancel_button = QPushButton(self)
        self.cancel_button.setFont(self.font)
        self.cancel_button.setFixedSize(195, 30)
        self.cancel_button.setText("Cancel Changes")
        self.cancel_button.move(self.save_button.x() + self.save_button.width() + 10, self.save_button.y())
        self.cancel_button.setStyleSheet(
            "background-color: orange; border: none; border-radius: 10px; font-style: bold; font-size: 12px")
        self.cancel_button.show()
        self.cancel_button.clicked.connect(self.close)

        self.delete_button = QPushButton(self)
        self.delete_button.setFont(self.font)
        self.delete_button.setFixedSize(195, 30)
        self.delete_button.setText("Delete Routine")
        self.delete_button.move(self.cancel_button.x(),
                                self.cancel_button.y() + self.cancel_button.height() + 10)
        self.delete_button.setStyleSheet("background-color: red; border: none; border-radius: 10px; font-style: bold; font-size: 12px")
        self.delete_button.show()
        self.delete_button.clicked.connect(self.delete_scene)

        self.get_schema()

        # If a new folder is being created, then this window will be short lived.
        # This window will send the request to create the folder and then close itself
        if self.is_new_folder:
            self.starting_data = {
                "name": data["name"],
                "parent": data["parent"],

            }
            self.setWindowTitle(f"Creating Folder: {self.starting_data['name']}")
            self.send_save_request("add_scene", "{\"folder\":\"\"}",
                                   [], scene_parent=self.starting_data['parent'])
            return

        # Check if the main window is full screen, if so make this window full screen on top of it
        active_window = QApplication.instance().activeWindow()
        if active_window.isFullScreen():
            self.setWindowState(Qt.WindowState.WindowFullScreen)

    def closeEvent(self, a0) -> None:
        # Mark all objects for garbage collection
        self.schema_getter.deleteLater()
        self.scene_request.deleteLater()
        for tile in self.action_device_list.device_labels:
            tile.deleteLater()
        self.action_device_list.deleteLater()
        for tile in self.available_device_list.device_labels:
            tile.deleteLater()
        for trigger in self.selected_trigger_list.trigger_labels:
            trigger.deleteLater()
        for trigger in self.available_trigger_list.trigger_labels:
            trigger.deleteLater()
        self.deleteLater()

    def get_schema(self):
        try:
            request = QNetworkRequest(QUrl(f"{get_host()}/get_schema?interface_name=testing"))
            request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
            self.schema_getter.get(request)
        except Exception as e:
            logging.error(f"Error getting schema: {e}")
            logging.exception(e)

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
            devices = list(data.keys())
            devices.append("RoutineController")
            for device in devices:
                # Check if the device is already in the action list
                if self.action_device_list.has_device(device):
                    continue
                self.available_device_list.add_device(device)
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def transfer_device(self, source_column, tile):
        try:
            if source_column == self.available_device_list:
                self.action_device_list.add_device(self.available_device_list.remove_device(tile.device))
            else:
                self.available_device_list.add_device(self.action_device_list.remove_device(tile.device))
        except Exception as e:
            logging.error(f"Error transferring device: {e}")
            logging.exception(e)

    def transfer_trigger(self, trigger):
        try:
            if trigger in self.selected_trigger_list.trigger_labels:
                self.selected_trigger_list.remove_trigger(trigger)
                logging.debug(f"Removed trigger: {trigger.trigger_data}")
            else:
                self.selected_trigger_list.add_trigger(trigger.trigger_type, trigger.trigger_data)
                logging.debug(f"Added trigger: {trigger.trigger_data}")
        except Exception as e:
            logging.error(f"Error transferring trigger: {e}")
            logging.exception(e)

    def handle_scene_response(self, reply):
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
                exception_window.setWindowTitle("Error Processing Request")
                exception_window.setText(f"Server Error While Processing Request")
                exception_window.setInformativeText(data['result'])
                exception_window.setIcon(QMessageBox.Icon.Critical)
                exception_window.show()
                exception_window.exec()
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def send_save_request(self, action, new_action_data, new_trigger_data, description=None, scene_parent=None):
        request = QNetworkRequest(
            QUrl(f"{get_host()}/scene_action/{action}/{self.scene_id}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
        payload = {"scene_data": new_action_data, "triggers": new_trigger_data,
                   "scene_name": self.starting_data['name'], "scene_description": description,
                   "scene_parent": scene_parent}
        self.scene_request.post(request, bytes(json.dumps(payload), 'utf-8'))

    def save_scene(self):
        try:
            if self.is_new and not self.has_set_name:
                if not self.request_scene_name():
                    return
            new_action_data = {}
            for tile in self.action_device_list.device_labels:
                new_action_data[tile.device] = tile.action_data
            new_trigger_data = []
            for trigger in self.selected_trigger_list.trigger_labels:
                new_trigger_data.append(trigger.trigger_data)
            action = "add_scene" if self.is_new else "update_scene"
            self.send_save_request(action, new_action_data, new_trigger_data,
                                   description=self.starting_data['description'],
                                   scene_parent=self.starting_data['parent'])
            # self.processing_request_dialog.show()
        except Exception as e:
            exception_window = QDialog(self)
            exception_window.setFixedSize(400, 200)
            exception_window.setWindowTitle("Error Saving Scene")
            exception_window.show()
            logging.error(f"Error saving scene: {e}")
            logging.exception(e)

    def confirm_delete(self):
        confirm_window = QMessageBox()
        confirm_window.setFixedSize(400, 200)
        confirm_window.setWindowTitle("Confirm Delete")
        confirm_window.setText(f"Are you sure you want to delete the scene {self.starting_data['name']}?")
        confirm_window.setInformativeText("This action cannot be undone")
        confirm_window.setIcon(QMessageBox.Icon.Warning)
        confirm_window.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm_window.setDefaultButton(QMessageBox.StandardButton.No)
        confirm_window.show()
        result = confirm_window.exec()
        if result == 16384:
            return True
        return False

    def delete_scene(self):
        try:
            if self.confirm_delete():
                request = QNetworkRequest(
                    QUrl(f"{get_host()}/scene_action/delete_scene/{self.scene_id}"))
                request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
                self.scene_request.post(request, bytes(json.dumps({}), 'utf-8'))
        except Exception as e:
            exception_window = QDialog(self)
            exception_window.setFixedSize(400, 200)
            exception_window.setWindowTitle("Error Deleting Scene")
            exception_window.show()
            logging.error(f"Error deleting scene: {e}")
            logging.exception(e)

    def request_scene_name(self):
        rename_window = QInputDialog()
        rename_window.setFixedSize(200, 30)
        rename_window.setWindowTitle("Rename Scene")
        if self.is_new and not self.has_set_name:
            rename_window.setLabelText("New Scene Name:")
        else:
            rename_window.setLabelText("Scene Name:")
            rename_window.setTextValue(self.starting_data['name'])
        rename_window.setWindowFlag(Qt.WindowType.WindowCloseButtonHint)
        rename_window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        rename_window.setWindowFlag(Qt.WindowType.WindowTitleHint)
        result = rename_window.exec()
        if result == 1:
            new_name = rename_window.textValue()
            self.starting_data['name'] = new_name
            self.setWindowTitle(f"Scene Editor: {new_name}")
            return True
        return False

    def titleClicked(self, a0) -> None:
        try:
            self.request_scene_name()
            self.has_set_name = True
        except Exception as e:
            logging.error(f"Error renaming scene: {e}")
            logging.exception(e)
