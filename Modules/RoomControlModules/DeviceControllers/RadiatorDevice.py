from Modules.RoomControlModules.DeviceControllers.ToggleDevice import ToggleDevice
from Utils.RoomDevice import RoomDevice
from PyQt6.QtCore import QTimer


class RadiatorDevice(ToggleDevice, RoomDevice):
    supported_types = ["satellite_Radiator"]

    def __init__(self, parent=None, device=None, priority=0):
        super().__init__(parent, device, priority)
        self.spinner_phase = 0
        self.text_update_timer = QTimer()
        self.text_update_timer.timeout.connect(self.update_status)
        # self.text_update_timer.start(500)
        self.text_update_timer.setSingleShot(True)

    def spinner(self):
        """
        Use the unicode braille characters to create a spinning animation
        :return:
        """
        animation_list = ['⡇', '⠏', '⠛', '⠹', '⢸', '⣰', '⣤', '⣆']
        self.spinner_phase = (self.spinner_phase + 1) % len(animation_list)
        return animation_list[self.spinner_phase]

    def update_status(self):
        health = self.data["health"]
        if not health["online"]:
            self.device_text.setText(f"<pre>DEVICE OFFLINE</pre>")
            self.toggle_button.setStyleSheet("color: black; font-size: 14px; font-weight: bold; background-color: red;")
        elif health["fault"]:
            self.device_text.setText(f"<pre>FAULT: {self.state['radiator_temp']:.02f}°F</pre>")
            self.toggle_button.setStyleSheet(
                "color: black; font-size: 14px; font-weight: bold; background-color: orange;")
        else:
            if self.state['state'] in ['IDLE', ]:
                self.device_text.setText(f"<pre>IDLE: {self.state['radiator_temp']:.02f}°F</pre>")
            elif self.state['state'] in ['OPENING VALVE']:
                if self.state['radiator_temp'] is not None:
                    self.device_text.setText(f"<pre>START{self.spinner()}: {self.state['radiator_temp']:.02f}°F</pre>")
                else:
                    self.device_text.setText(f"<pre>START{self.spinner()}: N/A°F</pre>")
                self.text_update_timer.start(250)
            elif self.state['state'] in ['CLOSING VALVE']:
                if self.state['radiator_temp'] is not None:
                    self.device_text.setText(f"<pre>STOP{self.spinner()}: {self.state['radiator_temp']:.02f}°F</pre>")
                else:
                    self.device_text.setText(f"<pre>STOP{self.spinner()}: N/A°F</pre>")
                self.text_update_timer.start(250)
            elif self.state['state'] in ['ACTIVE', 'WARMUP', 'COOLDOWN']:
                if self.state['radiator_temp'] is not None:
                    self.device_text.setText(f"<pre>{self.state['state']} {self.state['radiator_temp']:.02f}°F</pre>")
                else:
                    self.device_text.setText(f"<pre>{self.state['state']} N/A°F</pre>")
            else:
                self.device_text.setText(f"<pre>{self.state['state']}</pre>")
                self.toggle_button.setStyleSheet(
                    "color: black; font-size: 14px; font-weight: bold; background-color: orange;")
