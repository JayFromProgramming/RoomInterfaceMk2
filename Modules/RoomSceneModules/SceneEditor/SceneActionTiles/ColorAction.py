from PyQt6.QtWidgets import QSpinBox, QLabel

from Modules.RoomSceneModules.SceneEditor.SceneActionTiles.BaseAction import BaseAction


class ColorAction(BaseAction):

    supported_action = [("color", "Color", [0, 0, 0])]

    def create_action_input(self):
        self.action_input_object = QLabel(self)
        self.action_input_object.setFixedSize(150, 20)
        for i in range(3):
            color_box = QSpinBox(self.action_input_object)
            color_box.setRange(0, 255)
            color_box.setSingleStep(5)
            color_box.setValue(self.payload[i])
            color_box.move(i * 50, 0)
            color_box.show()
        self.action_label.setText("Set color:")
        self.action_input_object.move(self.width() - self.action_input_object.width() - 5, 5)
