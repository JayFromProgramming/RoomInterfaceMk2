import json
import os

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel

from Modules.RoomSceneModules.SceneWidget import SceneWidget
from Utils.ScrollableMenu import ScrollableMenu
from loguru import logger as logging


class RoomSceneHost(ScrollableMenu):

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

        self.scene_widgets = []

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_network_response)

        self.hide()

        self.retry_timer = QTimer(self)
        self.retry_timer.timeout.connect(self.make_request)
        self.retry_timer.start(5000)
        self.make_request()

    def make_request(self):
        request = QNetworkRequest(QUrl(f"http://{self.host}/get_scenes"))
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
            logging.debug(f"Data: {data}")
            self.retry_timer.stop()
            self.handle_scene_data(data["scenes"])
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
            self.retry_timer.start(5000)

    def reload(self):
        for widget in self.scene_widgets:
            widget.hide()
            widget.deleteLater()
        self.scene_widgets = []
        self.make_request()

    def handle_scene_data(self, data):
        for scene in data.values():
            self.scene_widgets.append(SceneWidget(self, scene))
        self.layout_widgets()

    def move_widgets(self, offset):
        offset = round(offset)
        for widget in self.scene_widgets:
            widget.move(widget.x(), widget.y() + offset)
        self.scroll_offset = 0

    def layout_widgets(self):

        # Sort the scenes by immediate requests first
        self.scene_widgets.sort(key=lambda x: x.is_immediate, reverse=True)

        # Lay the widgets out row by row with a 10 pixel margin
        y_offset = 20
        x_offset = 10
        # Start a new row when the widgets won't fit on the current row
        for widget in self.scene_widgets:
            widget.move(x_offset, y_offset)
            widget.show()
            x_offset += widget.width() + 10
            # Wrap around to the next row if the widget won't fit on the current row
            if x_offset + widget.width() > self.width():
                x_offset = 10
                y_offset += widget.height() + 10


