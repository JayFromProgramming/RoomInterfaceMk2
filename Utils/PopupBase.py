from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton

from Utils.PopupManager import PopupManager
from loguru import logger as logging


class PopupContainer(QLabel):

    def __init__(self, title, size, content):
        self.popup_manager = PopupManager.instance()
        super().__init__(self.popup_manager)

        self.header_bar = QLabel(self)
        self.header_bar.setFixedSize(size[0], 30)
        self.header_bar.move(5, 0)
        self.header_bar.setStyleSheet("background-color: black; border: none; border-top-left-radius: 10px;"
                                      "border-top-right-radius: 10px; border-bottom: 2px solid #ffcd00;"
                                      " boarder-bottom-left-radius: 0px; boarder-bottom-right-radius: 0px")
        self.setStyleSheet("background-color: black; border: none; bottom-left-radius: 10px; bottom-right-radius: 10px")

        self.title = QLabel(self.header_bar)
        self.title.setText(title)
        self.title.setFixedSize(size[0] - 30, 30)
        self.title.move(0, 0)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;"
                                 " background-color: transparent")

        self.close_button = QPushButton(self.header_bar)
        self.close_button.setText("X")
        self.close_button.setFixedSize(30, 30)
        self.close_button.move(size[0] - 30, 0)
        self.close_button.clicked.connect(lambda: self.popup_manager.remove_popup(self))
        self.close_button.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;"
                                        " background-color: red; border-top-right-radius: 10px; top-left-radius: 0px;"
                                        " border-bottom-right-radius: 0px; border-bottom-left-radius: 0px")

        self.setFixedSize(size[0] + 10, size[1] + 35)
        # self.setStyleSheet(

        self.content_panel = content
        self.content_panel.setParent(self)

        self.content_panel.move(5, 30)
        self.content_panel.raise_()

    def finish_render(self):
        self.popup_manager.add_popup(self)


class PopupBase(QLabel):

    def __init__(self, title, size):
        super().__init__()
        self.setFixedSize(size[0], size[1])
        self.container = PopupContainer(title, size, self)

    def finish_render(self):
        self.container.finish_render()

