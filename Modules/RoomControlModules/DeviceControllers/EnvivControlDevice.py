from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QDoubleSpinBox, QSpinBox, QWidget
from loguru import logger as logging
from Utils.RoomDevice import RoomDevice


class EnvivControlDevice(RoomDevice):
    supported_types = ["environment_controller"]

    def __init__(self, parent=None, device=None):
        super().__init__(parent.auth, parent, device, True)

        self.device_label = QLabel(self)
        self.device_label.setFont(parent.font)
        self.device_label.setFixedSize(200, 20)
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.device_label.setStyleSheet("color: black; font-size: 15px; font-weight: bold; border: none")
        self.device_label.setText(f"{device}")
        self.device_label.move(10, 0)
        self.unit = "°?"

        self.info_text = QLabel(self)
        self.info_text.setFixedSize(200, 75)
        self.info_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.info_text.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none; background-color: transparent")
        self.info_text.setText("<pre>Target: N/A\nCurrent: N/A\nState: UNKNOWN</pre>")
        self.info_text.move(10, 20)
        self.info_text.setFont(parent.font)

        self.toggle_button = QPushButton(self)
        self.toggle_button.setFixedSize(90, 30)
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey")
        self.toggle_button.setText("?????")
        self.toggle_button.move(self.width() - self.toggle_button.width() - 10, 5)
        self.toggle_button.clicked.connect(self.toggle_device)
        self.toggle_button.setFont(parent.font)

        self.target_selector_button = QPushButton(self)
        self.target_selector_button.setFixedSize(90, 30)
        self.target_selector_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey")
        self.target_selector_button.setText("Set Target")
        self.target_selector_button.move(self.width() - self.target_selector_button.width() - 10, 40)
        self.target_selector_button.clicked.connect(self.open_target_selector)
        self.target_selector_button.setFont(parent.font)

        self.spin_box = QDoubleSpinBox(self)
        self.spin_box.setFixedSize(90, 40)
        self.spin_box.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: grey;"
                                    "border: none; border-radius: none")
        self.spin_box.setRange(0, 100)
        self.spin_box.setSingleStep(0.5)
        self.spin_box.setValue(0)
        self.spin_box.setSuffix(self.unit)
        # Move the spin box to left center
        self.spin_box.move(10, 20)
        self.spin_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_box.hide()

    def update_human_name(self, name):
        self.device_label.setText(name)

    def update_state(self):
        if not self.data["health"]["online"]:
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red")
            return "OFFLINE"
        elif self.data["health"]["fault"]:
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: orange")
            return "FAULT"
        elif self.state["on"]:
            return "NORMAL" if self.data["health"]["down_devices"] == 0 else "DEGRADED"
        else:
            return "STANDBY"

    def parse_data(self, data):
        self.unit = data["info"]["units"]
        button_color = "#4080FF" if self.state["on"] else "grey"

        self.toggle_button.setStyleSheet(f"color: black; font-size: 14px; font-weight: bold; background-color: {button_color};")
        if self.state['current_value'] is None:
            self.info_text.setText(f"<pre>Target:  {round(self.state['target_value'], 2)}{self.unit}\n"
                                   f"Current: N/A\n"
                                   f"State: {self.update_state()}</pre>")
        else:
            self.info_text.setText(f"<pre>Target:  {round(self.state['target_value'], 2)}{self.unit}\n"
                                   f"Current: {round(self.state['current_value'], 2)}{self.unit}\n"
                                   f"State: {self.update_state()}</pre>")
        self.toggle_button.setText(f"{['Enable', 'Disable'][self.state['on']]}")

    def toggle_device(self):
        command = {"on": not self.state["on"]}
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: blue")
        self.send_command(command)

    def open_target_selector(self):
        try:
            if self.spin_box.isHidden():
                self.spin_box.show()
                # Hide the other buttons and rename the target selector button to "Submit"
                self.toggle_button.hide()
                self.target_selector_button.setText("Submit")
                self.spin_box.setValue(self.state["target_value"])
                self.spin_box.setSuffix(self.unit)
                self.target_selector_button.move(self.width() - self.target_selector_button.width() - 10,
                                                 self.spin_box.y())
                self.info_text.hide()
            else:
                self.spin_box.hide()
                self.toggle_button.show()
                self.target_selector_button.setText("Set Target")
                self.target_selector_button.move(self.width() - self.target_selector_button.width() - 10, 40)
                self.info_text.show()
                self.set_target()
        except Exception as e:
            logging.error(e)
            logging.exception(e)

    def set_target(self):
        command = {"target_value": self.spin_box.value()}
        self.send_command(command)

    def handle_failure(self, response):
        self.info_text.setText(f"<pre>Server Error</pre>")
        self.toggle_button.setText("?????")
        self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red")
        self.update_state()
        self.spin_box.hide()
        self.toggle_button.show()
        self.target_selector_button.setText("Set Target")
        self.target_selector_button.move(self.width() - self.target_selector_button.width() - 10, 40)
        self.info_text.show()
