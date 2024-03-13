from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging


class TriggerColumn(QLabel):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.auth = parent.auth
        self.host = parent.host
        self.font = parent.font

        self.setFixedSize(180, 400)

        self.setStyleSheet("background-color: transparent; border: 2px solid #ffcd00; border-radius: 10px")

        self.column_name = QLabel(self)
        self.column_name.setFont(self.font)
        self.column_name.setFixedSize(185, 20)
        self.column_name.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.column_name.setStyleSheet("color: #ffcd00; font-size: 16px; font-weight: bold; border: none;")
        self.column_name.setText("Triggers")
