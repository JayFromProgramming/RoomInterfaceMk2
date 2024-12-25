from PyQt6.QtWidgets import QLabel, QSpinBox

from Modules.RoomSceneModules.SceneEditor.SceneActionTiles.BaseAction import BaseAction


class FadeAction(BaseAction):

    supported_action = [("fade", "Fade", {'target': [0, 0, 0, 0], 'time': 0})]

    def create_action_input(self):

        self.action_input_object = QLabel(self)
        self.action_input_object.setFixedSize(200, 50)
        for i in range(4):
            color_box = QSpinBox(self.action_input_object)
            color_box.setRange(0, 255)
            color_box.setSingleStep(5)
            color_box.setValue(self.payload['target'][i])
            color_box.move(i * 50, 0)
            color_box.setStyleSheet('border: 1px solid black')
            color_box.show()
        time_label = QLabel(self.action_input_object)
        time_box = QSpinBox(self.action_input_object)
        time_box.setRange(0, 1000000)
        time_box.setSingleStep(5)
        time_box.setValue(self.payload['time'])
        time_box.move(0, 25)
        time_label.setText("(S)")
        time_label.move(time_box.width() + 5, 25)
        time_box.show()

        self.action_label.setText("Fade to:")
        self.action_input_object.move(self.width() - self.action_input_object.width() - 5, 5)

    def get_payload(self):
        return {
            'target': [self.action_input_object.children()[i].value() for i in range(4)],
            'time': self.action_input_object.children()[5].value()
        }