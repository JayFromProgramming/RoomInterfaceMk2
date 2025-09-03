from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging

from Modules.RoomSceneModules.SceneEditor.DeviceTile import DeviceTile
from Utils.ScrollableMenu import ScrollableMenu


class DeviceColumn(ScrollableMenu):

    sort_order = {
        "RoutineController": -1,
        "abstract_rgb": 0,
        "VoiceMonkeyDevice": 1,
        "abstract_toggle_device": 2,
        "environment_controller": 3,
        "light_controller": 4,
        "Unknown": 5,
    }

    def __init__(self, parent, column_name, starting_device_ids=None):
        super().__init__(parent, parent.font)
        self.parent = parent
        self.name = column_name
        self.host = parent.host
        self.auth = parent.auth
        self.font = self.parent.font
        self.setFixedSize(290, self.parent.height() - 40)
        self.focused = True
        self.setStyleSheet("background-color: transparent; border: 2px solid #ffcd00; border-radius: 10px;"
                           "overflow: hidden;")

        self.column_name = QLabel(self)
        self.column_name.setFont(self.font)
        self.column_name.setFixedSize(290, 20)
        self.column_name.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.column_name.setStyleSheet("color: #ffcd00; font-size: 16px; font-weight: bold; border: none;")
        if starting_device_ids is not None:
            self.column_name.setText(f"{column_name} [{len(starting_device_ids)}]")
        else:
            self.column_name.setText(f"{column_name} [?]")
        self.column_name.move(0, 2)

        self.name_manager = QNetworkAccessManager()
        self.name_manager.finished.connect(self.handle_name_response)

        self.placeholder_label = QLabel(self)
        self.placeholder_label.setFont(self.font)
        self.placeholder_label.setFixedSize(280, 100)
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.placeholder_label.setStyleSheet("color: #ffcd00; font-size: 16px; font-weight: bold; border: none;")
        self.placeholder_label.setText("Loading Devices\nFrom RoomController\nPlease Wait...")
        self.placeholder_label.move(0, 20)

        self.device_labels = []
        # logging.debug(f"Starting device ids: {starting_device_ids}")
        if starting_device_ids is not None:
            for device, action in starting_device_ids.items():
                self.device_labels.append(DeviceTile(self, device, action))
        # logging.debug(f"Device labels: {self.device_labels}")

        self.layout_widgets()

    def make_name_request(self, device):
        request = QNetworkRequest(QUrl(f"http://{self.host}/name/{device}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        self.name_manager.get(request)

    def handle_name_response(self, reply):
        try:
            # Get the original query
            original_query = reply.request().url().toString()
            # Get the device name from the query
            device = original_query.split("/")[-1]
            # Get the data from the reply
            data = reply.readAll()
            for widget in self.device_labels:
                if widget.device == device:
                    widget.update_human_name(str(data, 'utf-8'))
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def has_device(self, device):
        for label in self.device_labels:
            if label.device == device:
                return True
        return False

    def add_device(self, device, group=None):
        try:
            if isinstance(device, str):
                tile = DeviceTile(self, device, group)
            else:
                device.setParent(self)
                device.parent = self
                tile = device
            tile.show()
            self.device_labels.append(tile)
            self.column_name.setText(f"{self.name} [{len(self.device_labels)}]")
            self.layout_widgets()
        except Exception as e:
            logging.error(f"Error adding device to column: {e}")
            logging.exception(e)

    def remove_device(self, device):
        for label in self.device_labels:
            if label.device == device:
                label.hide()
                self.device_labels.remove(label)
                self.column_name.setText(f"{self.name} [{len(self.device_labels)}]")
                self.layout_widgets()
                return label
        return None

    def clicked(self, tile):
        """
        Called by a DeviceTile when it is clicked
        :param tile:
        :return:
        """
        self.parent.transfer_device(self, tile)

    def move_widgets(self, y):
        y = round(y)
        for label in self.device_labels:
            label.move(5, y)
            y += label.height() + 5
        # self.repaint()

    def layout_widgets(self):
        y = 30
        if len(self.device_labels) == 0:
            self.placeholder_label.show()
        else:
            self.placeholder_label.hide()
        # Sort widgets by their group and then by their type
        self.device_labels.sort(key=lambda x: (self.sort_order.get(x.type, 5)))
        for label in self.device_labels:
            label.move(5, y)
            y += label.height() + 5
        self.repaint()

