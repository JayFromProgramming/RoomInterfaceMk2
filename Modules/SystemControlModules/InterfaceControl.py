from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel


class InterfaceControl(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.font = self.parent.font
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")
        self.setFixedSize(parent.width(), 300)

        self.title_label = QLabel(self)
        self.title_label.setFont(self.font)
        self.title_label.setFixedSize(300, 20)
        self.title_label.setText("Local Interface Actions")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: black; font-size: 15px; font-weight: bold; border: none; background-color: transparent")


