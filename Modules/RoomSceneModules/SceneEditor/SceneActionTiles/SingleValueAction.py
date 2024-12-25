from PyQt6.QtWidgets import QSpinBox

from Modules.RoomSceneModules.SceneEditor.SceneActionTiles.BaseAction import BaseAction


class SingleValueAction(BaseAction):

    supported_action = [("brightness", "Brightness", 0), ("target_value", "Target Value", 0)]

    def create_action_input(self):
        match self.act:
            case "brightness":
                self.action_input_object = QSpinBox(self)
                self.action_input_object.setRange(0, 255)
                self.action_input_object.setValue(self.payload)
                self.action_input_object.setSingleStep(5)
                self.action_input_object.setFixedSize(50, 20)
                self.action_input_object.setStyleSheet("border: 1px solid black")
                self.action_label.setText("Set brightness:")
            case "target_value":
                self.action_input_object = QSpinBox(self)
                self.action_input_object.setRange(0, 100)
                self.action_input_object.setValue(self.payload)
                self.action_input_object.setFixedSize(50, 20)
                self.action_input_object.setSingleStep(0.5)
                self.action_input_object.setStyleSheet("border: 1px solid black")
                self.action_label.setText("Set target:")
            case _:
                raise ValueError(f"Unsupported action type {self.act}")

