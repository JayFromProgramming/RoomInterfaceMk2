from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging

from Modules.RoomSceneModules.SceneEditor.DeviceTile import DeviceTile
from Utils.ScrollableMenu import ScrollableMenu


class DeviceColumn(ScrollableMenu):

    def __init__(self, parent, column_name, starting_device_ids=None):
        super().__init__(parent, parent.font)
        self.parent = parent
        self.host = parent.host
        self.auth = parent.auth
        self.font = self.parent.font
        self.setFixedSize(290, 490)
        self.setStyleSheet("background-color: transparent; border: 2px solid #ffcd00; border-radius: 10px")

        self.column_name = QLabel(self)
        self.column_name.setFont(self.font)
        self.column_name.setFixedSize(300, 20)
        self.column_name.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.column_name.setStyleSheet("color: #ffcd00; font-size: 16px; font-weight: bold; border: none;")
        self.column_name.setText(column_name)
        self.column_name.move(0, 0)

        self.name_manager = QNetworkAccessManager()
        self.name_manager.finished.connect(self.handle_name_response)

        self.device_labels = []
        logging.debug(f"Starting device ids: {starting_device_ids}")
        if starting_device_ids is not None:
            for device in starting_device_ids.keys():
                self.device_labels.append(DeviceTile(self, device))
        logging.debug(f"Device labels: {self.device_labels}")

        self.layout_widgets()

    def make_name_request(self, device):
        request = QNetworkRequest(QUrl(f"http://{self.host}/name/{device}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        self.name_manager.get(request)

    def handle_name_response(self, reply):
        try:
            # Get the original query
            original_query = reply.request().url().toString()
            # Get the device name from the query
            device = original_query.split("/")[-1]
            # Get the data from the reply
            data = reply.readAll()
            for widget in self.device_labels:
                if widget.device == device:
                    widget.update_human_name(str(data, 'utf-8'))
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)

    def has_device(self, device):
        for label in self.device_labels:
            if label.device == device:
                return True
        return False

    def add_device(self, device):
        tile = DeviceTile(self, device)
        tile.show()
        self.device_labels.append(tile)
        self.layout_widgets()

    def move_widgets(self, y):
        y = round(y)
        for label in self.device_labels:
            label.move(5, y)
            y += label.height() + 5
        self.repaint()

    def layout_widgets(self):
        y = 30
        for label in self.device_labels:
            label.move(5, y)
            y += label.height() + 5
        self.repaint()

