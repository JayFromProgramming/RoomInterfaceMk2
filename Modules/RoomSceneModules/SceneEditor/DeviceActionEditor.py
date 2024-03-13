
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging


class DeviceActionEditor(QLabel):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.font = self.parent.font

        self.setFixedSize(400, 400)
        self.setStyleSheet("background-color: black; border: 2px solid #ffcd00; border-radius: 10px")


