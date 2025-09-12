from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget, QScrollArea, QComboBox, QPushButton, QApplication, QListView
from loguru import logger as logging
import json

from Modules.RoomSceneModules.SceneEditor.SceneActionTiles.SceneAction import SceneAction


class SceneActionEditor(QWidget):
    """
    This class creates a popup window that allows the user to edit the actions of a scene.
    Each action will be added to a scrollable list of labels.
    """

    def __init__(self, device_name: tuple, supported_actions, action_payload: dict = None):
        super().__init__()
        self.device_id = device_name[0]
        self.device_name = device_name[1]
        self.action_payload = action_payload
        self.actions = []

        self.setFixedSize(310, 375)
        self.setWindowTitle("Routine Action Editor")

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFixedSize(300, 275)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_panel = QLabel(self)
        self.scroll_panel.setFixedSize(300, 0)
        self.scroll_area.setWidget(self.scroll_panel)
        self.scroll_area.move(10, 10)
        self.no_actions_label = QLabel(self.scroll_panel)
        self.no_actions_label.setFixedSize(300, 50)
        self.no_actions_label.setText("Device supports no actions")
        self.no_actions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_actions_label.setStyleSheet("font-size: 14px; font-weight: bold; border: none; background-color: transparent")
        self.no_actions_label.hide()

        self.submit_slot = None
        self.device_supported_actions = supported_actions

        self.submit_button = QPushButton(self)
        self.submit_button.setFixedSize(60, 35)
        self.submit_button.move(10, self.scroll_area.y() + self.scroll_area.height() + 5)
        self.submit_button.setText("Submit")
        self.submit_button.clicked.connect(self.submit_action)

        self.cancel_button = QPushButton(self)
        self.cancel_button.setFixedSize(60, 35)
        self.cancel_button.move(self.submit_button.x(), self.submit_button.y() + self.submit_button.height() + 2)
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.deleteLater)

        self.device_name_label = QLabel(self)
        self.device_name_label.setFixedSize(280, 80)
        self.device_name_label.move(self.submit_button.x() + self.submit_button.width() + 5, self.submit_button.y())
        self.device_name_label.setText(f"<pre>Editing\nID:  {self.device_id}\nName:{self.device_name}</pre>")
        self.device_name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.device_name_label.setStyleSheet("font-size: 13px; font-weight: bold; border: none; background-color: transparent")

        self.revert_button = QPushButton(self)
        self.revert_button.setFixedSize(50, 22)
        self.revert_button.move(self.width() - self.revert_button.width() - 10,
                                self.scroll_area.y() + self.scroll_area.height() + 5)
        self.revert_button.setText("Revert")
        self.revert_button.clicked.connect(self.create_actions)

        self.copy_data_button = QPushButton(self)
        self.copy_data_button.setFixedSize(50, 22)
        self.copy_data_button.move(self.width() - self.copy_data_button.width() - 10,
                                   self.revert_button.y() + self.revert_button.height() + 5)
        self.copy_data_button.setText("Copy")
        self.copy_data_button.clicked.connect(self.copy_data)

        self.paste_data_button = QPushButton(self)
        self.paste_data_button.setFixedSize(50, 22)
        self.paste_data_button.move(self.width() - self.paste_data_button.width() - 10,
                                    self.copy_data_button.y() + self.copy_data_button.height() + 5)
        self.paste_data_button.setText("Paste")
        self.paste_data_button.clicked.connect(self.paste_data)

        self.create_actions()

        # Remove the window frame
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

    def create_actions(self):
        if len(self.actions) > 0:
            for action in self.actions:
                action.deleteLater()
        self.actions = []
        if self.action_payload is not None:
            for action in self.action_payload.items():
                action_label = SceneAction.create_action(self.scroll_panel, True, action)
                self.actions.append(action_label)
        self.add_remaining_actions()
        self.layout_actions()

    def add_remaining_actions(self):
        """
        This method will add any actions that are supported by the device but not present in the action payload.
        :return:
        """
        for action in self.device_supported_actions:
            if action not in [act.act for act in self.actions]:
                payload = (action, SceneAction.get_action_default_payload(action))
                action_label = SceneAction.create_action(self.scroll_panel, False, payload)
                self.actions.append(action_label)

    def delete_action(self, action):
        self.actions.remove(action)
        self.layout_actions()

    def get_payload(self):
        try:
            payload = {}
            for action in self.actions:
                if action.enabled_button.isChecked():
                    payload[action.act] = action.get_payload()
            return payload
        except Exception as e:
            logging.error(f"Error getting payload: {e}")
            logging.exception(e)
            return {}

    def layout_actions(self):
        x_offset = 5
        y_offset = 5
        for action in self.actions:
            action.move(x_offset, y_offset)
            action.show()
            y_offset = y_offset + action.height() + 5
        if len(self.actions) == 0:
            self.no_actions_label.show()
            self.scroll_panel.setFixedSize(self.scroll_panel.width(), 50)
        else:
            self.no_actions_label.hide()
            self.scroll_panel.setFixedSize(self.scroll_panel.width(), y_offset + 5)
        self.scroll_area.setWidget(self.scroll_panel)

    def copy_data(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(json.dumps(self.get_payload()))

    def paste_data(self):
        clipboard = QApplication.clipboard()
        data = clipboard.text()
        if data == "":
            return
        try:
            self.action_payload = json.loads(data)
            self.create_actions()
        except Exception as e:
            logging.error(f"Error pasting data: {e}")
            logging.exception(e)
            return

    def set_submit_slot(self, slot):
        self.submit_slot = slot

    def submit_action(self):
        if self.submit_slot is not None:
            self.submit_slot(self.get_payload())
        self.hide()
        self.deleteLater()

    def closeEvent(self, a0):
        self.hide()
        self.deleteLater()
