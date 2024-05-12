import json

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton, QSlider, QWidget

from loguru import logger as logging

from Utils.PopupBase import PopupBase
from Utils.PopupManager import PopupManager
from Utils.RoomDevice import RoomDevice


class BrightnessSliderPopup(PopupBase):

    def __init__(self, device=None):
        super().__init__(f"Brightness Control", (200, 100))
        self.device = device

        self.title = QLabel(self)
        self.title.setFixedSize(200, 20)
        self.title.setFont(device.font)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("color: white; font-size: 16px; font-weight: bold; border: none;"
                                 " background-color: transparent")
        self.title.setText(f"{device.name}")
        self.title.move(0, 30)

        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.slider.setFixedSize(150, 30)
        self.slider.move(25, 55)
        self.slider.setRange(0, 100)
        self.slider.setValue(device.data["state"]["brightness"])
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
        self.slide_label.move(25, 100)

        self.submit_button = QPushButton(self)
        self.submit_button.setFixedSize(75, 30)
        self.submit_button.move(100, 95)
        self.submit_button.setText("Submit")
        self.submit_button.clicked.connect(self.submit_brightness)
        self.submit_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey")

        self.show()


    def update_brightness(self):
        self.slide_label.setText(f"{self.slider.value()}%")

    def submit_brightness(self):
        self.device.set_brightness(self.slider.value())



class LevitonDevice(RoomDevice):
    supported_types = ["LevitonDevice"]

    def __init__(self, parent=None, device=None, priority=0):
        super().__init__(parent.auth, parent, device, False, priority)

        # self.device_label.setFont(parent.font)
        # self.device_label.setFixedSize(135, 20)
        # self.device_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.font = parent.font
        self.name = device
        self.device_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;")
        self.device_label.setText(f"{device}")

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
        elif health["fault"]:
            self.device_text.setText(f"<pre>Online: FAULT</pre>")
            self.toggle_button.setStyleSheet(
                "color: black; font-size: 14px; font-weight: bold; background-color: orange;")
        else:
            if self.data["info"]["dimmable"]:
                if self.state["on"]:
                    self.device_text.setText(f"<pre>Brightness: {self.data['state']['brightness']}%</pre>")
                else:
                    self.device_text.setText(f"<pre>Brightness:  OFF</pre>")
            else:
                self.device_text.setText(f"<pre>Online: IDLE</pre>")

    def parse_data(self, data):
        self.toggle_button.setText(f"Turn {['On', 'Off'][self.state['on']]}")
        button_color = "#4080FF" if self.state["on"] else "grey"
        self.toggle_button.setStyleSheet(
            f"color: black; font-size: 14px; font-weight: bold; background-color: {button_color};")
        self.update_status()

    def handle_failure(self, response):
        self.device_text.setText(f"<pre>Server Error</pre>")
        self.toggle_button.setText("Turn ???")
        self.device_text.setText(f"<pre>Network Error</pre>")
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")

    def set_brightness(self, brightness):
        logging.info(f"Setting brightness of light: {self.device} to {brightness}")
        payload = json.dumps({"brightness": brightness})
        self.send_command(payload)

    def mousePressEvent(self, a0) -> None:
        # Manually check for double click events
        try:
            if self.double_click_primed:
                self.double_click_primed = False
                self.double_click_timer.stop()
                if self.data["info"]["dimmable"]:
                    self.popup = BrightnessSliderPopup(self)
            else:
                self.double_click_primed = True
                self.double_click_timer.start(500)

        except Exception as e:
            logging.error(f"Error in SceneWidget.mousePressEvent: {e}")
            logging.exception(e)

    def resetDoubleClick(self):
        self.double_click_primed = False
