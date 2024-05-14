import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QWidget, QApplication, QMainWindow

from loguru import logger as logging


class PopupBase(QWidget):

    def get_main_window(self):
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMainWindow):
                return widget
        return None

    def __init__(self, window_name, size):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.X11BypassWindowManagerHint)
        self.setStyleSheet("background-color: black;")
        self.setFixedSize(size[0], size[1] + 30)
        # Get the parent windows X and Y coordinates on the screen so we can center the popup on it
        main_window_x, main_window_y = self.get_main_window().x(), self.get_main_window().y()
        main_window_width, main_window_height = self.get_main_window().width(), self.get_main_window().height()
        self.move(round(main_window_x + (main_window_width - size[0]) // 2),
                  round(main_window_y + (main_window_height - size[1]) // 2))
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

