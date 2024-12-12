import json
import re

from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton
from loguru import logger as logging
from Modules.RoomSceneModules.SceneEditor.SceneEditorFlyout import SceneEditorFlyout


class SceneWidget(QLabel):

    def __init__(self, parent=None, scene_id=None, data=None, is_back_widget=False):
        super().__init__(parent)
        self.parent = parent
        self.is_back_widget = is_back_widget
        self.host = parent.host
        self.auth = parent.auth
        self.scene_id = scene_id
        self.data = data
        self.font = self.parent.font
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")
        self.setFixedSize(245, 90)

        self.device_names = {}
        self.is_new = False

        # If scene_id is None and data is None, this is a new scene
        if scene_id is None and data is None:
            self.is_new = True
            self.data = {
                "name": "Create New Scene",
                "description": "Double click to edit",
                "action": "",
                "parent": None,
                "data": "{}",
                "triggers": [],
                "trigger_type": "immediate"
            }

        self.parent_scene = self.data["parent"]

        if self.data["data"] == "{\"folder\": \"\"}":
            self.is_folder = True
        else:
            self.is_folder = False

        if is_back_widget:
            self.is_folder = True
            self.is_new = False
            self.data = {
                "name": "Back",
                "description": "Return to previous folder",
                "action": "",
                "parent": None,
                "data": "{}",
                "triggers": [],
                "trigger_type": "immediate"
            }

        self.description = self.data["description"] if "description" in self.data else "Failed to load description"
        self.description = self.description if self.description is not None else "No description set"

        # Labels
        self.scene_name_label = QLabel(self)
        self.scene_name_label.setFont(self.font)
        if self.data["name"] is None:
            self.data["name"] = "Unnamed Scene"
        self.scene_name_label.setFixedSize(self.width(), 20)
        self.scene_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.scene_name_label.setStyleSheet("color: black; font-size: 16px; font-weight: bold; border: none;")
        self.scene_name_label.setText(f"{self.data['name']}")
        self.scene_name_label.move(0, 5)

        self.scene_description_label = QLabel(self)
        self.scene_description_label.setFont(self.font)
        self.scene_description_label.setFixedSize(self.width() - 10, 23)
        self.scene_description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.scene_description_label.setStyleSheet("color: black; font-size: 13px; font-weight: bold; "
                                                   "border: 2px solid black; border-radius: 5px;"
                                                   " background-color: transparent;")
        self.scene_description_label.move(5, self.scene_name_label.y() + self.scene_name_label.height() + 2)
        self.scene_description_label.setWordWrap(True)
        self.scene_description_label.setText(f"<pre>{self.description}</pre>")

        self.scene_trigger = QPushButton(self)
        self.scene_trigger.setFixedSize(70, 30)
        self.scene_trigger.setStyleSheet("color: white; font-size: 14px; font-weight: bold; background-color: grey;"
                                         "border: none; border-radius: 10px")
        if self.is_new:
            self.scene_trigger.setText("N/A")
        elif self.is_folder:
            self.scene_trigger.setText("Open")
        else:
            self.scene_trigger.setText("Run")

        self.scene_trigger.setFont(self.font)
        self.scene_trigger.clicked.connect(self.trigger_scene)
        self.scene_trigger.move(5, self.height() - self.scene_trigger.height() - 5)

        self.scene_trigger_label = QLabel(self)
        self.scene_trigger_label.setFont(self.font)
        self.scene_trigger_label.setFixedSize(self.width() - self.scene_trigger.width() - 10, 30)
        self.scene_trigger_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.scene_trigger_label.setStyleSheet("color: black; font-size: 12px; font-weight: bold; border: none;")

        trig_count = len(self.data['triggers'])
        enabled_trig_count = 0
        for trigger in self.data['triggers']:
            if trigger['enabled']:
                enabled_trig_count += 1
        try:
            act_count = len(json.loads(self.data['data']))
        except Exception as e:
            act_count = -1
        self.scene_trigger_label.setText(f"<pre>{trig_count} Trigger{'' if trig_count == 1 else 's'} | "
                                         f"{enabled_trig_count} Enabled\n"
                                         f"{act_count} Device{'' if act_count == 1 else 's'}</pre>")
        self.scene_trigger_label.move(self.scene_trigger.x() + self.scene_trigger.width() + 5, self.scene_trigger.y())

        self.double_click_timer = QTimer(self)
        self.double_click_timer.setSingleShot(True)
        self.double_click_primed = None

        self.scene_caller = QNetworkAccessManager()
        self.scene_caller.finished.connect(self.handle_scene_response)

        # self.request_names()

    # def request_names(self):
    #     # Find all the device names in the action
    #     # Send a request for each device name
    #     regex = r"\[(.*?)\]"
    #     matches = re.findall(regex, self.description)
    #     for match in matches:
    #         request = QNetworkRequest(QUrl(f"http://{self.parent.host}/name/{match}"))
    #         request.setRawHeader(b"Cookie", bytes("auth=" + self.parent.auth, 'utf-8'))
    #         self.device_name_getter.get(request)

    def trigger_scene(self):
        try:
            if self.is_folder:
                self.parent.open_folder(self.scene_id)
                return
            request = QNetworkRequest(QUrl(f"http://{self.parent.host}/scene_action/execute_scene/{self.scene_id}"))
            request.setRawHeader(b"Cookie", bytes("auth=" + self.parent.auth, 'utf-8'))
            self.scene_trigger.setStyleSheet("background-color: blue;")
            payload = {}
            self.scene_caller.post(request, bytes(json.dumps(payload), 'utf-8'))
        except Exception as e:
            logging.error(f"Error triggering scene: {e}")
            logging.exception(e)

    def handle_scene_response(self, reply):
        try:
            self.scene_trigger.setStyleSheet(
                "background-color: grey; color: white; font-size: 14px; font-weight: bold;")
        except Exception as e:
            pass
        finally:
            reply.deleteLater()

    def mousePressEvent(self, a0) -> None:
        # Manually check for double click events
        try:
            if self.double_click_primed:
                self.double_click_primed = False
                self.double_click_timer.stop()
                if self.is_folder:
                    self.parent.open_folder(self.scene_id)
                    return
                elif self.is_new:
                    flyout = SceneEditorFlyout(self.parent, None, None)
                else:
                    flyout = SceneEditorFlyout(self.parent, self.scene_id, self.data)
                flyout.show()
            else:
                super(SceneWidget, self).mousePressEvent(a0)
                self.double_click_primed = True
                self.double_click_timer.start(450)
        except Exception as e:
            logging.error(f"Error in SceneWidget.mousePressEvent: {e}")
            logging.exception(e)

    def resetDoubleClick(self):
        self.double_click_primed = False

    # def mouseDoubleClickEvent(self, a0) -> None:
    #     try:
    #         flyout = SceneEditorFlyout(self.parent, self.data)
    #         flyout.exec()
    #     except Exception as e:
    #         logging.error(f"Error opening scene editor flyout: {e}")
    #         logging.exception(e)

    def reload(self):
        self.parent.reload()