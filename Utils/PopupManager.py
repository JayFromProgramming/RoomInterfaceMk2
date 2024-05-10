from PyQt6.QtWidgets import QLabel
from loguru import logger as logging

from Utils.Singleton import Singleton


@Singleton
class PopupManager(QLabel):

    def __init__(self):
        super().__init__()
        self.popups = []
        self.parent = None
        self.setStyleSheet("background-color: transparent; border: none;")

    def add_parent(self, parent):
        self.parent = parent
        self.setParent(parent)

    def add_popup(self, popup):
        logging.debug(f"Adding popup {popup}")
        self.popups.append(popup)
        if len(self.popups) > 1:
            return
        self.show_popup(popup)

    def show_popup(self, popup):
        popup.setParent(self)
        # Set the managers size to the size of the popup
        self.setFixedSize(popup.size())
        # Center the manager
        self.move(round((self.parent.width() - self.width()) / 2),
                  round((self.parent.height() - self.height()) / 2))
        popup.show()
        self.show()

    def remove_popup(self, popup):
        self.popups.remove(popup)
        if len(self.popups) > 0:
            self.show_popup(self.popups[0])
        else:
            self.hide()

    def hide_all(self):
        for popup in self.popups:
            popup.hide()
