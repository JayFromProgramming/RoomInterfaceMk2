from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel, QPushButton
from loguru import logger as logging

class FlyoutButton(QPushButton):

    def __init__(self, parent=None, text="", flyout=None, idle_timeout=30):
        super().__init__(parent)
        self.parent = parent
        self.setFixedSize(140, 30)
        self.expanded = False
        self.idle_timeout = idle_timeout * 1000
        self.button_text = text
        self.setText(f"↑{text}↑")
        self.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: #ffcd00;"
                           "border: none; border-radius: 10px")
        self.setFont(parent.font)
        self.clicked.connect(self.fly_out)
        self.flyout = flyout

    def fly_out(self):
        try:
            self.expanded = not self.expanded
            self.parent.current_focus = self
            self.parent.collapse_not_focused()
            if self.expanded:
                self.setText(f"↓{self.button_text}↓")
                self.flyout.set_focus(True)
                self.parent.start_focus_timer()
            else:
                self.setText(f"↑{self.button_text}↑")
                self.parent.current_focus = None
                self.flyout.set_focus(False)
        except Exception as e:
            logging.error(f"Failed to expand/collapse flyout: {e}")
            logging.exception(e)

    def collapse(self):
        self.expanded = False
        self.flyout.set_focus(False)
        self.setText(f"↑{self.button_text}↑")


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

        self.buttons = []

        self.refocus_timer = QTimer(self)
        self.refocus_timer.timeout.connect(self.collapse_all)
        self.refocus_timer.setSingleShot(True)

        self.current_focus = None

        self.calculate_button_positions()

    def calculate_button_positions(self):
        # All buttons should have equal spacing between them and the edges of the menu bar
        # This method should be dynamic and work for any number of buttons
        button_spacing = (self.width() - (140 * len(self.buttons))) / (len(self.buttons) + 1)
        for i, button in enumerate(self.buttons):
            button.move(round(button_spacing * (i + 1) + button.width() * i), 5)

    def add_flyout_button(self, text, flyout, idle_timeout=30):
        button = FlyoutButton(self, text, flyout, idle_timeout)
        self.buttons.append(button)
        self.calculate_button_positions()

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        self.calculate_button_positions()

    def collapse_not_focused(self):
        for button in self.buttons:
            if button is not self.current_focus:
                button.collapse()

    def collapse_all(self):
        for button in self.buttons:
            button.collapse()
        self.current_focus = None

    def reset_focus_timer(self):
        self.refocus_timer.stop()
        if self.current_focus is not None:
            self.refocus_timer.start(self.current_focus.idle_timeout)

    def start_focus_timer(self):
        self.refocus_timer.start(self.current_focus.idle_timeout)

    # def focus_room_control(self):
    #     self.parent.focus_scene_control(True)
    #     self.parent.focus_system_control(True)
    #     self.parent.focus_room_control(False)
    #
    # def focus_scene_control(self):
    #     self.parent.focus_room_control(True)
    #     self.parent.focus_system_control(True)
    #     self.parent.focus_scene_control(False)
    #
    # def focus_system_control(self):
    #     self.parent.focus_room_control(True)
    #     self.parent.focus_scene_control(True)
    #     self.parent.focus_system_control(False)
