import json
import random
import time

from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWidgets import QLabel, QMenu, QInputDialog, QDialog
from PyQt6.QtWidgets import QLineEdit, QComboBox, QDialogButtonBox, QFormLayout
from loguru import logger as logging

from Utils.UtilMethods import has_internet, get_auth, get_host


class RoomDevice(QLabel):

    supported_types = []

    @classmethod
    def supports_type(cls, device_type):
        return device_type in cls.supported_types

    def __init__(self, parent=None, device=None, large=False, priority=0, tall=False):
        super().__init__(parent)
        self.parent = parent
        self.device = device
        self.priority = priority
        self.device_type = False
        if tall:
            self.setFixedSize(295, 160)
        elif large:
            self.setFixedSize(295, 75)
        else:
            self.setFixedSize(145, 75)
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")
        self.not_found = False

        self.toggle_button = None

        self.device_label = QLabel(self)
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.device_label.setFixedSize(self.width(), 22)
        self.device_label.setFont(parent.font)

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_response)
        self.command_manager = QNetworkAccessManager()
        self.command_manager.finished.connect(self.handle_command)
        self.schema_manager = QNetworkAccessManager()
        self.schema_manager.finished.connect(self.handle_schema_update)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.get_data)
        self.refresh_timer.setSingleShot(True)

        self.name_update_timer = QTimer(self)
        self.name_update_timer.timeout.connect(lambda: self.parent.make_name_request(self.device))
        self.name_update_timer.setSingleShot(True)

        self.context_menu = QMenu(self)
        self.context_menu.addAction("Rename").triggered.connect(self.rename_device)
        self.context_menu.addAction("Edit Schema").triggered.connect(self.edit_schema)
        self.context_menu.setStyleSheet(
            "QMenu { background-color: #222; color: #f0f0f0; }"
            "QMenu::item { padding: 6px 16px; }"
            "QMenu::item:selected { background-color: #3a3a3a; }"
        )

        self.state = None
        self.data = None
        self.has_names = False
        self.human_name = None  # type: str | None

        self.toggling = False
        self.last_toggle_state = None
        self.toggle_time = 0

    def update_human_name(self, name):
        # print(f"Updating name to {name}")
        self.has_names = True
        self.human_name = name
        self.device_label.setText(name)
        if not self.isHidden():
            self.name_update_timer.start(300000 + random.randint(0, 60000))  # Update the name every 5-6 minutes
        else:
            self.name_update_timer.start(900000 + random.randint(0, 120000)) # Update the name every 15-17 minutes

    def hideEvent(self, a0):
        self.refresh_timer.stop()
        super().hideEvent(a0)

    def showEvent(self, a0):
        # Randomize the refresh time to prevent all the devices from refreshing at the same time
        self.refresh_timer.start(5000 + random.randint(0, 1000))
        self.get_data()
        if not self.has_names:
            self.parent.make_name_request(self.device)
        super().showEvent(a0)

    def get_data(self):
        request = QNetworkRequest(QUrl(f"{get_host()}/get/{self.device}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
        request.setTransferTimeout(5000)
        self.network_manager.get(request)

    def send_command(self, command):
        request = QNetworkRequest(QUrl(f"{get_host()}/set/{self.device}"))
        # Add a json payload to the post request
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
        payload = json.dumps(command)
        self.command_manager.post(request, payload.encode("utf-8"))
        self.refresh_timer.start(500)

    def _get_room_control_host(self):
        if self.parent is None:
            return None
        return getattr(self.parent, "parent", None)

    def _get_device_schema(self):
        room_control = self._get_room_control_host()
        if room_control is None:
            return {}
        schema_data = getattr(room_control, "schema_data", {})
        return schema_data.get(self.device, {})

    def _schema_group_starred_dialog(self):
        dialog = QDialog(self.window())
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.setWindowTitle("Schema")
        dialog.setStyleSheet(
            "QDialog { background-color: #000; color: #ffcd00; }"
            "QLabel { color: #ffcd00; }"
            "QLineEdit, QComboBox { background-color: #111; color: #ffcd00; border: 1px solid #ffcd00; }"
            "QDialogButtonBox QPushButton { background-color: #111; color: #ffcd00; border: 1px solid #ffcd00; padding: 4px 10px; }"
            "QDialogButtonBox QPushButton:pressed { background-color: #222; }"
        )
        target_width = max(400, round(self.window().width() * 0.5))
        dialog.resize(target_width, dialog.sizeHint().height())
        layout = QFormLayout(dialog)

        schema_info = self._get_device_schema()
        group_input = QLineEdit(dialog)
        group_input.setPlaceholderText("Blank for none")
        group_input.setText(schema_info.get("group", "") or "")

        starred_input = QComboBox(dialog)
        starred_input.addItems(["False", "True"])
        default_starred = bool(schema_info.get("starred", False))
        starred_input.setCurrentIndex(1 if default_starred else 0)

        priority_input = QLineEdit(dialog)
        priority_input.setPlaceholderText("Blank for none")
        priority_value = schema_info.get("priority", self.priority)
        priority_input.setText("" if priority_value is None else str(priority_value))

        layout.addRow("Group name:", group_input)
        layout.addRow("Starred:", starred_input)
        layout.addRow("Priority:", priority_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.setCenterButtons(True)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None, None, None
        group_name = group_input.text().strip()
        if group_name == "":
            group_name = None
        starred = starred_input.currentText() == "True"
        priority_text = priority_input.text().strip()
        if priority_text == "":
            priority = None
        else:
            priority = int(priority_text)
        return group_name, starred, priority

    def _edit_schema_flow(self):
        try:
            group_name, starred, priority = self._schema_group_starred_dialog()
            if group_name is None and starred is None and priority is None:
                return

            payload = {
                self.device: {
                    "group": group_name,
                    "starred": starred,
                    "priority": priority
                }
            }
            request = QNetworkRequest(QUrl(f"{get_host()}/update_device_schema?interface_name=testing"))
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
            request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
            self.schema_manager.post(request, json.dumps(payload).encode("utf-8"))
        except ValueError:
            logging.error("Invalid priority value entered")
        except Exception as e:
            logging.error(f"Error editing schema: {e}")
            logging.exception(e)

    def edit_schema(self):
        QTimer.singleShot(0, self._edit_schema_flow)

    def handle_schema_update(self, reply):
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                logging.error(f"Schema update error: {reply.errorString()}")
                return
            room_control = self._get_room_control_host()
            if room_control is not None and hasattr(room_control, "reload_schema"):
                QTimer.singleShot(500, room_control.reload_schema)
        except Exception as e:
            logging.error(f"Error handling schema update response: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def rename_device(self):
        try:
            diag = QInputDialog()
            diag.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            diag.setLabelText("Enter a new name for the device:")
            diag.setTextValue(self.human_name.replace("|", "") if self.human_name is not None else "")
            diag.setOkButtonText("Submit")
            diag.setCancelButtonText("Cancel")
            diag.exec()
            new_name = diag.textValue()
            if new_name == "":
                return
            request = QNetworkRequest(QUrl(f"{get_host()}/set_name/{self.device}/{new_name}"))
            request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
            self.command_manager.get(request)
            QTimer.singleShot(500, self.parent.widgets_rebuild)
        except Exception as e:
            logging.error(f"Error renaming device: {e}")
            logging.exception(e)

    def parse_data(self, data):
        raise NotImplementedError("This method must be implemented by the child class")

    def toggle_device(self):
        command = {"on": not self.state["on"]}
        if self.toggle_button is not None:
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold;"
                                             " background-color: blue;")
            self.toggling = True
            self.last_toggle_state = self.state["on"]
            self.toggle_time = time.time()
            # Increase the refresh rate so that we can see the change faster
            self.refresh_timer.start(500)
        self.send_command(command)

    def check_device_type(self, data):
        try:
            if "type" in data:
                if self.device_type is False:  # If the device type is not set (false instead of None because None is a valid type)
                    self.device_type = data["type"]
                else:
                    if self.device_type != data["type"]:
                        logging.error(f"Device type mismatch: {self.device_type} != {data['type']}")
                        self.parent.widgets_rebuild()  # Rebuild the widgets to fix the type mismatch
            else:
                logging.error(f"Device type not found in data: {data}")
        except Exception as e:
            logging.error(f"Error checking device type: {e}")
            logging.exception(e)

    def handle_response(self, response):
        try:
            if str(response.error()) != "NetworkError.NoError":
                logging.error(f"Device data error: {response.error()} : {has_internet()}")
                self.handle_failure(response)
                return
            data = response.readAll()
            if data == b'Device not found':
                self.not_found = True
                self.parse_data(None)
                return
            elif 'WOPR Login' in str(data):
                logging.error("Authentication error: WOPR Login found in response")
                self.handle_failure(response)
                return
            data = json.loads(str(data, 'utf-8'))
            self.data = data
            self.state = data["state"]
            self.check_device_type(data)
            if self.toggling and self.state["on"] != self.last_toggle_state:
                self.toggling = False
            self.parse_data(data)
        except Exception as e:
            logging.error(f"Error handling response: {e}")
            logging.exception(e)
        finally:
            if not self.toggling:
                self.refresh_timer.start(4000 + random.randint(0, 1500))
            else:
                self.refresh_timer.start(1000)
            response.deleteLater()

    def handle_command(self, response):
        try:
            # Check if the response code is 302
            response_code = response.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if response_code == 302 or response_code == 200:
                self.get_data()
            else:
                logging.error(f"Error handling command response: {response.error()}: {response_code}")
        except Exception as e:
            logging.error(f"Error handling command response: {e}")
            logging.exception(e)
        finally:
            response.deleteLater()

    def contextMenuEvent(self, ev):
        self.context_menu.exec(ev.globalPos())

    def handle_failure(self, response):
        raise NotImplementedError("This method must be implemented by the child class")
