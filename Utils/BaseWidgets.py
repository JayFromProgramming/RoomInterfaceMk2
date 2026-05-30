from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton


class StandardButton(QPushButton):

    def __init__(self, parent=None, text="", width=95, height=30, callback=None,
                 style="color: black; font-size: 14px; font-weight: bold; background-color: grey"):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setStyleSheet(style)
        self.setText(text)
        if callback is not None:
            self.clicked.connect(callback)
        self.setFont(parent.font)


class TargetSelector(QWidget):

    @staticmethod
    def float_format(value):
        # Round the value to 2 decimal places and make sure there are 2 characters before and after the decimal point
        # e.g 01.23, 12.34, 23.40, 112.00
        return f"{value:.2f}".zfill(5)

    def __init__(self, parent=None, label="",
                 initial_value=0, step=1, unit="°F", min_value=None, max_value=None):
        super().__init__(parent)
        self.setFixedSize(120, 50)
        self.min_value = min_value if min_value is not None else -99.99
        self.max_value = max_value if max_value is not None else 999.99
        self.setStyleSheet("color: black; font-size: 19px; font-weight: bold; background-color: grey;"
                           "border: none; border-radius: none;")
        self.unit = unit
        self.spin_box = QLabel(self)
        self.spin_box.setFixedSize(80, 50)
        self.spin_box.setStyleSheet("color: black; font-size: 19px; font-weight: bold; background-color: grey;"
                                    "border: none; border-radius: none;")
        self.spin_value = initial_value
        self.spin_step = step
        self.spin_box.setText(str(self.spin_value) + self.unit)
        # Move the spin box to left center
        self.spin_box.move(0, 0 if label == "" else 7)
        self.spin_box.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.label = QLabel(self)
        self.label.setFixedSize(80, 20)
        self.label.setStyleSheet("color: black; font-size: 12px; font-weight: bold; background-color: grey;")
        self.label.setText(label)
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.label.move(0, 0)

        self.increase_button = QPushButton(self)
        self.increase_button.setFixedSize(35, 25)
        self.increase_button.setStyleSheet("color: black; font-size: 16px; font-weight: bold; background-color: grey;"
                                           "border: black; border-radius: 0px; border-width: 1px;")
        self.increase_button.setText("▲")
        self.increase_button.move(self.spin_box.width(), 0)
        self.increase_button.clicked.connect(self.increase_value)

        self.decrease_button = QPushButton(self)
        self.decrease_button.setFixedSize(35, 25)
        self.decrease_button.setStyleSheet("color: black; font-size: 16px; font-weight: bold; background-color: grey;"
                                           "border: black; border-radius: 0px; border-width: 1px;")
        self.decrease_button.setText("▼")
        self.decrease_button.move(self.increase_button.x(),
                                  self.increase_button.y() + self.increase_button.height())
        self.decrease_button.clicked.connect(self.decrease_value)

    def increase_value(self):
        self.spin_value += self.spin_step
        if self.spin_value > self.max_value:
            self.spin_value = self.max_value
        if self.spin_value < self.min_value:
            self.spin_value = self.min_value
        self.spin_box.setText(f"{self.float_format(self.spin_value)}{self.unit}")

    def decrease_value(self):
        self.spin_value -= self.spin_step
        if self.spin_value > self.max_value:
            self.spin_value = self.max_value
        if self.spin_value < self.min_value:
            self.spin_value = self.min_value
        self.spin_box.setText(f"{self.float_format(self.spin_value)}{self.unit}")

    @property
    def value(self):
        return self.spin_value

    @value.setter
    def value(self, new_value):
        self.spin_value = new_value
        self.spin_box.setText(f"{self.float_format(self.spin_value)}{self.unit}")