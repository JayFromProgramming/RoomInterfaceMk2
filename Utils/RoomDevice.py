import json

from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging


class RoomDevice(QLabel):

    supported_types = []

    @classmethod
    def supports_type(cls, device_type):
        return device_type in cls.supported_types

    def __init__(self, auth, parent=None, device=None, large=False):
        super().__init__(parent)
        self.parent = parent
        self.device = device
        self.auth = auth
        if large:
            self.setFixedSize(300, 75)
        else:
            self.setFixedSize(145, 75)
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")

        self.toggle_button = None

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_response)
        self.command_manager = QNetworkAccessManager()
        self.command_manager.finished.connect(self.handle_command)
        self.state = None
        self.data = None
        self.parent.make_name_request(self.device)
        self.get_data()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.get_data)
        self.refresh_timer.start(5000)

    def hideEvent(self, a0):
        self.refresh_timer.stop()
        super().hideEvent(a0)

    def showEvent(self, a0):
        self.refresh_timer.start(5000)
        self.get_data()
        super().showEvent(a0)

    def get_data(self):
        request = QNetworkRequest(QUrl(f"http://moldy.mug.loafclan.org/get/{self.device}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        self.network_manager.get(request)

    def send_command(self, command):
        request = QNetworkRequest(QUrl(f"http://moldy.mug.loafclan.org/set/{self.device}"))
        # Add a json payload to the post request
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        payload = json.dumps(command)
        self.command_manager.post(request, payload.encode("utf-8"))

    def parse_data(self, data):
        raise NotImplementedError("This method must be implemented by the child class")

    def toggle_device(self):
        command = {"on": not self.state["on"]}
        if self.toggle_button is not None:
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: blue;")
        self.send_command(command)

    def handle_response(self, response):
        try:
            if str(response.error()) != "NetworkError.NoError":
                logging.error(f"Error handling response: {response.error()}")
                self.handle_failure(response)
                return
            data = response.readAll()
            data = json.loads(str(data, 'utf-8'))
            self.data = data
            self.state = data["state"]
            self.parse_data(data)
        except Exception as e:
            logging.error(f"Error handling response: {e}")
            logging.exception(e)

    def handle_command(self, response):
        try:
            # Check if the response code is 302
            response_code = response.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if response_code == 302 or response_code == 200:
                self.get_data()
            else:
                logging.error(f"Error handling command response: {response.error()}: {response_code}")
        except Exception as e:
            logging.error(f"Error handling command response: {e}")
            logging.exception(e)

    def handle_failure(self, response):
        raise NotImplementedError("This method must be implemented by the child class")
