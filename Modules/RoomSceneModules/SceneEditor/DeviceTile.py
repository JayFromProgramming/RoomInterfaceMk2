from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging

class DeviceTile(QLabel):

    def __init__(self, parent=None, device=None):
        super().__init__(parent)
        self.parent = parent
        self.device = device
        self.font = parent.font
        self.setFixedSize(280, 40)
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")

        self.device_label = QLabel(self)
        self.device_label.setFont(self.font)
        self.device_label.setFixedSize(280, 20)
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.device_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;"
                                        "background-color: transparent")
        self.device_label.setText(f"{device}")

        self.device_text = QLabel(self)
        self.device_text.setFont(self.font)
        self.device_text.setFixedSize(280, 20)
        self.device_text.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        self.device_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;"
                                        "background-color: transparent")
        self.device_text.setText("<pre>Status: ???</pre>")
        self.device_text.move(5, 70)

        self.parent.make_name_request(device)

    def update_human_name(self, name):
        self.device_label.setText(name)


