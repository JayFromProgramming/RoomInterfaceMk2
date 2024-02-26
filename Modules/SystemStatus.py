from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import QLabel

import psutils


class AdapterCheckThread(QThread):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        # Check if there is a network connection
        adapters = psutils.net_if_addrs()


class InternetCheckThread(QThread):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        pass


class MugCheckThread(QThread):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        pass


class ControllerCheckThread(QThread):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        pass


class SystemStatus(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(500, 300)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: black; border: 2px solid #ffcd00;")

        self.system_status_label = QLabel(self)
        self.system_status_label.setFixedSize(490, 20)
        self.system_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.system_status_label.setStyleSheet("color: #ffcd00; font-size: 20px; font-weight: bold; border: none;")
        self.system_status_label.setFont(parent.get_font("JetBrainsMono-Bold"))
        self.system_status_label.setText("SYSTEM STATUS")
        self.system_status_label.move(5, 5)

        self.system_status_content = QLabel(self)
        self.system_status_content.setFixedSize(490, 250)
        self.system_status_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.system_status_content.setStyleSheet("border: none; color: white; font-size: 15px")
        self.system_status_content.setFont(parent.get_font("JetBrainsMono-Regular"))
        self.system_status_content.move(5, 30)
        self.system_status_concerns = {}
        self.check_system_status()
        self.generate_status_text()

    def check_system_status(self):
        self.check_adapter_status()
        self.check_internet_status()
        self.check_mug_status()
        self.check_controller_status()

    def generate_status_text(self):
        status_text = ""
        # All names are on the left and status are right aligned with .'s filling the space
        for entry in entries:
            status_text += f"{entry[0]:<20}{entry[1]:>20}\n"

        self.system_status_content.setText(status_text)
