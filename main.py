import os

from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton
from PyQt6.QtGui import QFont, QFontDatabase

# Replace this with auto-import later
from Modules.DisplayClock import DisplayClock
from Modules.CurrentWeather import CurrentWeather
from Modules.Forecast.ForecastHost import ForecastHost
from Modules.MenuBar import MenuBar

from Modules.RoomControlModules.RoomControlHost import RoomControlHost

# from Modules.SystemStatus import SystemStatus

from loguru import logger as logging


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RoomInterfaceMk2")
        self.setGeometry(100, 100, 1024, 600)
        # Set the background color to black
        self.setStyleSheet("background-color: black;")

        self.clock = DisplayClock(self)
        # Move the clock to the upper right corner (dynamic, so it will always be in the upper right corner)
        self.clock.move(self.width() - self.clock.width(), 0)

        self.weather = CurrentWeather(self)
        self.weather.move(0, 0)

        self.forecast = ForecastHost(self)
        self.forecast.move(0, 90)
        # self.forecast.hide()

        self.room_control = RoomControlHost(self)
        self.room_control.move(0, self.forecast.height() + self.forecast.y() + 10)

        # self.system_status = SystemStatus(self)
        # # Put the system status dead center (it gets to choose if it's shown or not)
        # self.system_status.move(round((self.width() - self.system_status.width()) / 2),
        #                         round((self.height() - self.system_status.height()) / 2))

        self.menu_bar = MenuBar(self)
        # Move the menu bar to the very bottom of the window
        self.menu_bar.move(0, self.height() - self.menu_bar.height())

        self.show()
        # If running on a linux system, use this to make the window full screen
        if os.name == "posix":
            self.showFullScreen()

    def focus_room_control(self):
        if not self.room_control.focused:
            self.room_control.move(0, 90)
            self.room_control.set_focus(True)
            self.menu_bar.room_control_expand.setText("↓Room Control↓")
            self.forecast.hide()
        else:
            self.room_control.move(0, self.forecast.height() + self.forecast.y() + 10)
            self.room_control.set_focus(False)
            self.menu_bar.room_control_expand.setText("↑Room Control↑")
            self.forecast.show()

    def get_font(self, name: str):
        # Load the custom font from a file
        font_id = QFontDatabase.addApplicationFont(f"Assets/Fonts/Jetbrains/{name}.ttf")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                return QFont(font_families[0])
            else:
                print(f"Failed to load the font family: {name}.ttf")
                return QFont()
        else:
            print(f"Failed to load the font: {name}.ttf")
            return QFont()

    def resizeEvent(self, event):
        try:
            self.menu_bar.setFixedSize(self.width(), self.menu_bar.height())
            self.menu_bar.move(0, self.height() - self.menu_bar.height())
            self.clock.move(self.width() - self.clock.width(), 0)
            self.forecast.setFixedSize(self.width(), self.forecast.height())
            self.forecast.layout_widgets()
            self.room_control.resizeEvent(event)
        except Exception as e:
            logging.exception(e)


app = QApplication([])
window = MainWindow()
app.exec()
