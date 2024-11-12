from Modules.RoomControlModules.DeviceControllers.ToggleDevice import ToggleDevice
from Utils.RoomDevice import RoomDevice


class RadiatorDevice(ToggleDevice, RoomDevice):

    supported_types = ["satellite_Radiator"]

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
            if self.state['state'] in ['IDLE', 'WARMUP', 'ACTIVE', 'COOLDOWN']:
                self.device_text.setText(f"<pre>Online: {self.state['state']}</pre>")
            elif self.state['state'] in ['OPENING VALVE', 'CLOSING VALVE']:
                self.device_text.setText(f"<pre>{self.state['state']}</pre>")
            else:
                self.device_text.setText(f"<pre>{self.state['state']}</pre>")
                self.toggle_button.setStyleSheet(
                    "color: black; font-size: 14px; font-weight: bold; background-color: orange;")



