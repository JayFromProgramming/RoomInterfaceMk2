import json
import os

from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from loguru import logger as logging

from Modules.SystemControlModules.LocalInterfaceControl import LocalInterfaceControl
from Modules.SystemControlModules.RemoteInterfaceControl import RemoteInterfaceControl
from Utils.ScrollableMenu import ScrollableMenu


class SystemControlHost(ScrollableMenu):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(parent.width(), parent.height() - self.y())
        self.setStyleSheet("border: 2px solid #ffcd00; border-radius: 10px")
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

        self.system_widgets = []
        self.system_widgets.append(LocalInterfaceControl(self))

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_network_response)

        self.hide()

        self.retry_timer = QTimer(self)
        self.retry_timer.timeout.connect(self.make_request)
        self.retry_timer.start(5000)
        self.make_request()

    def make_request(self):
        request = QNetworkRequest(QUrl(f"http://{self.host}/get_system_monitors"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        self.network_manager.get(request)

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
            for name in data["system_monitors"]:
                self.system_widgets.append(RemoteInterfaceControl(self, name))
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
            self.retry_timer.start(5000)

    def handle_system_data(self, data):
        pass

    def layout_widgets(self):
        # Lay the widgets out row by row with a 10 pixel margin
        y_offset = 20
        x_offset = 10
        first_row_x_offset = 0
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

    def move_widgets(self, y):
        pass
