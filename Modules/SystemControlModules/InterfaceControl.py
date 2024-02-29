import os
import subprocess
import time

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel, QPushButton, QDialog, QMessageBox, QStyleFactory
import psutil
import humanize
from loguru import logger as logging


class InterfaceControl(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.font = self.parent.font
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")
        self.setFixedSize(430, 130)

        self.latest = None

        self.title_label = QLabel(self)
        self.title_label.setFont(self.font)
        self.title_label.setFixedSize(430, 20)
        self.title_label.setText("Local Interface Info")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: black; font-size: 15px; font-weight: bold; border: none; background-color: transparent")

        self.interface_stats = QLabel(self)
        self.interface_stats.setFont(self.font)
        self.interface_stats.setFixedSize(430, 60)
        self.interface_stats.setText("<pre>CPU: 0% | RAM: 0% | Disk: 0% | Network: 0% | Uptime: 0:00:00\n</pre>")
        self.interface_stats.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.interface_stats.setStyleSheet("color: black; font-size: 15px; font-weight: bold; border: none; background-color: transparent")
        self.interface_stats.move(5, 20)

        self.interface_stats_update_timer = QTimer(self)
        self.interface_stats_update_timer.timeout.connect(self.update_interface_stats)
        self.interface_stats_update_timer.start(1000)
        self.last_network_bytes = 0

        self.action_title_label = QLabel(self)
        self.action_title_label.setFont(self.font)
        self.action_title_label.setFixedSize(430, 20)
        self.action_title_label.setText("Local Interface Actions")
        self.action_title_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.action_title_label.setStyleSheet("color: black; font-size: 15px; font-weight: bold; border: none; background-color: transparent")
        self.action_title_label.move(5, 70)

        self.reboot_button = QPushButton(self)
        self.reboot_button.setFont(self.font)
        self.reboot_button.setFixedSize(100, 30)
        self.reboot_button.setText("Reboot")
        self.reboot_button.setStyleSheet("color: white; font-size: 14px; font-weight: bold; background-color: grey;"
                                         "border: none; border-radius: 10px")
        self.reboot_button.move(5, 90)
        self.reboot_button.clicked.connect(self.reboot)

        self.restart_button = QPushButton(self)
        self.restart_button.setFont(self.font)
        self.restart_button.setFixedSize(100, 30)
        self.restart_button.setText("Restart")
        self.restart_button.setStyleSheet("color: white; font-size: 14px; font-weight: bold; background-color: grey;"
                                          "border: none; border-radius: 10px")
        self.restart_button.move(110, 90)
        self.restart_button.clicked.connect(self.restart)

        self.update_button = QPushButton(self)
        self.update_button.setFont(self.font)
        self.update_button.setFixedSize(100, 30)
        self.update_button.setText("Update")
        self.update_button.setStyleSheet("color: white; font-size: 14px; font-weight: bold; background-color: grey;"
                                         "border: none; border-radius: 10px")
        self.update_button.move(215, 90)
        self.update_button.clicked.connect(self.update_code)

        self.shutdown_button = QPushButton(self)
        self.shutdown_button.setFont(self.font)
        self.shutdown_button.setFixedSize(100, 30)
        self.shutdown_button.setText("Shutdown")
        self.shutdown_button.setStyleSheet("color: red; font-size: 14px; font-weight: bold; background-color: grey;"
                                           "border: none; border-radius: 10px")
        self.shutdown_button.move(320, 90)
        self.shutdown_button.clicked.connect(self.shutdown)

        # self.move(0, parent.height() - self.height())

    @staticmethod
    def get_confirmation(message, sub_message=None):
        # Open a dialog box to confirm the action
        diag = QMessageBox()
        diag.setWindowTitle("Confirmation")
        diag.setText(message)
        if sub_message:
            diag.setInformativeText(sub_message)
        diag.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        diag.setDefaultButton(QMessageBox.StandardButton.No)
        diag.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        diag.exec()
        if diag.result() == 16384:
            return True
        return False

    def reboot(self):
        raise NotImplementedError

    def restart(self):
        raise NotImplementedError

    def update_code(self):
        raise NotImplementedError

    def shutdown(self):
        raise NotImplementedError
