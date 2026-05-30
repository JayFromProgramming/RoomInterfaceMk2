import enum

from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QNetworkReply
from PyQt6.QtWidgets import QLabel, QPushButton, QDoubleSpinBox, QSpinBox, QWidget
from loguru import logger as logging
from Utils.RoomDevice import RoomDevice
from Utils.UtilMethods import has_internet, network_error_to_string, clean_error_type
from Utils.BaseWidgets import StandardButton, TargetSelector

class MideaDevice(RoomDevice):
    supported_types = ["MideaDevice"]

    class Modes(enum.IntEnum):
        AUTO = 1
        COOL = 2
        DRY = 3
        HEAT = 4
        FAN = 5

    def __init__(self, parent=None, device=None, priority=0):
        super().__init__(parent, device, True, priority, tall=True)
        self.font = parent.font
        self.device_label.setFont(parent.font)
        self.device_label.setFixedSize(200, 20)
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.device_label.setStyleSheet("color: black; font-size: 15px; font-weight: bold; border: none")
        self.device_label.setText(f"{device}")
        self.device_label.move(self.width() // 2 - self.device_label.width() // 2, 0)
        self.unit = "°F"

        self.info_text = QLabel(self)
        self.info_text.setFixedSize(250, self.height() - self.device_label.height() - 10)
        self.info_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.info_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;"
                                     " background-color: transparent")
        self.info_text.setText("<pre>Target:  N/A\nCurrent: N/A\nState: UNKNOWN</pre>")
        self.info_text.move(10, 20)
        self.info_text.setFont(parent.font)

        self.toggle_button = StandardButton(self, "?????", callback=self.toggle_device)
        self.target_selector_button = StandardButton(self, "Set Target", callback=self.open_target_selector)

        self.spin_step = 1
        self.temperature_selector = TargetSelector(self, label="Target Temp",
                                                   initial_value=0, step=self.spin_step, unit=self.unit)
        self.temperature_selector.move(10, 30)
        self.temperature_selector.hide()

        self.fan_speed_selector = TargetSelector(self, label="Fan Speed", min_value=0, max_value=100,
                                                 initial_value=0, step=1, unit="%")
        self.fan_speed_selector.move(10, 90)
        self.fan_speed_selector.hide()

        self.eco_mode_button = StandardButton(self, "Eco", width=50, height=25, callback=self.toggle_eco_mode)
        self.eco_mode_button.move(self.temperature_selector.x() + self.temperature_selector.width() + 2,
                                  self.temperature_selector.y() + self.temperature_selector.height() // 2 - self.eco_mode_button.height() // 2)
        self.eco_mode_button.hide()

        self.fan_auto_button = StandardButton(self, "Auto", width=50, height=25, callback=self.fan_auto_button)
        self.fan_auto_button.move(self.fan_speed_selector.x() + self.fan_speed_selector.width() + 2,
                                  self.fan_speed_selector.y() + self.fan_speed_selector.height() // 2 - self.fan_auto_button.height() // 2)
        self.fan_auto_button.hide()

        self.mode_button = StandardButton(self, "AUTO", callback=self.change_mode)
        self.mode_button.hide()
        self.selected_mode = 0

        self.swing_button = StandardButton(self, "Vent Swing", callback=self.toggle_swing)
        self.turbo_button = StandardButton(self, "Turbo", callback=self.toggle_turbo)
        self.turbo_button.hide()

        self.toggle_button.move(self.width() - self.toggle_button.width() - 10, 20)
        self.swing_button.move(self.width() - self.swing_button.width() - 10,
                                self.toggle_button.y() + self.toggle_button.height() + 5)
        self.target_selector_button.move(self.width() - self.target_selector_button.width() - 10,
                                         self.swing_button.y() + self.swing_button.height() + 5)

    def update_human_name(self, name):
        self.device_label.setText(name)

    def update_state(self):
        return f"State  : {'RUNNING' if self.state['on'] else 'IDLE'}"

    def parse_data(self, data):
        button_color = "#4080FF" if self.state["on"] else "grey"

        self.toggle_button.setStyleSheet(
            f"color: black; font-size: 14px; font-weight: bold; background-color: {button_color};")
        self.info_text.setText(
            f"<pre>"
            f"Target : {self.float_format(round(self.state['target_temperature']))}{self.unit}\n"
            f"Indoor : {self.float_format(self.state['indoor_temperature'])}{self.unit}\n"
            f"Outdoor: {self.float_format(self.state['outdoor_temperature'])}{self.unit}\n"
            "\n"
            f"Mode   : {self.state['mode']}\n"
            f"Fan    : {'AUTO' if self.state['fan_auto'] else f'{self.state['fan_speed']}%'}"
                f"{'-TURBO' if self.state['turbo_fan'] else ''}\n"
            f"{self.update_state()}</pre>")
        self.toggle_button.setText(f"{['Enable', 'Disable'][self.state['on']]}")

        if self.state['vertical_swing']:
            self.swing_button.setStyleSheet(
                "color: black; font-size: 14px; font-weight: bold; background-color: #4080FF;")
        else:
            self.swing_button.setStyleSheet(
                "color: black; font-size: 14px; font-weight: bold; background-color: grey;")

        if self.state['turbo_fan']:
            self.turbo_button.setStyleSheet(
                "color: black; font-size: 14px; font-weight: bold; background-color: red;")
        else:
            self.turbo_button.setStyleSheet(
                "color: black; font-size: 14px; font-weight: bold; background-color: grey;")

        if self.state['eco_mode']:
            self.eco_mode_button.setStyleSheet(
                "color: black; font-size: 14px; font-weight: bold; background-color: green;")
        else:
            self.eco_mode_button.setStyleSheet(
                "color: black; font-size: 14px; font-weight: bold; background-color: grey;")

    @staticmethod
    def float_format(value):
        # Round the value to 2 decimal places and make sure there are 2 characters before and after the decimal point
        # e.g 01.23, 12.34, 23.40, 112.00
        return f"{value:.2f}".zfill(5)

    def round_to_half_step(self, value):
        return round(value / self.spin_step) * self.spin_step

    def open_target_selector(self):
        try:
            if self.state is None:
                return
            if self.temperature_selector.isHidden():
                self.temperature_selector.show()
                self.fan_speed_selector.show()
                self.mode_button.show()
                self.fan_auto_button.show()
                self.turbo_button.show()
                self.eco_mode_button.show()

                self.toggle_button.hide()
                self.swing_button.hide()
                self.info_text.hide()
                self.target_selector_button.setText("Submit")
                self.temperature_selector.value = self.round_to_half_step(self.state["target_temperature"])
                self.fan_speed_selector.value = self.state["fan_speed"] if not self.state["fan_auto"] else 102
                self.selected_mode = self.Modes(self.state["mode_int"])
                self.display_mode()
                self.mode_button.move(self.width() - self.target_selector_button.width() - 10,
                                      self.temperature_selector.y())
                self.turbo_button.move(self.width() - self.turbo_button.width() - 10,
                                       self.mode_button.y() + self.mode_button.height() + 5)
                self.target_selector_button.move(self.width() - self.mode_button.width() - 10,
                                                 self.turbo_button.y() + self.turbo_button.height() + 5)
            else:
                self.temperature_selector.hide()
                self.fan_speed_selector.hide()
                self.mode_button.hide()
                self.fan_auto_button.hide()
                self.turbo_button.hide()
                self.eco_mode_button.hide()
                self.toggle_button.show()
                self.target_selector_button.setText("Set Target")
                self.target_selector_button.move(self.width() - self.target_selector_button.width() - 10,
                                                 self.swing_button.y() + self.swing_button.height() + 5)
                self.swing_button.show()
                self.info_text.show()
                self.set_target()
                self.set_directionality()
        except Exception as e:
            logging.error(e)
            logging.exception(e)

    def fan_auto_button(self):
        self.fan_speed_selector.value = 102

    def toggle_swing(self):
        command = {"swing": not self.state["vertical_swing"]}
        self.send_command(command)

    def toggle_turbo(self):
        command = {"turbo": not self.state["turbo"] and not self.state["turbo_fan"]}
        self.send_command(command)

    def toggle_eco_mode(self):
        command = {"eco": not self.state["eco_mode"]}
        self.send_command(command)

    def set_target(self):
        command = {"target_value": self.temperature_selector.value,
                   "fan_speed": self.fan_speed_selector.value}
        self.send_command(command)

    def change_mode(self):
        self.selected_mode = ((self.selected_mode + 1) % 5) + 1
        self.display_mode()

    def set_directionality(self):
        command = {"mode": self.selected_mode}
        self.send_command(command)

    def display_mode(self):
        match self.selected_mode:
            case self.Modes.AUTO:
                self.mode_button.setText("Mode: AUTO")
                self.mode_button.setStyleSheet(
                    "color: black; font-size: 14px; font-weight: bold; background-color: green")
            case self.Modes.COOL:
                self.mode_button.setText("Mode: COOL")
                self.mode_button.setStyleSheet(
                    "color: black; font-size: 14px; font-weight: bold; background-color: #4080FF")
            case self.Modes.DRY:
                self.mode_button.setText("Mode: DRY")
                self.mode_button.setStyleSheet(
                    "color: black; font-size: 14px; font-weight: bold; background-color: orange")
            case self.Modes.HEAT:
                self.mode_button.setText("Mode: HEAT")
                self.mode_button.setStyleSheet(
                    "color: black; font-size: 14px; font-weight: bold; background-color: red")
            case self.Modes.FAN:
                self.mode_button.setText("Mode: FAN")
                self.mode_button.setStyleSheet(
                    "color: black; font-size: 14px; font-weight: bold; background-color: grey")

    def handle_failure(self, response):
        has_network = has_internet()
        error_message = network_error_to_string(response, has_network)
        self.info_text.setText(f"<pre>{error_message}\n{clean_error_type(response.error())}\n"
                               f"NETWORK: {'OFFLINE' if not has_network else 'ONLINE'}</pre>")
        self.toggle_button.setText("?????")
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red")
        self.swing_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red")
        self.mode_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red")
        self.info_text.show()