from logging import logProcesses

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QComboBox, QLineEdit, QPushButton, QLabel
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from Modules.RoomSceneModules.SceneEditor.SceneActionTiles.BaseAction import BaseAction
from Utils.UtilMethods import get_auth, get_host

from loguru import logger as logging

class RoutineLine(QLabel):

    def __init__(self, parent, routine):
        super().__init__(parent)

        self.input_combo = QComboBox(self)
        self.input_combo.setFixedSize(150, 20)
        self.setFixedSize(150, 25)
        self.setStyleSheet("color: black; font-size: 12px; font-weight: bold; border: none;"
                           "background-color: transparent")
        self.setText(f"{routine.get('name', 'Unknown Routine')} (ID: {routine.get('id', 'N/A')})")
        self.move(10, 5 + (25 * parent.routine_count))
        parent.routine_count += 1
        self.show()

    def routine_list_received(self, routines):
        pass

class RoutineControlAction(BaseAction):

    supported_action = [("execute_routine", "Execute Routine", [0]),
                        ("enable_routine", "Enable Routine", [0]),
                        ("disable_routine", "Disable Routine", [0])]

    def __init__(self, parent, enabled, action: tuple):
        self.action_type = action[0]
        self.total_actions = len(action[1])
        self.routines = []
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_routine_response)
        self.add_routine_button = None

        super().__init__(parent, enabled, action)

    def request_all_routines(self):
        logging.info("Requesting all routines from server...")
        try:
            request = QNetworkRequest(QUrl(f"http://{get_host()}/scene_get/scenes/null"))
            request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
            self.network_manager.get(request)
        except Exception as e:
            logging.error(f"Error requesting routines: {e}")
            self.routines = []

    def handle_routine_response(self, reply):
        logging.info("Received routines response from server")
        if reply.error() != QNetworkReply.NetworkError.NoError:
            error_str = reply.errorString()
            logging.error(f"Network error while fetching routines: {reply.errorString()}")
            self.routines = []
        else:
            data = reply.readAll().data()
            try:
                import json
                schema = json.loads(data)
                self.routines = schema.get("routines", [])
            except Exception as e:
                logging.error(f"Error parsing routines JSON: {e}")
                self.routines = []
        self.update_action_input()

    def add_routine_line(self):
        pass

    def update_action_input(self):
        pass

    def create_action_input(self):
        self.setFixedSize(270, 30)
        self.request_all_routines()
        self.add_routine_button = QPushButton(self)
        self.add_routine_button.setText("Add Routine")
        self.add_routine_button.setFixedSize(75, 24)
        self.add_routine_button.setStyleSheet("color: black; border: 2px solid black; font-size: 12px; font-weight: bold;"
                                                "background-color: lightgray;")
        self.add_routine_button.clicked.connect(self.add_routine_line)
        # Set the action label to whatever the assigned action of this tile is
        match self.action_type:
            case "execute_routine":
                self.action_label.setText("Execute Routines:")
            case "enable_routine":
                self.action_label.setText("Enable Routines:")
            case "disable_routine":
                self.action_label.setText("Disable Routines:")
            case _:
                self.action_label.setText("Unknown Action:")
        self.enabled_button.move(self.width() - self.enabled_button.width(),
                                 self.height() - self.enabled_button.height())
        self.add_routine_button.move(self.action_label.x() + self.action_label.width() + 5,
                                        self.height() - self.add_routine_button.height() - 5)

    def get_payload(self):
        pass
