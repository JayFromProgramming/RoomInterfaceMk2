import json
import random
import time

from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QMenu, QInputDialog
from loguru import logger as logging

from Utils.UtilMethods import has_internet


class RoomDevice(QLabel):

    supported_types = []

    @classmethod
    def supports_type(cls, device_type):
        return device_type in cls.supported_types

    def __init__(self, auth, parent=None, device=None, large=False, priority=0):
        super().__init__(parent)
        self.parent = parent
        self.device = device
        self.priority = priority
        self.host = parent.host
        self.auth = auth
        self.device_type = False
        if large:
            self.setFixedSize(295, 75)
        else:
            self.setFixedSize(145, 75)
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")
        self.not_found = False

        self.toggle_button = None

        self.device_label = QLabel(self)
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.device_label.setFixedSize(self.width(), 22)
        self.device_label.setFont(parent.font)

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_response)
        self.command_manager = QNetworkAccessManager()
        self.command_manager.finished.connect(self.handle_command)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.get_data)
        self.refresh_timer.setSingleShot(True)

        self.name_update_timer = QTimer(self)
        self.name_update_timer.timeout.connect(self.parent.make_name_request)
        self.name_update_timer.setSingleShot(True)

        self.context_menu = QMenu(self)
        self.context_menu.addAction("Rename").triggered.connect(self.rename_device)
        self.context_menu.setStyleSheet("color: white; background-color: black")

        self.state = None
        self.data = None
        self.has_names = False
        self.human_name = None

        self.toggling = False
        self.last_toggle_state = None
        self.toggle_time = 0

    def update_human_name(self, name):
        # print(f"Updating name to {name}")
        self.has_names = True
        self.human_name = name
        self.device_label.setText(name)
        if not self.isHidden():
            self.name_update_timer.start(300000 + random.randint(0, 60000))  # Update the name every 5-6 minutes
        else:
            self.name_update_timer.start(900000 + random.randint(0, 120000)) # Update the name every 15-17 minutes

    def hideEvent(self, a0):
        self.refresh_timer.stop()
        super().hideEvent(a0)

    def showEvent(self, a0):
        # Randomize the refresh time to prevent all the devices from refreshing at the same time
        self.refresh_timer.start(5000 + random.randint(0, 1000))
        self.get_data()
        if not self.has_names:
            self.parent.make_name_request(self.device)
        super().showEvent(a0)

    def get_data(self):
        request = QNetworkRequest(QUrl(f"http://{self.host}/get/{self.device}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        request.setTransferTimeout(5000)
        self.network_manager.get(request)

    def send_command(self, command):
        request = QNetworkRequest(QUrl(f"http://{self.host}/set/{self.device}"))
        # Add a json payload to the post request
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        payload = json.dumps(command)
        self.command_manager.post(request, payload.encode("utf-8"))
        self.refresh_timer.start(500)

    def rename_device(self):
        try:
            diag = QInputDialog()
            diag.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            diag.setLabelText("Enter a new name for the device:")
            diag.setTextValue(self.human_name)
            diag.setOkButtonText("Submit")
            diag.setCancelButtonText("Cancel")
            diag.exec()
            new_name = diag.textValue()
            if new_name == "":
                return
            request = QNetworkRequest(QUrl(f"http://{self.host}/set_name/{self.device}/{new_name}"))
            request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
            self.command_manager.get(request)
            QTimer.singleShot(500, self.parent.widgets_rebuild)
        except Exception as e:
            logging.error(f"Error renaming device: {e}")
            logging.exception(e)

    def parse_data(self, data):
        raise NotImplementedError("This method must be implemented by the child class")

    def toggle_device(self):
        command = {"on": not self.state["on"]}
        if self.toggle_button is not None:
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold;"
                                             " background-color: blue;")
            self.toggling = True
            self.last_toggle_state = self.state["on"]
            self.toggle_time = time.time()
            # Increase the refresh rate so that we can see the change faster
            self.refresh_timer.start(500)
        self.send_command(command)

    def check_device_type(self, data):
        try:
            if "type" in data:
                if self.device_type is False:  # If the device type is not set (false instead of None because None is a valid type)
                    self.device_type = data["type"]
                else:
                    if self.device_type != data["type"]:
                        logging.error(f"Device type mismatch: {self.device_type} != {data['type']}")
                        self.parent.widgets_rebuild()  # Rebuild the widgets to fix the type mismatch
            else:
                logging.error(f"Device type not found in data: {data}")
        except Exception as e:
            logging.error(f"Error checking device type: {e}")
            logging.exception(e)

    def handle_response(self, response):
        try:
            if str(response.error()) != "NetworkError.NoError":
                logging.error(f"Device data error: {response.error()} : {has_internet()}")
                self.handle_failure(response)
                return
            data = response.readAll()
            if data == b'Device not found':
                self.not_found = True
                self.parse_data(None)
                return
            data = json.loads(str(data, 'utf-8'))
            self.data = data
            self.state = data["state"]
            self.check_device_type(data)
            if self.toggling and self.state["on"] != self.last_toggle_state:
                self.toggling = False
            self.parse_data(data)
        except Exception as e:
            logging.error(f"Error handling response: {e}")
            logging.exception(e)
        finally:
            if not self.toggling:
                self.refresh_timer.start(4000 + random.randint(0, 1500))
            else:
                self.refresh_timer.start(1000)
            response.deleteLater()

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
        finally:
            response.deleteLater()

    def contextMenuEvent(self, ev):
        self.context_menu.exec(ev.globalPos())

    def handle_failure(self, response):
        raise NotImplementedError("This method must be implemented by the child class")
