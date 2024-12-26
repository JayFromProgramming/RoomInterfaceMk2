import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QCheckBox
from loguru import logger as logging


class BaseAction(QLabel):
    supported_action = []

    def __init__(self, parent, enabled, action: tuple):
        super().__init__(parent)
        self.setFixedSize(270, 50)
        self.act = action[0]
        self.payload = action[1]
        self.setStyleSheet("background-color: grey; font-size: 14px; font-weight: bold; border: none; color: white")
        self.action_label = QLabel(self)
        self.action_label.move(0, 0)
        self.action_label.setFixedSize(150, 50)
        self.action_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.action_input_object = None

        self.enabled_button = QCheckBox(self)
        self.enabled_button.setFixedSize(20, 20)
        self.enabled_button.move(self.width() - self.enabled_button.width(),
                                 self.height() - self.enabled_button.height())
        self.enabled_button.setChecked(enabled)
        try:
            self.create_action_input()
        except Exception as e:
            logging.error(f"Error creating action input: {e}")
            logging.exception(e)
        self.enabled_button.raise_()

    def create_action_input(self):
        self.action_input_object = QLabel(self)
        self.action_input_object.setText(f"{self.act}")
        self.action_label.setText("Unknown Action:")
        self.action_input_object.move(self.width() - self.action_input_object.width() - 5, 5)
        self.action_input_object.show()

    def get_payload(self):
        raise NotImplementedError("get_payload must be implemented")
