from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PyQt6.QtWidgets import QLabel

from loguru import logger as logging

from Modules.RoomControlModules.DeviceControllers.NotInitalizedDevice import NotInitalizedDevice
from Utils.RoomDevice import RoomDevice

import os

if os.path.exists("Modules/RoomControlModules/DeviceControllers"):
    for file in os.listdir("Modules/RoomControlModules/DeviceControllers"):
        if file.endswith(".py") and not file.startswith("__"):
            # print(f"Importing {file}")
            __import__(f"Modules.RoomControlModules.DeviceControllers.{file[:-3]}")


class DeviceGroupHost(QLabel):

    def __init__(self, parent=None, group_name=None, center=False):
        super().__init__(parent)
        self.setStyleSheet("border: 2px solid #ffcd00; border-radius: 10px")
        self.auth = parent.auth
        self.host = parent.host
        self.group_name = group_name
        self.parent = parent
        self.center = center
        self.setFixedSize(parent.width(), 300)
        self.dragging = False
        self.scroll_offset = 0
        self.scroll_start = 0
        self.last_scroll = 0
        self.device_widgets = []
        self.lines = []
        self.font = self.parent.font

        self.group_label = QLabel(self)
        self.group_label.setFont(self.font)
        self.group_label.setFixedSize(self.width() - 10, 20)
        self.group_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.group_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none; "
                                       "background-color: transparent")
        self.group_label.setText(f"{group_name}")
        # Move the group label to the middle of the top
        self.group_label.move(round((self.width() - self.group_label.width()) / 2), 0)

        self.no_devices_label = QLabel(self)
        self.no_devices_label.setFont(self.font)
        self.no_devices_label.setFixedSize(300, 20)
        self.no_devices_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.no_devices_label.setStyleSheet(
            "color: white; font-size: 15px; font-weight: bold; border: none; background-color: transparent")
        self.no_devices_label.setText(f"No Devices Found For {group_name}")
        self.no_devices_label.move(round((self.width() - self.no_devices_label.width()) / 2), 20)
        self.no_devices_label.hide()

        self.layout_widgets()

        self.device_names = []
        self.delete_on_rebuild = False

        self.type_manager = QNetworkAccessManager()
        self.type_manager.finished.connect(self.create_widget)

        self.name_manager = QNetworkAccessManager()
        self.name_manager.finished.connect(self.handle_name_response)

    def make_name_request(self, device):
        request = QNetworkRequest(QUrl(f"http://{self.host}/name/{device}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        self.name_manager.get(request)

    def handle_name_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Name Error: {reply.error()}")
                return
            # Get the original query
            original_query = reply.request().url().toString()
            # Get the device name from the query
            device = original_query.split("/")[-1]
            # Get the data from the reply
            data = reply.readAll()
            for widget in self.device_widgets:
                if widget.device == device:
                    widget.update_human_name(str(data, 'utf-8'))
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def widget_add(self, widget):
        # Make a widget of the same device name isn't already in the list
        for w in self.device_widgets:
            if w.device == widget.device:
                widget.hide()
                widget.deleteLater()
                return
        self.device_widgets.append(widget)
        self.layout_widgets()

    def widgets_delete(self):
        logging.warning(f"Deleting widgets for {self.group_name}")
        for widget in self.device_widgets:
            widget.hide()
            widget.deleteLater()
        self.device_widgets.clear()
        self.layout_widgets()

    def widgets_rebuild(self):
        """
        Called by a widget when it determines that it's type does not match the server's type.
        This will remove all widgets and re-request the device types. This is useful when the server is restarted and
        the device types either change or are not yet loaded.
        :return:
        """
        try:
            logging.warning(f"Queueing rebuild for {self.group_name}")
            self.delete_on_rebuild = True
            for device in self.device_widgets:
                self.add_device(device.device, device.priority, True)
        except Exception as e:
            logging.error(f"Error rebuilding widgets: {e}")
            logging.exception(e)

    def create_widget(self, response):
        try:
            if self.delete_on_rebuild:
                self.widgets_delete()
                self.delete_on_rebuild = False
            original_query = response.request().url().toString()
            priority = response.request().rawHeader(b"Priority").data().decode("utf-8")
            # Get the device name from the query
            device = original_query.split("/")[-1]
            data = response.readAll()
            device_type = data.data().decode("utf-8")
            found = False
            for widget_class in RoomDevice.__subclasses__():
                # Find a widget class that supports the device type
                if widget_class.supports_type(device_type):
                    widget = widget_class(self, device, priority)
                    self.widget_add(widget)
                    found = True
                    break
            if not found:
                widget = NotInitalizedDevice(self, device, priority)
                self.widget_add(widget)
                logging.warning(f"Device ({device}) of type [{device_type}] not supported")
            self.layout_widgets()
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
        finally:
            response.deleteLater()

    def add_device(self, device: str, priority: int = 0, refresh: bool = False):
        request = QNetworkRequest(QUrl(f"http://{self.host}/get_type/{device}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        request.setRawHeader(b"Priority", bytes(str(priority), 'utf-8'))
        if not refresh:  # Prevents getting stuck in an infinite loop if we are rebuilding widgets
            self.device_names.append(device)
        self.type_manager.get(request)

    def sort_widgets(self):
        # Sort devices first by size, then type, then name (so the order is consistent independent of the load order)
        self.device_widgets.sort(key=lambda x: (x.width(), x.priority, x.__class__.__name__, x.device), reverse=True)

    def layout_widgets(self):
        # Lay widgets out left to right wrapping around when they reach the right edge
        if len(self.device_widgets) == 0:
            self.no_devices_label.show()
            return
        else:
            self.no_devices_label.hide()
        y_offset = 20
        x_offset = 10
        center_offset = []
        row_num = 0
        # Sort the device widgets dict by size (largest to smallest)
        self.sort_widgets()
        for widget in self.device_widgets:
            widget.move(x_offset, y_offset)
            widget.show()
            x_offset += widget.width() + 5
            widget.row_num = row_num
            # If this is the last widget don't make a new row
            if x_offset + widget.width() > self.width() and widget != self.device_widgets[-1]:
                if self.center:
                    # If centering is enabled, calculate the remaining space of the first row from the boarder
                    center_offset.append(round((self.width() - x_offset - 5) / 2))
                    row_num += 1
                x_offset = 10
                y_offset += widget.height() + 10

        if self.center:
            # If centering is enabled, calculate the remaining space of the first row from the boarder
            center_offset.append(round((self.width() - x_offset - 5) / 2))
            row_num += 1

        # If centering is enabled, move all widgets to the right by the remaining space of the first row
        if self.center:
            for widget in self.device_widgets:
                widget.move(widget.x() + center_offset[widget.row_num], widget.y())

        self.group_label.setFixedSize(self.width() - 10, 20)
        self.group_label.move(round((self.width() - self.group_label.width()) / 2), 0)

        if len(self.device_widgets) > 0:
            self.setFixedSize(self.width(),
                              y_offset + self.device_widgets[0].height() + 5)
            # self.parent.layout_widgets()
            self.parent.update()
