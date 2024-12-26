import json

from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QInputDialog
from loguru import logger as logging

from Modules.RoomSceneModules.SceneEditor.SceneActionEditor import SceneActionEditor


class DeviceTile(QLabel):
    valid_actions = [
        'on', 'target_value', 'color',
        'white', 'brightness'
    ]  # Temporary until the server will return only valid actions in "state" field and other info in "info" field

    device_type_translation = {
        "light_controller": "Light Control",
        "VoiceMonkeyDevice": "Toggleable",
        "abstract_toggle_device": "Toggleable",
        "abstract_rgb": "Light",
        "environment_controller": "Environment",
        "LevitonDevice": "Switch",
    }

    def __init__(self, parent, device, group, action_data=None):
        super().__init__(parent)
        self.parent = parent
        self.auth = parent.auth
        self.host = parent.host
        self.device = device
        self.group = group

        self.human_name = None
        self.data = None
        self.type = "Unknown"
        self.supported_actions = []
        self.action_data = action_data

        self.font = parent.font
        self.setFixedSize(280, 55)
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")

        self.device_label = QLabel(self)
        self.device_label.setFont(self.font)
        self.device_label.setFixedSize(280, 20)
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.device_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;"
                                        "background-color: transparent")
        self.device_label.setText(f"{device}")
        self.device_label.move(5, 0)

        self.action_text = QLabel(self)
        self.action_text.setFont(self.font)
        self.action_text.setFixedSize(280, 40)
        self.action_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.action_text.setStyleSheet("color: black; font-size: 12px; font-weight: bold; border: none;"
                                       "background-color: transparent")
        self.action_text.setText("Actions: Not Set")
        self.action_text.move(2, 17)

        self.parent.make_name_request(device)

        self.info_getter = QNetworkAccessManager()
        self.info_getter.finished.connect(self.handle_info_response)

        self.single_click_timer = QTimer(self)
        self.single_click_timer.setSingleShot(True)
        self.single_click_timer.timeout.connect(self.mouseSingleClickEvent)
        self.double_click_occurred = False

        self.destroyed.connect(self.on_destroy)

        self.edit_dialog = None

        self.setToolTip(f"Double click to edit {device}")

        self.get_data()
        # self.update_action_text()

    def update_device_text(self):
        self.device_label.setText(f"{self.device_type_translation.get(self.type, self.type)}: {self.human_name}")
        self.parent.layout_widgets()

    def update_action_text(self):
        if self.action_data is None:
            self.action_text.setText("<pre>Actions: Not Set</pre>")
            return
        rows = []
        text = "Actions: "
        for key, action in self.action_data.items():
            # add carriage return if the text is too long
            if len(text) > 25:
                text = text[:-2]
                rows.append(text)
                text = ""
            text += f"{key.capitalize()}={action}, "
        if len(rows) >= 3:
            # If we have more than 3 rows we need to expand the tile's height to fit the text
            self.setFixedSize(280, 55 + (len(rows) - 2) * 20)
            self.action_text.setFixedSize(280, 40 + (len(rows) - 2) * 20)
        if text[-2:] == ", ":
            text = text[:-2]
        rows.append(text)
        text = "\n".join(rows)
        self.action_text.setText(text)

    def generate_action_data(self):
        """
        Use the devices current state to generate a dictionary of actions that would set the device to that state
        """
        self.action_data = {}
        if self.data["state"] is None:
            return
        for key, value in self.data["state"].items():
            if key in self.valid_actions:
                self.action_data[key] = value

        # If any of the action data is null it should be removed
        for key in list(self.action_data.keys()):
            if self.action_data[key] is None:
                del self.action_data[key]

        # Temporary fix until server code updated to handle
        # Color, White, and Brightness are mutually exclusive and should not be sent together
        # Prioritize white != 0, then color, then brightness
        # Additionally if any of these are present remove the "on" action
        if "on" in self.action_data and self.action_data["on"] is False:
            if "color" in self.action_data:
                del self.action_data["color"]
            if "brightness" in self.action_data:
                del self.action_data["brightness"]
            if "white" in self.action_data:
                del self.action_data["white"]
        elif "white" in self.action_data and self.action_data["white"] != 0:
            if "color" in self.action_data:
                del self.action_data["color"]
            if "brightness" in self.action_data:
                del self.action_data["brightness"]
        elif "color" in self.action_data:
            if "brightness" in self.action_data:
                del self.action_data["brightness"]
            if "white" in self.action_data:
                del self.action_data["white"]

        if "white" in self.action_data or "color" in self.action_data or "brightness" in self.action_data:
            if "on" in self.action_data:
                del self.action_data["on"]

    def handle_info_response(self, reply):
        try:
            data = reply.readAll()
            if data == b"Device not found":
                # self.device_text.setText("<pre>Status: Device not found</pre>")
                return
            self.data = json.loads(str(data, 'utf-8'))
            self.type = self.data["type"]
            self.supported_actions = self.data["actions"]
            self.update_device_text()
            if self.action_data is None:
                self.generate_action_data()
            self.update_action_text()
        except Exception as e:
            logging.error(f"Error handling network response for device {self.device}: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def get_data(self):
        request = QNetworkRequest(QUrl(f"http://{self.host}/get/{self.device}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        self.info_getter.get(request)

    def update_human_name(self, name):
        self.device_label.setText(f"{self.device_type_translation.get(self.type, self.type)}: {name}")
        self.human_name = name

    def mouseReleaseEvent(self, ev):
        try:
            if abs(self.parent.scroll_total_offset) > 5:
                super().mouseReleaseEvent(ev)
                return
            else:
                super().mouseReleaseEvent(ev)
            self.single_click_timer.start(450)
        except Exception as e:
            logging.error(f"Error in DeviceTile.mouseReleaseEvent: {e}")
            logging.exception(e)

    def mouseSingleClickEvent(self):
        try:
            if self.double_click_occurred:
                self.double_click_occurred = False
                return
            logging.debug(f"DeviceTile {self.device} clicked")
            self.parent.clicked(self)
        except Exception as e:
            logging.error(f"Error in DeviceTile.mouseSingleClickEvent: {e}")
            logging.exception(e)

    def mouseDoubleClickEvent(self, a0):
        super().mouseDoubleClickEvent(a0)
        try:
            self.double_click_occurred = True
            if self.edit_dialog is not None:
                return
            self.edit_dialog = SceneActionEditor(self.device, self.supported_actions, self.action_data)
            self.edit_dialog.set_submit_slot(self.edit_device_action)
            self.edit_dialog.destroyed.connect(self.edit_dialog_closed)
            self.edit_dialog.show()
        except Exception as e:
            logging.error(f"Error")
            logging.exception(e)

    def edit_dialog_closed(self):
        self.edit_dialog = None

    def edit_device_action(self, action):
        # Validate the input
        self.action_data = action
        self.update_action_text()

    def hideEvent(self, a0):
        if self.edit_dialog is not None:
            self.edit_dialog.close()
            self.edit_dialog = None

    def on_destroy(self):
        if self.edit_dialog is not None:
            self.edit_dialog.close()
            self.edit_dialog = None
        self.deleteLater()
        self.hide()

