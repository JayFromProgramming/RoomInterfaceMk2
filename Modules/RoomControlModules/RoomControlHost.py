import json

from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWidgets import QLabel

from Modules.RoomControlModules.DeviceGroupHost import DeviceGroupHost
from loguru import logger as logging

from Utils.ScrollableMenu import ScrollableMenu
from Utils.UtilMethods import get_host, get_auth, clean_error_type


class RoomControlHost(ScrollableMenu):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(parent.width(), parent.height() - self.y())
        self.internet_connected = False

        self.schema_data = {}
        self.loading_label = QLabel(self)
        self.loading_label.setFont(self.font)
        self.loading_label.setFixedSize(600, 60)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;"
                                         " background-color: transparent")
        self.loading_label.setText("Loading Room Control Schema, Please Wait...")
        self.loading_label.move(round((self.width() - self.loading_label.width()) / 2), 20)

        self.has_schema = False
        self.setStyleSheet("border-radius: 10px")

        self.starred_device_host = DeviceGroupHost(self, "Starred Devices", center=True)
        self.device_group_hosts = []
        self.ungrouped_device_host = DeviceGroupHost(self, "Ungrouped Devices")

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_network_response)

        self.retry_timer = QTimer(self)
        self.retry_timer.timeout.connect(self.make_request)
        self.retry_timer.start(5000)  # Retry every 5 seconds
        self.retry_time = 5

        self.make_request()

    def reload_schema(self):
        self.loading_label.show()
        self.starred_device_host.deleteLater()
        self.ungrouped_device_host.deleteLater()
        for widget in self.device_group_hosts:
            widget.deleteLater()
        self.device_group_hosts.clear()
        self.starred_device_host = DeviceGroupHost(self, "Starred Devices", center=True)
        self.device_group_hosts = []
        self.ungrouped_device_host = DeviceGroupHost(self, "Ungrouped Devices")
        self.make_request()

    def make_request(self):
        request = QNetworkRequest(QUrl(f"{get_host()}/get_schema?interface_name=testing"))
        request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
        self.network_manager.get(request)

    def process_schema_response(self, data):
        for device_name, values in data.items():
            priority = values.get("priority", 0)
            if priority is None:
                priority = 0
            # Check if the device is in a group
            if values["starred"] is True:
                self.starred_device_host.add_device(device_name, priority)
            if values["group"] is not None:
                found = False
                for widget in self.device_group_hosts:
                    if widget.group_name == values["group"]:
                        widget.add_device(device_name, priority)
                        found = True
                        break
                if not found:
                    self.device_group_hosts.append(DeviceGroupHost(self, values["group"]))
                    self.device_group_hosts[-1].add_device(device_name, priority)
            else:
                self.ungrouped_device_host.add_device(device_name, priority)

    def handle_network_response(self, reply):  # Schema response handler
        try:
            data = reply.readAll()
            if reply.error() != QNetworkReply.NetworkError.NoError:
                logging.error(f"Error: {reply.error()}")
                self.loading_label.setText(
                    f"Error Loading Room Control Schema\n{clean_error_type(reply.error())}\n"
                    f"Attempting to acquire schema again...")
                return
            try:
                data = json.loads(str(data, 'utf-8'))
            except Exception as e:
                logging.error(f"Error parsing network response: {e}")
                logging.error(f"Data: {data}")
                self.loading_label.setText(f"Error Loading Room Control Schema, Retrying...\n{e}")
                return
            self.process_schema_response(data)
            self.loading_label.hide()
            self.retry_timer.stop()  # Stop retrying if we got a response
            self.layout_widgets()
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            self.loading_label.setText(f"Error Loading Room Control Schema, Retrying...\n{e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def resizeEvent(self, event):
        # Our height is the height from our x position to the bottom of the window
        self.setFixedSize(self.parent.width(), self.parent.height() - self.y() - 30)
        # Calculate the width of the device group hosts while allowing for a 20 pixel margin on each side
        self.layout_widgets()

    def set_focus(self, focus):
        # Move this widget when it is focused
        try:
            self.focused = focus
            if focus:
                self.move(0, 90)
                self.setFixedSize(self.parent.width(), self.parent.height() - self.y() - 30)
            else:
                self.move(0, self.parent.forecast.height() + self.parent.forecast.y() + 10)
                self.setFixedSize(self.parent.width(), self.parent.height() - self.y() - 30)
        except Exception as e:
            logging.error(f"Error setting focus: {e}")
            logging.exception(e)

    def move_widgets(self, y):
        y = round(y)
        # Determine if this movement would cause the ungrouped device host to go off the top of the screen
        if self.ungrouped_device_host.y() + y < -self.ungrouped_device_host.height() - 200:
            y = -self.ungrouped_device_host.y() - self.ungrouped_device_host.height() - 200
            self.scroll_velocity = 0
            self.scroll_offset = y
        # Determine if this movement would cause the starred device host to go below its original position
        if len(self.device_group_hosts) == 0:
            if self.ungrouped_device_host.y() + y > 10:
                y = 5
                self.scroll_velocity = 0
                self.scroll_offset = y
        else:
            if self.device_group_hosts[0].y() + y > 10:
                y = 5
                self.scroll_velocity = 0
                self.scroll_offset = y

        self.scroll_total_offset += y
        # self.starred_device_host.move(20, y)
        # y += self.starred_device_host.height() + 10
        for widget in self.device_group_hosts:
            widget.move(20, y)
            y += widget.height() + 10
        self.ungrouped_device_host.move(20, y)

    def layout_widgets(self, no_resize=False):
        width = self.width() - 40
        if not no_resize:
            self.starred_device_host.setFixedSize(width, 0)
            self.ungrouped_device_host.setFixedSize(width, 0)
            self.ungrouped_device_host.layout_widgets()
            self.starred_device_host.layout_widgets()
            for widget in self.device_group_hosts:
                widget.setFixedSize(width, 0)
                widget.layout_widgets()
        # If we are not focused only show the starred device host
        if not self.focused:
            self.starred_device_host.center = True
            self.allow_scroll = False
            self.starred_device_host.layout_widgets()
            self.starred_device_host.show()
            self.starred_device_host.move(20, 0)
            # self.starred_device_host.setFixedSize(self.width(), self.height() - self.y())
            for widget in self.device_group_hosts:
                widget.hide()
            self.ungrouped_device_host.hide()
            return
        else:
            # Layout each device group host out in a vertical line
            y = 5
            self.starred_device_host.center = False
            self.allow_scroll = True
            # self.starred_device_host.layout_widgets()
            self.starred_device_host.hide()
            # self.starred_device_host.move(20, y)
            # y += self.starred_device_host.height() + 10
            for widget in self.device_group_hosts:
                widget.show()
                widget.move(20, y)
                y += widget.height() + 10
            self.ungrouped_device_host.show()
            self.ungrouped_device_host.move(20, y)
