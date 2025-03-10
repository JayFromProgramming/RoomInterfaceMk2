from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QNetworkReply
from PyQt6.QtWidgets import QLabel, QPushButton, QDoubleSpinBox, QSpinBox, QWidget
from loguru import logger as logging
from Utils.RoomDevice import RoomDevice
from Utils.UtilMethods import has_internet


class EnvivControlDevice(RoomDevice):
    supported_types = ["environment_controller"]

    def __init__(self, parent=None, device=None, priority=0):
        super().__init__(parent.auth, parent, device, True, priority)

        self.device_label.setFont(parent.font)
        self.device_label.setFixedSize(200, 20)
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.device_label.setStyleSheet("color: black; font-size: 15px; font-weight: bold; border: none")
        self.device_label.setText(f"{device}")
        self.device_label.move(10, 0)
        self.unit = "°?"

        self.info_text = QLabel(self)
        self.info_text.setFixedSize(250, 75)
        self.info_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.info_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;"
                                     " background-color: transparent")
        self.info_text.setText("<pre>Target:  N/A\nCurrent: N/A\nState: UNKNOWN</pre>")
        self.info_text.move(10, 20)
        self.info_text.setFont(parent.font)

        self.toggle_button = QPushButton(self)
        self.toggle_button.setFixedSize(95, 30)
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey")
        self.toggle_button.setText("?????")
        self.toggle_button.move(self.width() - self.toggle_button.width() - 10, 5)
        self.toggle_button.clicked.connect(self.toggle_device)
        self.toggle_button.setFont(parent.font)

        self.target_selector_button = QPushButton(self)
        self.target_selector_button.setFixedSize(95, 30)
        self.target_selector_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey")
        self.target_selector_button.setText("Set Target")
        self.target_selector_button.move(self.width() - self.target_selector_button.width() - 10, 40)
        self.target_selector_button.clicked.connect(self.open_target_selector)
        self.target_selector_button.setFont(parent.font)

        self.spin_box = QLabel(self)
        self.spin_box.setFixedSize(90, 50)
        self.spin_box.setStyleSheet("color: black; font-size: 19px; font-weight: bold; background-color: grey;"
                                    "border: none; border-radius: none;")
        self.spin_value = 0
        self.spin_step = 0.5
        self.spin_box.setText(str(self.spin_value) + self.unit)
        # Move the spin box to left center
        self.spin_box.move(10, 20)
        self.spin_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_box.hide()

        self.directionality_button = QPushButton(self)
        self.directionality_button.setFixedSize(95, 30)
        self.directionality_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey")
        self.directionality_button.setText("INC + DEC")
        self.directionality_button.clicked.connect(self.toggle_directionality)
        self.directionality_button.setFont(parent.font)
        self.directionality_button.hide()
        self.selected_directionality = 0

        self.increase_button = QPushButton(self)
        self.increase_button.setFixedSize(35, 25)
        self.increase_button.setStyleSheet("color: black; font-size: 16px; font-weight: bold; background-color: grey;"
                                           "border: black; border-radius: 0px; boarder-width: 1px;")
        self.increase_button.setText("▲")
        self.increase_button.move(self.spin_box.x() + self.spin_box.width(), 20)
        self.increase_button.clicked.connect(self.increase_target)
        self.increase_button.hide()

        self.decrease_button = QPushButton(self)
        self.decrease_button.setFixedSize(35, 25)
        self.decrease_button.setStyleSheet("color: black; font-size: 16px; font-weight: bold; background-color: grey;"
                                           "border: black; border-radius: 0px; boarder-width: 1px;")
        self.decrease_button.setText("▼")
        self.decrease_button.move(self.increase_button.x(),
                                  self.increase_button.y() + self.increase_button.height())
        self.decrease_button.clicked.connect(self.decrease_target)
        self.decrease_button.hide()

    def update_human_name(self, name):
        self.device_label.setText(name)

    def active_text(self):
        if "active_increasers" not in self.state or "active_decreasers" not in self.state:
            return "State:   NORMAL"
        active_increasers = self.state["active_increasers"]
        active_decreasers = self.state["active_decreasers"]
        if active_increasers == 0 and active_decreasers == 0:
            return "State  : IDLE"
        output = "State  : ACTIVE "
        # Use up arrow for increasers and down arrow for decreasers
        for _ in range(active_increasers):
            output += "▲"
        for _ in range(active_decreasers):
            output += "▼"
        # If there is both increasers and decreasers, display a conflict warning
        if active_increasers > 0 and active_decreasers > 0:
            output = "State  : CONFLICT ▲▼"
        return output

    def direction_arrow(self) -> str:
        if self.state["directionality"] == 0:
            return "|"
        if self.state["directionality"] == 1:  # INC Only
            return "▲"
        if self.state["directionality"] == 2:  # DEC Only
            return "▼"
        return "???"

    def update_state(self):
        self.target_selector_button.show()
        if self.data is None:
            return "State  : UNKNOWN"
        if not self.data["health"]["online"]:
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red")
            return "OFFLINE"
        elif self.data["health"]["fault"]:
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: orange")
            # Hide the set target button if the device is in a fault state
            self.target_selector_button.hide()
            return "FAULT: " + self.data["health"]["reason"]
        elif self.state["on"]:
            if self.data["health"]["down_devices"] == 0:
                return self.active_text()
            return f"State  : DEGRADED[-{self.data['health']['down_devices']}]"
        else:
            return "State  : STANDBY"

    def parse_data(self, data):
        self.unit = data["info"]["units"]
        if self.unit is None:
            self.unit = "°?"
        button_color = "#4080FF" if self.state["on"] else "grey"

        self.toggle_button.setStyleSheet(f"color: black; font-size: 14px; font-weight: bold; background-color: {button_color};")
        if self.state['current_value'] is None:
            self.info_text.setText(f"<pre>Target{self.direction_arrow()}: {self.float_format(self.state['target_value'])}{self.unit}\n"
                                   f"Current: N/A\n"
                                   f"{self.update_state()}</pre>")
        else:
            self.info_text.setText(f"<pre>Target{self.direction_arrow()}: {self.float_format(self.state['target_value'])}{self.unit}\n"
                                   f"Current: {self.float_format(self.state['current_value'])}{self.unit}\n"
                                   f"{self.update_state()}</pre>")
        self.toggle_button.setText(f"{['Enable', 'Disable'][self.state['on']]}")

    @staticmethod
    def float_format(value):
        # Round the value to 2 decimal places and make sure there are 2 characters before and after the decimal point
        # e.g 01.23, 12.34, 23.40, 112.00
        return f"{value:.2f}".zfill(5)

    def open_target_selector(self):
        try:
            if self.state is None:
                return
            if self.spin_box.isHidden():
                self.spin_box.show()
                # Hide the other buttons and rename the target selector button to "Submit"
                self.toggle_button.hide()
                self.target_selector_button.setText("Submit")
                self.directionality_button.show()
                self.spin_value = self.state["target_value"]
                self.spin_box.setText(f"{self.float_format(self.spin_value)}{self.unit}")
                self.increase_button.show()
                self.decrease_button.show()
                self.selected_directionality = self.state["directionality"]
                self.display_directionality()
                self.directionality_button.move(self.width() - self.target_selector_button.width() - 10, self.spin_box.y() - 15)
                self.target_selector_button.move(self.width() - self.directionality_button.width() - 10,
                                                 self.directionality_button.y() + self.directionality_button.height() + 5)
                self.info_text.hide()
            else:
                self.spin_box.hide()
                self.increase_button.hide()
                self.decrease_button.hide()
                self.directionality_button.hide()
                self.toggle_button.show()
                self.target_selector_button.setText("Set Target")
                self.target_selector_button.move(self.width() - self.target_selector_button.width() - 10, 40)
                self.info_text.show()
                self.set_target()
                self.set_directionality()
        except Exception as e:
            logging.error(e)
            logging.exception(e)

    def increase_target(self):
        self.spin_value += self.spin_step
        self.spin_box.setText(f"{self.float_format(self.spin_value)}{self.unit}")

    def decrease_target(self):
        self.spin_value -= self.spin_step
        self.spin_box.setText(f"{self.float_format(self.spin_value)}{self.unit}")

    def set_target(self):
        command = {"target_value": self.spin_value}
        self.send_command(command)

    def toggle_directionality(self):
        self.selected_directionality = (self.selected_directionality + 1) % 3
        self.display_directionality()

    def set_directionality(self):
        command = {"directionality": self.selected_directionality}
        self.send_command(command)

    def display_directionality(self):
        match self.selected_directionality:
            case 0:
                self.directionality_button.setText("INC + DEC")
                self.directionality_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: #4080FF")
            case 1:
                self.directionality_button.setText("INC Only")
                self.directionality_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red")
            case 2:
                self.directionality_button.setText("DEC Only")
                self.directionality_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: green")

    def handle_failure(self, response):
        error_string = str(response.error()).split(".")
        has_network = has_internet()
        if response.error() == QNetworkReply.NetworkError.ConnectionRefusedError:
            self.info_text.setText(f"<pre>SERVER DOWN\nCONNECTION REFUSED\nNETWORK:   OK</pre>")
        elif response.error() == QNetworkReply.NetworkError.OperationCanceledError and has_network:
            self.info_text.setText(f"<pre>SERVER OFFLINE\nCONNECTION TIMEOUT\nNETWORK:   OK</pre>")
        elif response.error() == QNetworkReply.NetworkError.OperationCanceledError and not has_network:
            self.info_text.setText(f"<pre>NETWORK ERROR\nCONNECTION TIMEOUT\nNETWORK: DOWN</pre>")
        elif response.error() == QNetworkReply.NetworkError.InternalServerError:
            self.info_text.setText(f"<pre>SERVER ERROR\nINTERNAL SERVER ERROR\n{error_string[-1]}</pre>")
        elif response.error() == QNetworkReply.NetworkError.HostNotFoundError and has_network:
            self.info_text.setText(f"<pre>SERVER NOT FOUND\nUNABLE TO RESOLVE HOST\nNETWORK:   OK</pre>")
        elif response.error() == QNetworkReply.NetworkError.HostNotFoundError and not has_network:
            self.info_text.setText(f"<pre>NETWORK ERROR\nNAME RESOLUTION FAILURE\nNETWORK: DOWN</pre>")
        elif response.error() == QNetworkReply.NetworkError.TemporaryNetworkFailureError:
            self.info_text.setText(f"<pre>NETWORK ERROR\nTEMPORARY NETWORK FAILURE\n{error_string[-1]}</pre>")
        elif response.error() == QNetworkReply.NetworkError.UnknownNetworkError:
            self.info_text.setText(f"<pre>NETWORK ERROR\nUNKNOWN NETWORK ERROR\n{error_string[-1]}</pre>")
        else:
            self.info_text.setText(f"<pre>UNKNOWN ERROR\n{error_string[-1]}</pre>")
        self.toggle_button.setText("?????")
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red")
        self.update_state()
        self.spin_box.hide()
        self.toggle_button.show()
        self.target_selector_button.setText("Set Target")
        self.target_selector_button.move(self.width() - self.target_selector_button.width() - 10, 40)
        self.info_text.show()
