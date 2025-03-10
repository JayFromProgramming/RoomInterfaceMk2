import json

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWidgets import QLabel, QPushButton, QSlider, QWidget

from loguru import logger as logging

from Utils.PopupBase import PopupBase
from Utils.RoomDevice import RoomDevice
from Utils.UtilMethods import has_internet


class BrightnessSliderPopup(PopupBase):

    def __init__(self, device=None):
        super().__init__(f"Brightness Control", (225, 100))
        self.device = device

        self.title = QLabel(self)
        self.title.setFixedSize(self.width(), 20)
        self.title.setFont(device.font)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("color: white; font-size: 16px; font-weight: bold; border: none;"
                                 " background-color: transparent")
        self.title.setText(f"{device.name}")
        self.title.move(0, 30)

        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.slider.setFixedSize(150, 30)
        self.slider.move(self.width() // 2 - self.slider.width() // 2, 55)
        self.slider.setRange(0, 100)
        self.slider.setValue(round(device.data["state"]["brightness"] / 255 * 100))
        self.slider.valueChanged.connect(self.update_brightness)
        self.slider.setStyleSheet("background-color: white; border: none")
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(10)
        self.slider.setSingleStep(1)

        self.slide_label = QLabel(self)
        self.slide_label.setFixedSize(50, 20)
        self.slide_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.slide_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; border: none;"
                                       " background-color: transparent")
        self.slide_label.setText(f"{self.slider.value()}%")
        self.slide_label.move(50, 100)

        self.submit_button = QPushButton(self)
        self.submit_button.setFixedSize(75, 30)
        self.submit_button.move(125, 95)
        self.submit_button.setText("Submit")
        self.submit_button.clicked.connect(self.submit_brightness)
        self.submit_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey")

        self.show()

    def update_brightness(self):
        self.slide_label.setText(f"{self.slider.value()}%")

    def submit_brightness(self):
        self.device.set_brightness(self.slider.value())
        self.close()


class LevitonDevice(RoomDevice):
    supported_types = ["LIFXDevice", "TPLinkDevice"]

    def __init__(self, parent=None, device=None, priority=0):
        super().__init__(parent.auth, parent, device, False, priority)

        self.font = parent.font
        self.name = device
        self.device_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.device_label.setText(f"[{device}]")

        self.toggle_button = QPushButton(self)
        self.toggle_button.setFont(parent.font)
        self.toggle_button.setFixedSize(135, 30)
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey")
        self.toggle_button.setText("Turn ???")
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_device)
        self.toggle_button.move(5, 40)

        self.device_text = QLabel(self)
        self.device_text.setFont(parent.font)
        self.device_text.setFixedSize(135, 20)
        self.device_text.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        self.device_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.device_text.setText("<pre>Status: ???</pre>")
        self.device_text.move(5, 20)

        self.double_click_primed = False
        self.double_click_timer = QTimer(self)
        self.double_click_timer.timeout.connect(self.resetDoubleClick)

        self.popup = None

    def update_human_name(self, name):
        super().update_human_name(name)
        self.device_label.setText(name)
        self.name = name

    def update_status(self):
        health = self.data["health"]
        if not health["online"]:
            self.device_text.setText(f"<pre>DEVICE OFFLINE</pre>")
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")
        else:
            if self.state["on"]:
                self.device_text.setText(f"<pre>Brightness: {self.data['state']['brightness'] / 255 * 100:.0f}%</pre>")
            else:
                self.device_text.setText(f"<pre>Brightness:  OFF</pre>")

    def parse_data(self, data):
        if not self.toggling:
            self.toggle_button.setText(f"Turn {['On', 'Off'][self.state['on']]}")
            button_color = "#4080FF" if self.state["on"] else "grey"
            self.toggle_button.setStyleSheet(
                f"color: black; font-size: 14px; font-weight: bold; background-color: {button_color};")
            self.update_status()
        else:
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold;"
                                             " background-color: blue;")

    def handle_failure(self, response):
        has_network = has_internet()
        if response.error() == QNetworkReply.NetworkError.ConnectionRefusedError:
            self.device_text.setText(f"<pre>SERVER DOWN</pre>")
        elif response.error() == QNetworkReply.NetworkError.OperationCanceledError and has_network:
            self.device_text.setText(f"<pre>SERVER OFFLINE</pre>")
        elif response.error() == QNetworkReply.NetworkError.InternalServerError:
            self.device_text.setText(f"<pre>SERVER ERROR</pre>")
        elif response.error() == QNetworkReply.NetworkError.OperationCanceledError and not has_network:
            self.device_text.setText(f"<pre>NETWORK ERROR</pre>")
        elif response.error() == QNetworkReply.NetworkError.HostNotFoundError and not has_network:
            self.device_text.setText(f"<pre>NO NETWORK</pre>")
        elif response.error() == QNetworkReply.NetworkError.HostNotFoundError and has_network:
            self.device_text.setText(f"<pre>SERVER NOT FOUND</pre>")
        elif response.error() == QNetworkReply.NetworkError.TemporaryNetworkFailureError:
            self.device_text.setText(f"<pre>NET FAILURE</pre>")
        elif response.error() == QNetworkReply.NetworkError.UnknownNetworkError and not has_network:
            self.device_text.setText(f"<pre>NET FAILURE</pre>")
        else:
            self.device_text.setText(f"<pre>UNKNOWN ERROR</pre>")
        self.toggle_button.setText("Turn ???")
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")

    def set_brightness(self, brightness):
        # Convert 0-100 to 0-255
        brightness = round(brightness / 100 * 255)
        logging.info(f"Setting brightness of light: {self.device} to {brightness}")
        payload = json.dumps({"brightness": brightness})
        self.send_command(payload)

    def mousePressEvent(self, a0) -> None:
        # Manually check for double click events
        try:
            if self.double_click_primed:
                self.double_click_primed = False
                self.double_click_timer.stop()
                # if self.data["info"]["dimmable"]:
                self.popup = BrightnessSliderPopup(self)
            else:
                self.double_click_primed = True
                self.double_click_timer.start(500)

        except Exception as e:
            logging.error(f"Error in SceneWidget.mousePressEvent: {e}")
            logging.exception(e)

    def resetDoubleClick(self):
        self.double_click_primed = False
