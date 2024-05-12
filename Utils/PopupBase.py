import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QWidget

from Utils.PopupManager import PopupManager
from loguru import logger as logging


class PopupBase(QWidget):

    def __init__(self, window_name, size):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.X11BypassWindowManagerHint)
        self.setStyleSheet("background-color: black;")
        self.setFixedSize(size[0], size[1] + 30)
        self.move(round(512 - self.height() / 2), round(300 - self.width() / 2))
        self.title_label = QLabel(self)
        self.title_label.setFixedSize(size[0], 30)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.title_label.setStyleSheet("color: white; font-size: 16px;"
                                       " font-weight: bold; border: none; background-color: transparent")
        self.title_label.setText(window_name)
        self.title_label.move(5, 0)
        self.close_button = QPushButton(self)
        self.close_button.setFixedSize(25, 25)
        self.close_button.move(size[0] - 30, 5)
        self.close_button.setStyleSheet("color: black; font-size: 20px; font-weight: bold; background-color: red")
        self.close_button.setText("X")
        self.close_button.clicked.connect(self.close)

