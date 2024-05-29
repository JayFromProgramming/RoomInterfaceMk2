import copy
import json

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging

from Modules.RoomSceneModules.SceneEditor.TriggerTile import TriggerTile
from Utils.ScrollableMenu import ScrollableMenu


class TriggerColumn(ScrollableMenu):

    def __init__(self, parent, name):
        super().__init__(parent, parent.font)
        self.parent = parent
        self.auth = parent.auth
        self.host = parent.host
        self.font = parent.font

        # self.setFixedSize(400, 375)

        self.setStyleSheet("background-color: transparent; border: 2px solid #ffcd00; border-radius: 10px")

        self.column_name = QLabel(self)
        self.column_name.setFont(self.font)
        self.column_name.setFixedSize(400, 20)
        self.column_name.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.column_name.setStyleSheet("color: #ffcd00; font-size: 16px; font-weight: bold; border: none;")
        self.column_name.setText(f"{name}")

        self.place_holder_text = QLabel(self)
        self.place_holder_text.setFont(self.font)
        self.place_holder_text.setFixedSize(400, 20)
        self.place_holder_text.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.place_holder_text.setStyleSheet("color: #ffcd00; font-size: 16px; font-weight: bold; border: none;")
        self.place_holder_text.setText(f"No Automated Triggers Configured\nFor This Scene")
        # Center the place holder text to the middle both horizontally and vertically
        self.place_holder_text.move(round(self.width() / 2 - self.place_holder_text.width() / 2),
                                    round(self.height() / 2 - self.place_holder_text.height() / 2))

        self.trigger_labels = []
        self.default_trigger_network_manager = QNetworkAccessManager()
        self.default_trigger_network_manager.finished.connect(self.handle_default_trigger_response)

        self.layout_widgets()

    def load_default_triggers(self):
        request = QNetworkRequest(QUrl(f"http://{self.host}/scene_get/default_triggers/null"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        self.default_trigger_network_manager.get(request)

    def handle_default_trigger_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Error: {reply.error()}")
                return
            data = reply.readAll()
            data = data.data().decode("utf-8")
            data = json.loads(data)
            for trigger in data["result"]:
                self.add_trigger(trigger["trigger_type"], trigger)
        except Exception as e:
            logging.error(f"Error handling default trigger response: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def add_trigger(self, trigger_type, data=None):
        try:
            trigger = TriggerTile(self, copy.deepcopy(trigger_type),
                                    copy.deepcopy(data) if data is not None else None)
            self.trigger_labels.append(trigger)
            self.layout_widgets()
        except Exception as e:
            logging.error(f"Error adding trigger: {e}")
            logging.exception(e)

    def transfer_trigger(self, trigger):
        self.parent.transfer_trigger(trigger)

    def remove_trigger(self, trigger, without_replacement=False):
        self.trigger_labels.remove(trigger)
        if without_replacement:
            trigger.deleteLater()
        self.layout_widgets()

    def move_widgets(self, y):
        pass

    def layout_widgets(self):
        try:
            self.place_holder_text.move(round(self.width() / 2 - self.place_holder_text.width() / 2),
                                        round(self.height() / 2 - self.place_holder_text.height() / 2))
            if len(self.trigger_labels) == 0:
                self.place_holder_text.show()
            else:
                self.place_holder_text.hide()
            x = 5
            y = 20
            # Layout one row and then move to the next when the row is full
            for trigger in self.trigger_labels:
                trigger.move(x, y)
                trigger.show()
                x += trigger.width() + 5
                if x + trigger.width() > self.width():
                    x = 5
                    y += trigger.height() + 5
        except Exception as e:
            logging.error(f"Error laying out trigger labels: {e}")
            logging.exception(e)
