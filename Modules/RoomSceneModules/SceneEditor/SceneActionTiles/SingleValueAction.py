from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox

from Modules.RoomSceneModules.SceneEditor.SceneActionTiles.BaseAction import BaseAction


class SingleValueAction(BaseAction):

    supported_action = [("brightness", "Brightness", 0),
                        ("white", "White", 0),
                        ("target_value", "Target Value", 0)]

    def create_action_input(self):
        self.setFixedSize(270, 30)
        match self.act:
            case "brightness":
                self.action_input_object = QSpinBox(self)
                self.action_input_object.setRange(0, 255)
                self.action_input_object.setValue(self.payload)
                self.action_input_object.setSingleStep(5)
                self.action_input_object.setFixedSize(100, 20)
                self.action_input_object.setStyleSheet("border: 1px solid black")
                self.action_label.setText("Set brightness:")
            case "white":
                self.action_input_object = QSpinBox(self)
                self.action_input_object.setRange(0, 255)
                self.action_input_object.setValue(self.payload)
                self.action_input_object.setSingleStep(5)
                self.action_input_object.setFixedSize(100, 20)
                self.action_input_object.setStyleSheet("border: 1px solid black")
                self.action_label.setText("Set white:")
            case "target_value":
                self.action_input_object = QDoubleSpinBox(self)
                self.action_input_object.setRange(0, 100)
                self.action_input_object.setValue(self.payload)
                self.action_input_object.setFixedSize(100, 20)
                self.action_input_object.setSingleStep(0.5)
                self.action_input_object.setStyleSheet("border: 1px solid black")
                self.action_label.setText("Set target:")
            case _:
                raise ValueError(f"Unsupported action type {self.act}")

        self.enabled_button.move(self.width() - self.enabled_button.width(),
                                 self.height() - self.enabled_button.height())
        self.action_input_object.move(self.width() - self.enabled_button.width() - self.action_input_object.width() - 5, 5)
        self.action_input_object.show()

    def get_payload(self):
        return self.action_input_object.value()