from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging


class TriggerTile(QLabel):

    def __init__(self, parent, name, data):
        super().__init__(parent)
        self.parent = parent
        self.auth = parent.auth
        self.host = parent.host
        self.font = parent.font

        self.setFixedSize(170, 60)

        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")

        self.trigger_name = QLabel(self)
        self.trigger_name.setFont(self.font)
        self.trigger_name.setFixedSize(170, 20)
        self.trigger_name.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.trigger_name.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.trigger_name.setText(name)

        self.trigger_data = QLabel(self)
        self.trigger_data.setFont(self.font)
        self.trigger_data.setFixedSize(170, 380)
        self.trigger_data.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.trigger_data.setStyleSheet("color: black; font-size: 12px; font-weight: bold; border: none; background-color: transparent")
        self.trigger_data.setText(f"Type: {data['trigger_type']}\nValue: {data['trigger_value']}")
        self.trigger_data.move(5, 20)



