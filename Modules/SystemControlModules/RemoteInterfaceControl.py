import json
import os
import subprocess
import time

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton, QDialog, QMessageBox, QStyleFactory
import humanize
from loguru import logger as logging

from Modules.SystemControlModules.InterfaceControl import InterfaceControl


class RemoteInterfaceControl(InterfaceControl):

    def __init__(self, parent=None, name=None):
        super().__init__(parent)
        self.parent = parent
        self.auth = self.parent.auth
        self.name = name
        self.font = self.parent.font
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")
        self.setFixedSize(430, 130)

        self.title_label.setText(f"{self.name} Interface Info")

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_network_response)

    def send_command(self, command):
        request = QNetworkRequest(QUrl(f"http://moldy.mug.loafclan.org/set/{self.name}"))
        # Add a json payload to the post request
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        payload = json.dumps(command)
        self.network_manager.post(request, payload.encode("utf-8"))

    def update_interface_stats(self):
        self.make_request()

    def make_request(self):
        request = QNetworkRequest(QUrl(f"http://{self.parent.host}/get/{self.name}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.parent.auth, 'utf-8'))
        self.network_manager.get(request)

    def hideEvent(self, a0):
        self.interface_stats_update_timer.stop()

    def showEvent(self, a0):
        self.interface_stats_update_timer.start(1000)
        self.make_request()

    def handle_network_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Network Error: {reply.error()}")
                return
            data = reply.readAll()
            data = data.data().decode("utf-8")
            data = json.loads(data)
            if "state" not in data:
                logging.error(f"Invalid Response Received: {data}")
                return
            self.parse_interface_stats(data["state"])
        except Exception as e:
            logging.error(f"Parsing Error: {e}")

    def parse_interface_stats(self, data):
        try:
            self.title_label.setText(f"{data['name']} Info")
            # self.action_title_label.setText(f"{data['name']} Actions")
            cpu_temp = str(data["temperature"]).rjust(3, " ")
            cpu_percent = str(round(data["cpu_usage"], 2)).rjust(5, " ")
            ram_percent = str(round(data["memory_usage"], 2)).rjust(5, " ")
            disk_percent = str(round(data["disk_usage"], 2)).rjust(5, " ")
            network_usage = data["network_usage"]
            network_usage = humanize.naturalsize(network_usage, binary=True)
            sys_uptime = self.format_uptime(data["uptime_system"])
            prog_uptime = self.format_uptime(data["uptime_controller"])
            version = "Latest Commit" if data["update_available"] else "Behind" \
                if data["update_available"] is not None else "Git Error"
            network_address = str(data["address"]).rjust(15, " ")
            text = f"CPU:  {cpu_percent}% | Temp: {cpu_temp}°C | RAM: {ram_percent}%\n"
            text += f"Disk: {disk_percent}% | Net: {network_usage}\n"
            text += f"S.Uptime: {sys_uptime} | Version: {version}\n"
            text += f"P.Uptime: {prog_uptime} | Addr: {network_address}\n"

            self.interface_stats.setText(f"<pre>{text}</pre>")
        except Exception as e:
            self.interface_stats.setText(f"<pre>Error: {e}</pre>")

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
        if self.get_confirmation("Are you sure you want to reboot this device?"):
            logging.info("Rebooting the interface on user request")
            self.send_command({"action": "reboot"})

    def restart(self):
        if self.get_confirmation("Are you sure you want to restart the interface?"):
            # Exit the application and let the service manager restart it
            self.send_command({"action": "restart"})

    def update_code(self):
        if self.get_confirmation("Are you sure you want to update the interface?"):
            logging.info("Updating the interface on user request")
            self.send_command({"action": "update"})

    def shutdown(self):
        if self.get_confirmation("Are you sure you want to shutdown this device?",
                                 "This action is irreversible and will require"
                                 " manual intervention to power this device back on."):
            logging.info("Shutting down the interface on user request")
            self.send_command({"action": "shutdown"})
