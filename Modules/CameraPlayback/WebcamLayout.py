import json
import os

from PyQt6.QtWidgets import QLabel
from loguru import logger as logging

try:
    from Modules.CameraPlayback.WebcamWindow import WebcamWindow
except ImportError:
    logging.error("Failed to import WebcamWindow")
    WebcamWindow = None


class WebcamLayout(QLabel):
    min_cam_width = 400
    target_layout = (4, 3)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.focused = False

        self.webcams = []
        if not os.path.exists("Config/webcams.json"):
            with open("Config/webcams.json", "w") as f:
                json.dump([], f)
                logging.warning("Please fill out the webcams.json file with the proper information")
        with open("Config/webcams.json", "r") as f:
            self.webcam_file = json.load(f)

        self.hide()

    def set_focus(self, focus) -> None:
        self.focused = focus
        if focus:
            self.create_layout()
            self.show()
        else:
            self.clear_layout()
            self.hide()

    def create_layout(self):
        # self.clear_layout()
        self.webcams = []
        if WebcamWindow is None:
            return
        for i, webcam in enumerate(self.webcam_file):
            if "thumb" not in webcam:
                webcam["thumb"] = None
            webcam_window = WebcamWindow(self, webcam["url"], webcam["thumb"],
                                         webcam["title"], (self.width() / self.target_layout[0],
                                                           self.height() / self.target_layout[1]))
            webcam_window.move((i % self.target_layout[0]) * webcam_window.width(),
                               (i // self.target_layout[0]) * webcam_window.height())
            self.webcams.append(webcam_window)

    def update_layout(self):
        # Check if the webcam
        for i, webcam in enumerate(self.webcams):
            webcam.setFixedSize(round(self.width() / self.target_layout[0]),
                                round(self.height() / self.target_layout[1]))
            webcam.resizeEvent(None)
            webcam.move((i % self.target_layout[0]) * webcam.width(), (i // self.target_layout[0]) * webcam.height())

    def clear_layout(self):
        for webcam in self.webcams:
            webcam.hide()
            webcam.deleteLater()
        # self.webcams = []

    def resizeEvent(self, a0):
        self.update_layout()

    # def hideEvent(self, a0):
    #     self.clear_layout()
    #
    # def showEvent(self, a0):
    #     self.update_layout()
