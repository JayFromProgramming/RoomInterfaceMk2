import json
import os

from PyQt6.QtCore import QTimer, QUrl, Qt
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging

from Modules.SystemControlModules.LocalInterfaceControl import LocalInterfaceControl
from Modules.SystemControlModules.RemoteInterfaceControl import RemoteInterfaceControl
from Utils.ScrollableMenu import ScrollableMenu
from Utils.UtilMethods import get_host, get_auth


class SystemControlHost(ScrollableMenu):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedSize(parent.width(), parent.height() - self.y())
        self.setStyleSheet("border: 2px solid #ffcd00; border-radius: 10px")

        self.system_widgets = []
        self.system_widgets.append(LocalInterfaceControl(self))

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_network_response)

        self.hide()

        self.title_label = QLabel("System Interface", self)
        self.title_label.setStyleSheet("font-size: 18px; color: #ffcd00; background-color: transparent;"
                                       " border: none; border-radius: 0px;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFixedSize(self.width(), 20)
        self.title_label.move(round((self.width() - self.title_label.width()) / 2), 5)
        self.title_label.setFont(parent.get_font("JetBrainsMono-Regular"))

        self.retry_timer = QTimer(self)
        self.retry_timer.timeout.connect(self.make_request)
        self.retry_timer.start(5000)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_interfaces)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes
        self.make_request()

    def refresh_interfaces(self):
        if self.isHidden(): # Only refresh the interface objects if the host is not visible
            logging.info("Refreshing system interfaces")
            self.make_request()

    def make_request(self):
        try:
            request = QNetworkRequest(QUrl(f"http://{get_host()}/get_system_monitors"))
            request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
            self.network_manager.get(request)
        except Exception as e:
            logging.error(f"Error making network request: {e}")
            self.retry_timer.start(5000)

    def clear_remote_widgets(self):
        for widget in self.system_widgets:
            if isinstance(widget, RemoteInterfaceControl):
                widget.deleteLater()
        self.system_widgets = [widget for widget in self.system_widgets if not isinstance(widget, RemoteInterfaceControl)]

    def handle_network_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Error: {reply.error()}")
                self.retry_timer.start(5000)
                return
            data = reply.readAll()
            data = data.data().decode("utf-8")
            data = json.loads(data)
            self.retry_timer.stop()
            self.clear_remote_widgets()
            for name in data["system_monitors"]:
                self.system_widgets.append(RemoteInterfaceControl(self, name))
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
            self.retry_timer.start(5000)
        finally:
            reply.deleteLater()

    def showEvent(self, a0) -> None:
        try:
            for widget in self.system_widgets:
                widget.show()
            super().showEvent(a0)
        except Exception as e:
            logging.error(f"Error showing system control host: {e}")
            logging.exception(e)

    def hideEvent(self, a0) -> None:
        for widget in self.system_widgets:
            widget.hide()
        super().hideEvent(a0)

    def layout_widgets(self):
        try:
            # Lay the widgets out row by row with a 10 pixel margin
            y_offset = 30
            x_offset = 10
            first_row_x_offset = 0
            # Sort the widgets by device name
            # sorted_widgets = sorted(self.system_widgets, key=lambda w: w.device_name)
            # Start a new row when the widgets won't fit on the current row
            for widget in self.system_widgets:
                widget.move(x_offset, y_offset)
                x_offset += widget.width() + 10
                # Wrap around to the next row if the widget won't fit on the current row
                if x_offset + widget.width() > self.width():
                    if first_row_x_offset == 0:
                        first_row_x_offset = round((self.width() - x_offset - 10) / 2)
                    x_offset = 10
                    y_offset += widget.height() + 10
            # Center the widgets
            for widget in self.system_widgets:
                widget.move(widget.x() + first_row_x_offset, widget.y())
        except Exception as e:
            logging.error(f"Error laying out system control host widgets: {e}")
            logging.exception(e)

    def move_widgets(self, y):
        pass
