from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging

from Utils.ScrollableMenu import ScrollableMenu


class DeviceColumn(ScrollableMenu):

    def __init__(self, parent, column_name, starting_device_ids=None):
        super().__init__(parent, parent.font)
        self.parent = parent
        self.font = self.parent.font
        self.setFixedSize(290, 490)
        self.setStyleSheet("background-color: transparent; border: 2px solid #ffcd00; border-radius: 10px")
        self.device_ids = starting_device_ids
        self.device_labels = []

        self.column_name = QLabel(self)
        self.column_name.setFont(self.font)
        self.column_name.setFixedSize(300, 20)
        self.column_name.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.column_name.setStyleSheet("color: #ffcd00; font-size: 16px; font-weight: bold; border: none;")
        self.column_name.setText(column_name)
        self.column_name.move(0, 0)

    def move_widgets(self, y):
        for label in self.device_labels:
            label.move(0, y)
            y += 25
