import json
import os
import time

from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel

from Modules.RoomControlModules.DeviceGroupHost import DeviceGroupHost
from loguru import logger as logging


class RoomControlHost(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedSize(parent.width(), parent.height() - self.y())
        self.dragging = False
        self.focused = False
        self.font = self.parent.get_font("JetBrainsMono-Bold")

        # Scroll related variables
        self.scroll_offset = 0
        self.scroll_start = 0
        self.scroll_velocity = 0  # Pixels per second
        self.scroll_velocity_decay = 0.8  # Percentage of velocity to keep each frame
        self.scroll_max_velocity = 100  # Pixels per second
        self.scroll_total_offset = 0
        self.last_scroll = time.time()

        self.loading_label = QLabel(self)
        self.loading_label.setFont(self.font)
        self.loading_label.setFixedSize(600, 60)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none; background-color: transparent")
        self.loading_label.setText("Loading Room Control Schema, Please Wait...")
        self.loading_label.move(round((self.width() - self.loading_label.width()) / 2), 20)

        self.scroll_motion_timer = QTimer(self)
        self.scroll_motion_timer.timeout.connect(self.scroll_motion)

        self.has_schema = False
        self.setStyleSheet("boarder: 2px solid #ffcd00; border-radius: 10px")
        if os.path.exists("Config/auth.json"):
            with open("Config/auth.json", "r") as f:
                data = json.load(f)
                self.auth = data["auth"]
                self.host = data["host"]
        else:
            os.makedirs("Config", exist_ok=True)
            with open("Config/auth.json", "w") as f:
                data = {
                    "auth": "",
                    "host": ""
                }
                json.dump(data, f)
                raise Exception("Please fill out the auth.json file with the proper information")

        self.starred_device_host = DeviceGroupHost(self, "Starred Devices", center=True)
        self.device_group_hosts = []
        self.ungrouped_device_host = DeviceGroupHost(self, "Ungrouped Devices")

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_network_response)

        self.retry_timer = QTimer(self)
        self.retry_timer.timeout.connect(self.make_request)
        self.retry_timer.start(5000)

        self.make_request()

    def make_request(self):
        request = QNetworkRequest(QUrl("http://moldy.mug.loafclan.org/get_schema"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        self.network_manager.get(request)

    def handle_network_response(self, reply):
        try:
            data = reply.readAll()
            try:
                data = json.loads(str(data, 'utf-8'))
            except Exception as e:
                logging.error(f"Error parsing network response: {e}")
                logging.error(f"Data: {data}")
                self.loading_label.setText(f"Error Loading Room Control Schema, Retrying...\n{e}")
                return
            for device_name, values in data.items():
                # Check if the device is in a group
                if values["starred"] is True:
                    self.starred_device_host.add_device(device_name)
                if values["group"] is not None:
                    found = False
                    for widget in self.device_group_hosts:
                        if widget.group_name == values["group"]:
                            widget.add_device(device_name)
                            found = True
                            break
                    if not found:
                        self.device_group_hosts.append(DeviceGroupHost(self, values["group"]))
                        self.device_group_hosts[-1].add_device(device_name)
                else:
                    self.ungrouped_device_host.add_device(device_name)
            self.layout_widgets()
            self.loading_label.hide()
            self.retry_timer.stop()  # Stop retrying if we got a response
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            self.loading_label.setText(f"Error Loading Room Control Schema, Retrying...\n{e}")
            logging.exception(e)

    def set_focus(self, focus):
        print("Toggling focus")
        self.focused = focus
        self.resizeEvent(None)
        self.layout_widgets()

    def resizeEvent(self, event):
        # Our height is the height from our x position to the bottom of the window
        self.setFixedSize(self.parent.width(), self.parent.height() - self.y() - 30)
        # Calculate the width of the device group hosts while allowing for a 20 pixel margin on each side
        width = self.width() - 40
        self.starred_device_host.setFixedSize(width, 0)
        self.ungrouped_device_host.setFixedSize(width, 0)
        for widget in self.device_group_hosts:
            widget.setFixedSize(width, 0)
            widget.layout_widgets()
        self.starred_device_host.layout_widgets()
        self.ungrouped_device_host.layout_widgets()
        self.layout_widgets()

    def mousePressEvent(self, event):
        try:
            if not self.focused:
                return
            self.dragging = True
            self.scroll_start = event.pos().y()
            self.last_scroll = time.time()
            self.scroll_motion_timer.stop()
        except Exception as e:
            logging.error(f"Error handling mouse press event: {e}")
            logging.exception(e)

    def mouseMoveEvent(self, ev):
        try:
            if self.dragging:
                # Offset the entire room control host by the difference in the y position
                self.scroll_offset += ev.pos().y() - self.scroll_start
                # Calculate the velocity of the scroll
                self.scroll_velocity = (ev.pos().y() - self.scroll_start) / (time.time() - self.last_scroll)
                self.scroll_start = ev.pos().y()
                # Move the widgets by the scroll offset
                self.move_widgets(self.scroll_offset)
        except Exception as e:
            logging.error(f"Error handling mouse move event: {e}")
            logging.exception(e)

    def mouseReleaseEvent(self, ev):
        try:
            self.dragging = False
            # Start the scroll motion timer to decay the scroll velocity and move the widgets
            self.last_scroll = time.time()
            self.scroll_motion_timer.start(round(1000 / 60))
        except Exception as e:
            logging.error(f"Error handling mouse release event: {e}")
            logging.exception(e)

    def scroll_motion(self):
        try:
            # Decay the scroll velocity
            self.scroll_velocity = max(-self.scroll_max_velocity, min(self.scroll_max_velocity, self.scroll_velocity))
            self.scroll_velocity *= self.scroll_velocity_decay
            # Move the widgets by the scroll velocity
            self.scroll_offset += self.scroll_velocity
            self.move_widgets(self.scroll_offset)
            # If the scroll velocity is less than 1 pixel per second, stop the scroll motion timer
            if abs(self.scroll_velocity) < 1:
                self.scroll_motion_timer.stop()
        except Exception as e:
            logging.error(f"Error handling scroll motion: {e}")
            logging.exception(e)

    def move_widgets(self, y):
        y = round(y)
        # Determine if this movement would cause the ungrouped device host to go off the top of the screen
        if self.ungrouped_device_host.y() + y < 0:
            y = -self.ungrouped_device_host.y()
            self.scroll_velocity = 0
        # Determine if this movement would cause the starred device host to go below its original position
        if self.starred_device_host.y() + y > 0:
            y = -self.starred_device_host.y()
            self.scroll_velocity = 0
        self.scroll_total_offset += y
        self.starred_device_host.move(20, y)
        y += self.starred_device_host.height() + 10
        for widget in self.device_group_hosts:
            widget.move(20, y)
            y += widget.height() + 10
        self.ungrouped_device_host.move(20, y)

    def layout_widgets(self):
        # If we are not focused only show the starred device host
        if not self.focused:
            self.starred_device_host.center = True
            self.starred_device_host.show()
            self.starred_device_host.move(20, 0)
            # self.starred_device_host.setFixedSize(self.width(), self.height() - self.y())
            for widget in self.device_group_hosts:
                widget.hide()
            self.ungrouped_device_host.hide()
            return
        else:
            # Layout each device group host out in a vertical line
            y = 0
            self.starred_device_host.center = False
            self.starred_device_host.show()
            self.starred_device_host.move(20, y)
            y += self.starred_device_host.height() + 10
            for widget in self.device_group_hosts:
                widget.show()
                widget.move(20, y)
                y += widget.height() + 10
            self.ungrouped_device_host.show()
            self.ungrouped_device_host.move(20, y)
