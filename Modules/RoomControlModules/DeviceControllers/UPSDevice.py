import datetime
import json

from PyQt6.QtCore import Qt, QUrl, QTimer, QIODevice
from PyQt6.QtGui import QColor
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWidgets import QLabel, QPushButton, QColorDialog

from loguru import logger as logging

from Utils.RoomDevice import RoomDevice
from Utils.UtilMethods import has_internet, network_error_to_string


class UPSDevice(RoomDevice):

    supported_types = ["UPSDevice"]

    def __init__(self, parent=None, device=None, priority=0):
        super().__init__(parent.auth, parent, device, True, priority)

        # This is one of many widgets that will be placed on the RoomControlHost so they shouldn't use too much space
        self.device_label.setFont(parent.font)
        self.device_label.setFixedSize(self.width(), 20)
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.device_label.setStyleSheet("color: black; font-size: 15px; font-weight: bold; border: none; background-color: transparent")
        self.device_label.setText(f"Light: [{device}]")
        self.device_label.move(10, 0)

        self.info_text = QLabel(self)
        self.info_text.setFixedSize(280, 75)
        self.info_text.setFont(parent.font)
        self.info_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.info_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none; background-color: transparent")
        self.info_text.setText("<pre>Color: N/A\nLevel: N/A\nMode:  N/A</pre>")
        self.info_text.move(10, 20)

        self.context_menu.addAction("Quick Self-Test").triggered.connect(self.quick_self_test)
        self.context_menu.addAction("Extended Self-Test").triggered.connect(self.extended_self_test)
        self.context_menu.addAction("Mute Alarm").triggered.connect(self.mute_alarm)


    def parse_data(self, data):
        if not data['health']['online']:
            self.info_text.setText(f"<pre>SERVER REPORTS\nUPS OFFLINE\n{data['health']['reason']}</pre>")
            self.toggle_button.setText("Turn ???")
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")
            # self.color_picker_button.setStyleSheet("color: black; font-size: 14px; "
            #                                        "font-weight: bold; background-color: red")
            return
        status = data["state"]["status"]
        output_watts = round(data["state"]["output_watts"])
        runtime_remaining = data["state"]["runtime_remaining"]
        runtime_text = datetime.timedelta(seconds=runtime_remaining)
        # Convert runtime_text to hh:mm:ss format
        runtime_text = str(runtime_text)

        battery_charge = round(data["state"]["battery_charge"])
        battery_voltage = data["state"]["battery_voltage"]
        input_voltage = round(data["state"]["input_voltage"])
        if input_voltage == 0:
            input_voltage = "FAIL"
        else:
            input_voltage = f"{input_voltage}v"
        output_voltage = round(data["state"]["output_voltage"])

        if "Discharging" in status and "Online" in status:
            grid_tie = "-|>"
        elif "Online" in status:
            grid_tie = "-->"
        elif "Discharging" in status:
            grid_tie = "X->"
        else:
            grid_tie = "-?-"

        self.info_text.setText(f"<pre>Status: {status}\n"
                               f"Battery: {battery_charge}%({battery_voltage}v) | {runtime_text}\n"
                               f"Power: {input_voltage} {grid_tie} {output_voltage}v | {output_watts}W</pre>")


    def handle_failure(self, response):
        has_network = has_internet()
        error_message = network_error_to_string(response, has_network)
        self.info_text.setText(f"<pre>{error_message}</pre>")
        self.toggle_button.setText("Turn ???")
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")

    def quick_self_test(self):
        command = {
            "preform_action": "self_test_quick"
        }
        self.send_command(command)

    def extended_self_test(self):
        command = {
            "preform_action": "self_test_extended"
        }
        self.send_command(command)

    def mute_alarm(self):
        command = {
            "preform_action": "silence_alarm"
        }
        self.send_command(command)

