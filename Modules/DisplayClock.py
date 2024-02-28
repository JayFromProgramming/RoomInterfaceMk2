from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtWidgets import QLabel


def ordinal(n):
    return str(n) + ('th' if 4 <= n <= 20 or 24 <= n <= 30 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))


class DisplayClock(QLabel):
    """Creates a surface that contains a clock in the format HH:MM:SS AM/PM that refreshes every second"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("color: white; font-size: 75px")
        self.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Create the text for the label
        self.text_label = QLabel(self)
        self.text_label.setStyleSheet("color: #ffcd00; font-size: 55px; font-weight: bold; background-color: transparent")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.text_label.setFont(parent.get_font("JetBrainsMono-Bold"))
        self.text_label.setFixedSize(400, 60)
        self.text_label.move(0, 0)

        self.date_label = QLabel(self)
        self.date_label.setStyleSheet("color: #ffcd00; font-size: 21px; background-color: transparent")
        self.date_label.setFont(parent.get_font("JetBrainsMono-Regular"))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.date_label.setFixedSize(400, 27)
        self.date_label.move(0, self.text_label.height())

        self.setFixedSize(400, self.text_label.height() + self.date_label.height())

        self.updateTime()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)

    def updateTime(self):
        """Updates the label to the current time"""
        current_time = QDateTime.currentDateTime()
        # date_suffix = ordinal(current_time.date().day())
        self.text_label.setText(current_time.toString("hh:mm:ssAP"))
        self.date_label.setText(current_time.toString(f"dddd, MMMM d, yyyy"))

        self.repaint()
