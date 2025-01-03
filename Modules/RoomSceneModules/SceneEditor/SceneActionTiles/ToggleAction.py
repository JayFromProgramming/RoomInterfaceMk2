from PyQt6.QtWidgets import QComboBox

from Modules.RoomSceneModules.SceneEditor.SceneActionTiles.BaseAction import BaseAction


class ToggleAction(BaseAction):

    supported_action = [("on", "On/Off", False)]

    def create_action_input(self):
        self.setFixedSize(270, 30)
        self.action_input_object = QComboBox(self)
        self.action_input_object.addItem("On")
        self.action_input_object.addItem("Off")
        self.action_input_object.setCurrentIndex(0 if self.payload else 1)
        self.action_input_object.setFixedSize(50, 20)
        self.action_input_object.setStyleSheet("border: 1px solid black")
        self.action_label.setText("Set target:")
        self.enabled_button.move(self.width() - self.enabled_button.width(),
                                 self.height() - self.enabled_button.height())
        self.action_input_object.move(85, 5)
        self.action_input_object.show()

    def get_payload(self):
        return self.action_input_object.currentIndex() == 0
