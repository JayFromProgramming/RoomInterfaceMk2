import json

from PyQt6.QtCore import Qt, QUrl, QTimer, QIODevice
from PyQt6.QtGui import QColor
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton, QColorDialog

from loguru import logger as logging

from Utils.RoomDevice import RoomDevice


class LightController(RoomDevice):

    supported_types = ["abstract_rgb"]

    def __init__(self, parent=None, device=None):
        super().__init__(parent.auth, parent, device, True)

        # This is one of many widgets that will be placed on the RoomControlHost so they shouldn't use too much space
        self.name_label = QLabel(self)
        self.name_label.setFixedSize(300, 20)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.name_label.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none; background-color: transparent")
        self.name_label.setText(f"Light: {device}")
        self.name_label.move(10, 0)

        self.info_text = QLabel(self)
        self.info_text.setFixedSize(200, 75)
        self.info_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.info_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none; background-color: transparent")
        self.info_text.setText("<pre>Color: N/A\nBrightness: N/A\nMode: N/A</pre>")
        self.info_text.move(10, 20)

        self.toggle_button = QPushButton(self)
        self.toggle_button.setFixedSize(90, 30)
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold;"
                                         "background-color: grey")
        self.toggle_button.setText("Turn ???")
        self.toggle_button.move(self.width() - self.toggle_button.width() - 10, 5)
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_light)

        self.color_picker_button = QPushButton(self)
        self.color_picker_button.setFixedSize(90, 30)
        self.color_picker_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold;"
                                               "background-color: grey")
        self.color_picker_button.setText("Set Color")
        self.color_picker_button.move(self.width() - self.color_picker_button.width() - 10, 40)
        self.color_picker_button.clicked.connect(self.open_color_picker)

    def update_human_name(self, name):
        self.name_label.setText(f"Light: {name}")

    def parse_data(self, data):
        color = self.state["color"] if not self.state["white_enabled"] else "Warm White"
        brightness = round(self.state["brightness"] / 255 * 100)

        self.info_text.setText(f"<pre>Color: {color}\nBrightness: {brightness}%\nMode: {self.state['mode']}</pre>")
        self.toggle_button.setText("Turn Off" if self.state["on"] else "Turn On")
        button_color = "#4080FF" if self.state["on"] else "grey"
        self.toggle_button.setStyleSheet(f"background: {button_color}; font-size: 14px; font-weight: bold;")

    def handle_failure(self, response):
        error_string = str(response.error()).split(".")

        self.info_text.setText(f"<pre>Server Error\n{error_string[0]}\n{error_string[1]}</pre>")
        self.toggle_button.setText("Turn ???")
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")

    def toggle_light(self):
        logging.info(f"Toggling light: {self.device} to {not self.state['on']}")
        command = {"on": not self.state["on"]}
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: blue;")
        self.send_command(command)

    def set_color(self, color):
        logging.info(f"Setting color of light: {self.device} to {color.name()}")
        self.color_picker_button.setStyleSheet(f"background: {color.name()}; font-size: 14px; font-weight: bold;")
        payload = json.dumps({"color": [color.red(), color.green(), color.blue()]})
        self.send_command(payload)

    def open_color_picker(self):
        try:
            color_picker = QColorDialog(self)
            color_picker.setStyleSheet("background-color: grey; color: black; border: none")
            color_picker.setOptions(QColorDialog.ColorDialogOption.ShowAlphaChannel)
            # Set the initial color to the current color
            color_picker.setCurrentColor(QColor(*self.state["color"]))
            color_picker.show()
            color_picker.exec()
            # Check if the color picker was closed with a color
            if color_picker.result() == 1:
                logging.info(f"Color picker closed with color: {color_picker.currentColor().name()}")
                self.set_color(color_picker.currentColor())
            else:
                logging.info("Color picker closed without a color")
        except Exception as e:
            logging.error(f"Error opening color picker: {e}")
            logging.exception(e)

