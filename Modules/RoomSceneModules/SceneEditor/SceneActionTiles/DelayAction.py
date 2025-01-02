from PyQt6.QtWidgets import QComboBox, QSpinBox, QLabel

from Modules.RoomSceneModules.SceneEditor.SceneActionTiles.BaseAction import BaseAction


class DelayAction(BaseAction):
    supported_action = [("delay", "Delay On/Off", {"state": False, "time": 0})]

    def create_action_input(self):
        self.setFixedSize(270, 30)
        self.action_input_object = QLabel(self)
        self.action_input_object.setFixedSize(150, 30)
        delay_label = QLabel(self.action_input_object)
        delay_label.setText("in")
        delay_label.setFixedSize(20, 20)
        self.delay_spinbox = QSpinBox(self.action_input_object)
        self.delay_spinbox.setRange(0, 1000)
        self.delay_spinbox.setSingleStep(5)
        self.delay_spinbox.setValue(self.payload['time'])
        self.delay_spinbox.setFixedSize(50, 20)
        self.delay_spinbox.setStyleSheet("border: 1px solid black")

        self.toggle_box = QComboBox(self.action_input_object)
        self.toggle_box.addItem("On")
        self.toggle_box.addItem("Off")
        self.toggle_box.setCurrentIndex(0 if self.payload['state'] else 1)
        self.toggle_box.setFixedSize(50, 20)
        self.toggle_box.setStyleSheet("border: 1px solid black")
        self.toggle_box.move(0, 0)

        delay_unit = QLabel(self.action_input_object)
        delay_unit.setText("S")
        delay_unit.setFixedSize(20, 20)
        delay_label.move(self.toggle_box.x() + self.toggle_box.width() + 5, 0)
        self.delay_spinbox.move(delay_label.x() + delay_label.width(), 0)
        delay_unit.move(self.delay_spinbox.x() + self.delay_spinbox.width(), 0)
        self.action_label.setText("Set target:")
        self.enabled_button.move(self.width() - self.enabled_button.width(),
                                 self.height() - self.enabled_button.height())
        self.action_input_object.move(85, 5)
        self.action_input_object.show()

    def get_payload(self):
        return {"state": self.toggle_box.currentIndex() == 0, "time": self.delay_spinbox.value()}
