from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton


class MenuBar(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedSize(parent.width(), 40)
        self.setStyleSheet("background-color: black;")
        self.move(0, 0)
        self.font = parent.get_font("JetBrainsMono-Regular")
        self.font.setPointSize(14)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.room_control_expand = QPushButton(self)
        self.room_control_expand.setFixedSize(140, 30)
        self.room_control_expand.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: #ffcd00;"
                                               "border: none; border-radius: 10px")
        self.room_control_expand.setText("↑Device Control↑")
        # Move the button to the exact center of the menu bar
        self.room_control_expand.move(round((self.width() - self.room_control_expand.width()) / 2), 5)
        self.room_control_expand.clicked.connect(self.focus_room_control)
        self.room_control_expand.setFont(self.font)

        self.scenes_expand = QPushButton(self)
        self.scenes_expand.setFixedSize(140, 30)
        self.scenes_expand.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: #ffcd00;"
                                         "border: none; border-radius: 10px")
        self.scenes_expand.setText("↑Scene Control↑")
        # Have this buttons position mirror the system control button
        self.scenes_expand.move(round(self.width() / 5 * 4 - self.scenes_expand.width() / 2), 5)
        self.scenes_expand.setFont(self.font)
        self.scenes_expand.clicked.connect(self.focus_scene_control)

        # self.font.setStrikeOut(True)
        self.system_control_expand = QPushButton(self)
        self.system_control_expand.setFixedSize(140, 30)
        self.system_control_expand.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: #ffcd00;"
                                                 "border: none; border-radius: 10px")
        self.system_control_expand.setText("↑System Control↑")
        self.system_control_expand.move(round(self.width() / 5 - self.system_control_expand.width() / 2), 5)
        self.system_control_expand.setFont(self.font)
        self.system_control_expand.clicked.connect(self.focus_system_control)

    def resizeEvent(self, a0):
        self.room_control_expand.move(round((self.width() - self.room_control_expand.width()) / 2), 5)
        self.system_control_expand.move(round(self.width() / 5 - self.system_control_expand.width() / 2), 5)
        self.scenes_expand.move(round(self.width() / 5 * 4 - self.scenes_expand.width() / 2), 5)
        super().resizeEvent(a0)

    def focus_room_control(self):
        self.parent.focus_scene_control(True)
        self.parent.focus_system_control(True)
        self.parent.focus_room_control(False)

    def focus_scene_control(self):
        self.parent.focus_room_control(True)
        self.parent.focus_system_control(True)
        self.parent.focus_scene_control(False)

    def focus_system_control(self):
        self.parent.focus_room_control(True)
        self.parent.focus_scene_control(True)
        self.parent.focus_system_control(False)
