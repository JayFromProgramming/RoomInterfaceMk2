from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QPushButton, QDialog
from loguru import logger as logging

from Modules.RoomSceneModules.SceneEditor.TriggerEditDialog import TriggerEditDialog


class TriggerTile(QLabel):

    def __init__(self, parent, trigger_type, data=None):
        super().__init__(parent)
        self.parent = parent
        self.font = parent.font
        self.trigger_type = trigger_type

        self.setFixedSize(192, 60)

        self.setStyleSheet("background-color: #ffcd00; border: 2px solid #ffcd00; border-radius: 10px")

        self.trigger_name = QLabel(self)
        self.trigger_name.setFont(self.font)
        self.trigger_name.setFixedSize(self.width(), 20)
        self.trigger_name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.trigger_name.setStyleSheet("color: black; font-size: 14px; font-weight: bold; border: none;"
                                        "background-color: transparent")
        self.trigger_name.setText(f"{trigger_type}")
        self.trigger_name.move(5, 0)

        if data is None:
            self.trigger_data = {
                "trigger_id": "0",  # "0" is a placeholder for "new trigger"
                "trigger_type": trigger_type,
                "trigger_subtype": None,
                "trigger_value": None,
                "enabled": -1
            }
        else:
            self.trigger_data = data

        self.trigger_data_label = QLabel(self)
        self.trigger_data_label.setFont(self.font)
        self.trigger_data_label.setFixedSize(self.width(), 300)
        self.trigger_data_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.trigger_data_label.setStyleSheet("color: black; font-size: 12px; font-weight: bold; border: none; "
                                              "background-color: transparent")
        self.trigger_data_label.setText(f"Val: {self.trigger_data['trigger_subtype']}\n"
                                        f"Arg: {self.trigger_data['trigger_value']}")
        self.trigger_data_label.move(5, 20)

        self.trigger_enable = QPushButton(self)
        self.trigger_enable.setFixedSize(60, 30)
        if self.trigger_data["enabled"] == 1:
            self.trigger_enable.setText("Disable")
            self.trigger_enable.setStyleSheet("background-color: green; border: 2px solid #ffcd00;"
                                              " border-radius: 10px")
        elif self.trigger_data["enabled"] == 0:
            self.trigger_enable.setText("Enable")
            self.trigger_enable.setStyleSheet("background-color: grey; border: 2px solid #ffcd00;"
                                              " border-radius: 10px")
        elif self.trigger_data["enabled"] == -1:
            self.trigger_enable.setText("Add")
            self.trigger_enable.setStyleSheet("background-color: grey; border: 2px solid #ffcd00;"
                                              " border-radius: 10px")
        else:
            self.trigger_enable.setText("IDFK")
            self.trigger_enable.setStyleSheet("background-color: red; border: 2px solid #ffcd00;"
                                              " border-radius: 10px")
        self.trigger_enable.setFont(self.font)
        self.trigger_enable.move(self.width() - self.trigger_enable.width() - 5,
                                 self.height() - self.trigger_enable.height() - 5)
        self.trigger_enable.clicked.connect(self.toggle_trigger)

    def toggle_trigger(self):
        if self.trigger_data["enabled"] == 1:
            self.trigger_data["enabled"] = 0
            self.trigger_enable.setText("Enable")
            self.trigger_enable.setStyleSheet("background-color: grey; border: 2px solid #ffcd00;"
                                              " border-radius: 10px")
        elif self.trigger_data["enabled"] == 0:
            self.trigger_data["enabled"] = 1
            self.trigger_enable.setText("Disable")
            self.trigger_enable.setStyleSheet("background-color: green; border: 2px solid #ffcd00;"
                                              " border-radius: 10px")
        elif self.trigger_data["enabled"] == -1:
            self.trigger_data["enabled"] = 1
            self.parent.transfer_trigger(self)
            self.trigger_data["enabled"] = -1

    def mouseReleaseEvent(self, ev) -> None:
        try:
            if self.trigger_data["enabled"] == -1:
                return
            # Open a 2 text input dialog to edit the trigger subtype and value
            modal = TriggerEditDialog(self.trigger_data['trigger_subtype'], self.trigger_data['trigger_value'])
            result = modal.exec()
            if result == QDialog.DialogCode.Accepted:
                self.trigger_data['trigger_subtype'] = modal.subtype
                self.trigger_data['trigger_value'] = modal.value
                self.trigger_data_label.setText(f"Val: {self.trigger_data['trigger_subtype']}\n"
                                                f"Arg: {self.trigger_data['trigger_value']}")
            elif result == QDialog.DialogCode.Rejected:
                logging.info("Trigger edit dialog was rejected")
            elif result == 2:
                self.parent.remove_trigger(self, True)
            else:
                logging.error(f"Trigger edit dialog returned an unexpected value: {modal.exec()}")
        except Exception as e:
            logging.error(f"Error editing trigger: {e}")
            logging.exception(e)

    def resizeEvent(self, a0) -> None:
        self.trigger_name.setFixedSize(self.width(), 20)
        self.trigger_data_label.setFixedSize(self.width(), 300)
        super().resizeEvent(a0)
