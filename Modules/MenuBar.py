from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton


class MenuBar(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(parent.width(), 50)
        self.setStyleSheet("background-color: black;")
        self.move(0, 0)
        self.font = parent.get_font("JetBrainsMono-Bold")
        self.font.setPointSize(14)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.room_control_expand = QPushButton(self)
        self.room_control_expand.setFixedSize(140, 40)
        self.room_control_expand.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: #ffcd00;"
                                               "border: none; border-radius: 10px")
        self.room_control_expand.setText("↑Room Control↑")
        # Move the button to the exact center of the menu bar
        self.room_control_expand.move(round((self.width() - self.room_control_expand.width()) / 2), 5)
        self.room_control_expand.clicked.connect(parent.focus_room_control)
        self.room_control_expand.setFont(self.font)

        self.system_control_expand = QPushButton(self)
        self.system_control_expand.setFixedSize(140, 40)
        self.system_control_expand.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: #ffcd00;"
                                                 "border: none; border-radius: 10px")
        self.system_control_expand.setText("↑System Control↑")
        self.system_control_expand.move(round(self.width() / 5 - self.system_control_expand.width() / 2), 5)
        self.system_control_expand.setFont(self.font)

        self.settings_expand = QPushButton(self)
        self.settings_expand.setFixedSize(140, 40)
        self.settings_expand.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: #ffcd00;"
                                           "border: none; border-radius: 10px")
        self.settings_expand.setText("↑Device Control↑")
        # Have this buttons position mirror the system control button
        self.settings_expand.move(round(self.width() / 5 * 4 - self.settings_expand.width() / 2), 5)
        self.settings_expand.setFont(self.font)

