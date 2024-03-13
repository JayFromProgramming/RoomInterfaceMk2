from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging

from Modules.RoomSceneModules.SceneEditor.TriggerTile import TriggerTile
from Utils.ScrollableMenu import ScrollableMenu


class TriggerColumn(ScrollableMenu):

    def __init__(self, parent):
        super().__init__(parent, parent.font)
        self.parent = parent
        self.auth = parent.auth
        self.host = parent.host
        self.font = parent.font

        self.setFixedSize(180, 400)

        self.setStyleSheet("background-color: transparent; border: 2px solid #ffcd00; border-radius: 10px")

        self.column_name = QLabel(self)
        self.column_name.setFont(self.font)
        self.column_name.setFixedSize(185, 20)
        self.column_name.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        self.column_name.setStyleSheet("color: #ffcd00; font-size: 16px; font-weight: bold; border: none;")
        self.column_name.setText("Triggers")

        self.trigger_labels = []

        self.layout_widgets()

    def add_trigger(self, name, data):
        self.trigger_labels.append(TriggerTile(self, name, data))
        self.layout_widgets()

    def move_widgets(self, y):
        pass

    def layout_widgets(self):
        y = 20
        for label in self.trigger_labels:
            label.move(5, y)
            y += label.height() + 5
            label.show()
        self.column_name.move(0, 0)
        self.show()
