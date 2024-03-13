from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton, QDialog
from loguru import logger as logging


class SceneEditorFlyout(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.parent = parent
        self.starting_data = data
        self.font = self.parent.font

        # This is a flyout (popup) that will be used to edit a scene
        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")
        self.setFixedSize(800, 500)
        self.setWindowTitle(f"Scene Editor: {data['scene_name']}")

