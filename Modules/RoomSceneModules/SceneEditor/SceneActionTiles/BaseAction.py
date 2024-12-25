import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton
from loguru import logger as logging


class BaseAction(QLabel):
    supported_action = []

    def __init__(self, parent, delete_callback, action: tuple):
        super().__init__(parent)
        self.delete_callback = delete_callback
        self.setFixedSize(270, 50)
        self.act = action[0]
        self.payload = action[1]
        self.setStyleSheet("background-color: grey; font-size: 14px; font-weight: bold; border: none; color: white")
        self.action_label = QLabel(self)
        self.action_label.move(0, 0)
        self.action_label.setFixedSize(150, 50)
        self.action_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.action_input_object = None

        self.delete_button = QPushButton(self)
        self.delete_button.setFixedSize(20, 20)
        self.delete_button.move(self.width() - self.delete_button.width(),
                                self.height() - self.delete_button.height())
        self.delete_button.setText("X")
        self.delete_button.clicked.connect(self.delete_action)
        try:
            self.create_action_input()
        except Exception as e:
            logging.error(f"Error creating action input: {e}")
            logging.exception(e)
        self.delete_button.raise_()

    def create_action_input(self):
        self.action_input_object = QLabel(self)
        self.action_input_object.setText(f"{self.act}")
        self.action_label.setText("Unknown Action:")
        self.action_input_object.move(self.width() - self.action_input_object.width() - 5, 5)
        self.action_input_object.show()

    def get_payload(self):
        raise NotImplementedError("get_payload must be implemented")

    def delete_action(self):
        try:
            self.delete_callback(self)
            self.hide()
        except Exception as e:
            logging.error(f"Error deleting action: {e}")
            logging.exception(e)
