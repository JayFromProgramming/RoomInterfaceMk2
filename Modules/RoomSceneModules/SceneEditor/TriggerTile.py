from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton
from loguru import logger as logging


class TriggerTile(QLabel):

    def __init__(self, parent, trigger_type, data=None):
        super().__init__(parent)
        self.parent = parent
        self.auth = parent.auth
        self.host = parent.host
        self.font = parent.font

        self.setFixedSize(192, 60)

        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")

        self.trigger_name = QLabel(self)
        self.trigger_name.setFont(self.font)
        self.trigger_name.setFixedSize(self.width(), 20)
        self.trigger_name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.trigger_name.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;"
                                        "background-color: transparent")
        self.trigger_name.setText(f"{trigger_type}")
        self.trigger_name.move(5, 0)

        if data is None:
            data = {
                "trigger_type": trigger_type,
                "trigger_subtype": None,
                "trigger_value": None,
                "enabled": -1
            }

        self.trigger_data = QLabel(self)
        self.trigger_data.setFont(self.font)
        self.trigger_data.setFixedSize(self.width(), 300)
        self.trigger_data.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.trigger_data.setStyleSheet("color: black; font-size: 12px; font-weight: bold; border: none; "
                                        "background-color: transparent")
        self.trigger_data.setText(f"Val: {data['trigger_subtype']}\nArg: {data['trigger_value']}")
        self.trigger_data.move(5, 20)

        self.trigger_enable = QPushButton(self)
        self.trigger_enable.setFixedSize(60, 30)
        if data["enabled"] == 1:
            self.trigger_enable.setText("Disable")
            self.trigger_enable.setStyleSheet("background-color: green; border: 2px solid #ffcd00;"
                                              " border-radius: 10px")
        elif data["enabled"] == 0:
            self.trigger_enable.setText("Enable")
            self.trigger_enable.setStyleSheet("background-color: grey; border: 2px solid #ffcd00;"
                                              " border-radius: 10px")
        elif data["enabled"] == -1:
            self.trigger_enable.setText("Add")
            self.trigger_enable.setStyleSheet("background-color: grey; border: 2px solid #ffcd00;"
                                              " border-radius: 10px")
        else:
            self.trigger_enable.setText("IDFK")
            self.trigger_enable.setStyleSheet("background-color: red; border: 2px solid #ffcd00;"
                                              " border-radius: 10px")
        self.trigger_enable.setFont(self.font)
        self.trigger_enable.move(self.width() - self.trigger_enable.width() - 5,
                                 self.height() - self.trigger_enable.height() - 5)

    def resizeEvent(self, a0) -> None:
        self.trigger_name.setFixedSize(self.width(), 20)
        self.trigger_data.setFixedSize(self.width(), 300)
        super().resizeEvent(a0)



