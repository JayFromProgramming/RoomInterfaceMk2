import os
import subprocess
import time

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel, QPushButton, QDialog, QMessageBox, QStyleFactory
import psutil
import humanize
from loguru import logger as logging

from Modules.SystemControlModules.InterfaceControl import InterfaceControl


class LocalInterfaceControl(InterfaceControl):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.font = self.parent.font
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")
        self.setFixedSize(430, 130)

        self.latest = None

        self.version_check_timer = QTimer(self)
        self.version_check_timer.timeout.connect(self.check_version)
        self.version_check_timer.start(1000 * 60)  # Check for updates every minute
        self.check_version()

        # self.move(0, parent.height() - self.height())

    def check_version(self):
        # Check if the current version is the latest (use git to check if the current commit is the latest)
        try:
            subprocess.run(["git", "fetch", "origin", "master"])
            result = subprocess.run(["git", "rev-list", "--count", "HEAD..origin/master"], capture_output=True)
            if str(result.stdout) == b'0\n':
                self.latest = False
            self.latest = True
        except Exception as e:
            logging.error(f"Error checking for updates: {e}")
            self.latest = None

    def update_interface_stats(self):
        try:
            cpu_percent = str(round(psutil.cpu_percent(), 2)).rjust(5, " ")
            if hasattr(psutil, "sensors_temperatures"):
                sys_temp = psutil.sensors_temperatures()
                if "cpu_thermal" in sys_temp:
                    cpu_temp = round(sys_temp["cpu_thermal"][0].current)
                else:
                    cpu_temp = None
            else:
                cpu_temp = None

            ram_percent = str(round(psutil.virtual_memory().percent, 2)).rjust(5, " ")
            disk_percent = str(round(psutil.disk_usage("/").percent, 2)).rjust(5, " ")
            network_usage = psutil.net_io_counters().bytes_sent - self.last_network_bytes
            self.last_network_bytes = psutil.net_io_counters().bytes_sent
            network_usage = humanize.naturalsize(network_usage, binary=True)
            uptime = time.time() - psutil.boot_time()
            uptime = time.strftime("%H:%M:%S", time.gmtime(uptime))
            version = "Latest Commit" if self.latest else "Behind" \
                if self.latest is not None else "Git Error"

            text = f"CPU:  {cpu_percent}% | Temp: {cpu_temp}°C | RAM: {ram_percent}%\n"
            text += f"Disk: {disk_percent}% | Network: {network_usage}\n"
            text += f"Uptime: {uptime} | Version: {version}\n"

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
            os.system("sudo reboot")

    def restart(self):
        if self.get_confirmation("Are you sure you want to restart the interface?"):
            # Exit the application and let the service manager restart it
            logging.info("Restarting the interface on user request")
            exit(0)

    def update_code(self):
        if self.get_confirmation("Are you sure you want to update the interface?"):
            logging.info("Updating the interface on user request")
            os.system("git pull")
            exit(0)

    def shutdown(self):
        if self.get_confirmation("Are you sure you want to shutdown this device?",
                                 "This action is irreversible and will require"
                                 " manual intervention to power this device back on."):
            logging.info("Shutting down the interface on user request")
            os.system("sudo shutdown now")
