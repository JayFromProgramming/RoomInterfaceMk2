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
            if data["type"] == "SatelliteMonitor":
                self.parse_interface_state_satellite(data["state"])
            else:
                self.parse_interface_stats_central(data["state"])
        except Exception as e:
            logging.error(f"Parsing Error: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def parse_interface_state_satellite(self, data):
        try:
            self.title_label.setText(f"{data['name']} Info")
            cpu_temp = str(round(data["temperature"], 2)).rjust(3, " ") if data["temperature"] else "N/A"
            cpu_percent = str(round(data["cpu_usage"], 2)).rjust(5, " ") if data["cpu_usage"] else "  N/A"
            ram_percent = data["memory_usage"]if data["memory_usage"] else "N/A"
            boot_partition = data.get("boot_partition", "Unknown").replace('\u0000', '').upper().ljust(7, " ")
            mcu_uptime = self.format_uptime(data["uptime_mcu"]) if data["uptime_mcu"] \
                else "No Response"
            if not data.get("online", False):
                link_uptime = "Link Down  "
                network_address = "Host Unreachable"
            else:
                link_uptime = self.format_uptime(data["uptime_connection"]) if data["uptime_connection"] \
                    else "No Response"
                network_address = str(data["address"]).rjust(16, " ") if data["address"] else \
                    "Host Unreachable"
            firmware_version = data.get("firmware_version", "N/A")
            firmware_version = str(firmware_version).rjust(13, " ") if firmware_version else "N/A"
            text = f"CPU: {cpu_percent}% | Temp: {cpu_temp}°C | MEM: {ram_percent}B\n"
            text += f"Reset#:   0 | Boot: {boot_partition} | Sig: {data['signal_strength']}dBm\n"
            text += f"S.Uptime: {mcu_uptime} | Version: {firmware_version}\n"
            text += f"L.Uptime: {link_uptime} | Addr: {network_address}\n"

            self.interface_stats.setText(f"<pre>{text}</pre>")
            if data["address"] is None:
                # Set strike through on all the buttons if the host is unreachable
                self.set_button_strike_through(True)
            else:
                self.set_button_strike_through(False)
        except Exception as e:
            self.interface_stats.setText(f"<pre>Error: {e}</pre>")
            logging.error(f"Error parsing interface stats: {e}")
            logging.exception(e)

    def parse_interface_stats_central(self, data):
        try:
            self.title_label.setText(f"{data['name']} Info")
            cpu_temp = str(data["temperature"]).rjust(3, " ") if data["temperature"] else "N/A"
            cpu_percent = str(round(data["cpu_usage"], 2)).rjust(5, " ") if data["cpu_usage"] else "N/A"
            ram_percent = str(round(data["memory_usage"], 2)).rjust(5, " ") if data["memory_usage"] else "N/A"
            disk_percent = str(round(data["disk_usage"], 2)).rjust(5, " ") if data["disk_usage"] else "N/A"
            network_usage = data.get("network_usage", 0)
            network_usage = humanize.naturalsize(network_usage, binary=True) if network_usage else "N/A"
            sys_uptime = self.format_uptime(data["uptime_system"]) if data["uptime_system"] \
                else "No Response"
            prog_uptime = self.format_uptime(data["uptime_controller"]) if data["uptime_controller"] \
                else "No Response"
            host_name = str(data["hostname"]).rjust(16, " ") if data["hostname"] else \
                "Host Unreachable"
            network_address = str(data["address"]).rjust(16, " ") if data["address"] else \
                "Host Unreachable"
            text = f"CPU:  {cpu_percent}% | Temp: {cpu_temp}°C | RAM: {ram_percent}%\n"
            text += f"Disk: {disk_percent}% | Net: {network_usage}\n"
            text += f"S.Uptime: {sys_uptime} | Name: {host_name}\n"
            text += f"P.Uptime: {prog_uptime} | Addr: {network_address}\n"

            self.interface_stats.setText(f"<pre>{text}</pre>")
            if data["address"] is None:
                # Set strike through on all the buttons if the host is unreachable
                self.set_button_strike_through(True)
            else:
                self.set_button_strike_through(False)
        except Exception as e:
            self.interface_stats.setText(f"<pre>Error: {e}</pre>")
            logging.error(f"Error parsing interface stats: {e}")
            logging.exception(e)

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
