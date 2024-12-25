from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget, QScrollArea, QComboBox, QPushButton, QApplication
from loguru import logger as logging
import json

from Modules.RoomSceneModules.SceneEditor.SceneActionTiles.SceneAction import SceneAction


class SceneActionEditor(QWidget):
    """
    This class creates a popup window that allows the user to edit the actions of a scene.
    Each action will be added to a scrollable list of labels.
    """

    def __init__(self, device_name, action_payload: dict = None):
        super().__init__()
        self.setFixedSize(330, 440)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFixedSize(310, 350)
        self.scroll_panel = QLabel(self)
        self.scroll_panel.setFixedSize(310, 600)
        self.scroll_area.setWidget(self.scroll_panel)
        self.scroll_area.move(10, 10)
        self.setWindowTitle("Scene Action Editor")
        self.device_name = device_name
        self.action_payload = action_payload
        self.actions = []

        self.device_name_label = QLabel(self)
        self.device_name_label.setFixedSize(310, 20)
        self.device_name_label.move(10, 330)
        self.device_name_label.setText(f"Editing actions for {self.device_name}")

        self.add_new_button = QPushButton(self)
        self.add_new_button.setFixedSize(70, 30)
        self.add_new_button.move(10, 350)
        self.add_new_button.setText("Add Action")
        self.add_new_button.clicked.connect(self.add_new_action)

        self.action_type_selector = QComboBox(self)
        for action in SceneAction.supported_actions():
            self.action_type_selector.addItem(action[1])
        self.action_type_selector.setFixedSize(100, 30)
        self.action_type_selector.move(self.add_new_button.x() + self.add_new_button.width() + 5,
                                       self.add_new_button.y())

        self.paste_data_button = QPushButton(self)
        self.paste_data_button.setFixedSize(50, 22)
        self.paste_data_button.move(self.width() - self.paste_data_button.width() - 10,
                                    self.height() - self.paste_data_button.height() - 2)
        self.paste_data_button.setText("Paste")
        self.paste_data_button.clicked.connect(self.paste_data)

        self.copy_data_button = QPushButton(self)
        self.copy_data_button.setFixedSize(50, 22)
        self.copy_data_button.move(self.paste_data_button.x(), self.paste_data_button.y() - self.copy_data_button.height() - 2)
        self.copy_data_button.setText("Copy")
        self.copy_data_button.clicked.connect(self.copy_data)

        self.revert_button = QPushButton(self)
        self.revert_button.setFixedSize(50, 22)
        self.revert_button.move(self.copy_data_button.x(), self.copy_data_button.y() - self.revert_button.height() - 2)
        self.revert_button.setText("Revert")
        self.revert_button.clicked.connect(self.create_actions)

        self.create_actions()

    def create_actions(self):
        if len(self.actions) > 0:
            for action in self.actions:
                action.deleteLater()
        self.actions = []
        if self.action_payload is not None:
            for action in self.action_payload.items():
                action_label = SceneAction.create_action(self.scroll_panel, self.delete_action, action)
                self.actions.append(action_label)
        self.layout_actions()

    def add_new_action(self):
        action = SceneAction.supported_actions()[self.action_type_selector.currentIndex()]
        self.add_action(action)

    def add_action(self, action: tuple):
        action_payload = (action[0], action[2])
        action_label = SceneAction.create_action(self.scroll_panel, self.delete_action, action_payload)
        self.actions.append(action_label)
        self.layout_actions()

    def delete_action(self, action):
        self.actions.remove(action)
        self.layout_actions()

    def get_payload(self):
        try:
            payload = {}
            for action in self.actions:
                payload[action.act] = action.get_payload()
            return payload
        except Exception as e:
            logging.error(f"Error getting payload: {e}")
            logging.exception(e)
            return {}

    def layout_actions(self):
        x_offset = 10
        y_offset = 5
        for action in self.actions:
            action.move(x_offset, y_offset)
            action.show()
            y_offset = y_offset + action.height() + 5
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

    def closeEvent(self, a0):
        self.hide()
        self.deleteLater()
