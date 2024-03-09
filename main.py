import os

from PyQt6.QtCore import QTimer
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

from Modules.RoomSceneModules.RoomSceneHost import RoomSceneHost
from Modules.SystemControlModules.SystemControlHost import SystemControlHost


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

        self.scene_control = RoomSceneHost(self)
        self.scene_control.move(0, 90)

        self.system_control = SystemControlHost(self)
        self.system_control.move(0, 90)

        self.menu_bar = MenuBar(self)
        # Move the menu bar to the very bottom of the window
        self.menu_bar.move(0, self.height() - self.menu_bar.height())

        self.refocus_timer = QTimer(self)
        self.refocus_timer.timeout.connect(self.refocus_timer_timeout)

        self.show()
        # If running on a linux system, use this to make the window full screen
        if os.name == "posix":
            self.showFullScreen()

    def refocus_timer_timeout(self):
        self.focus_room_control(force_close=True)
        self.focus_scene_control(force_close=True)
        self.focus_system_control(force_close=True)
        self.refocus_timer.stop()

    def mousePressEvent(self, a0) -> None:
        self.refocus_timer.start(15000)  # Reset the refocus timer to 15 seconds
        super().mousePressEvent(a0)

    def focus_room_control(self, force_close=False):
        if self.room_control.focused or force_close:
            self.room_control.move(0, self.forecast.height() + self.forecast.y() + 10)
            self.room_control.set_focus(False)
            self.menu_bar.room_control_expand.setText("↑Room Control↑")
            self.forecast.show()
            self.refocus_timer.stop()
        else:
            self.room_control.move(0, 90)
            self.room_control.set_focus(True)
            self.menu_bar.room_control_expand.setText("↓Room Control↓")
            self.refocus_timer.start(30000)  # 15 seconds
            self.forecast.hide()

    def focus_system_control(self, force_close=False):
        try:
            if self.system_control.focused or force_close:
                self.system_control.set_focus(False)
                self.system_control.hide()
                self.menu_bar.system_control_expand.setText("↑System Control↑")
                self.forecast.show()
                self.refocus_timer.stop()
            else:
                self.system_control.set_focus(True)
                self.system_control.show()
                self.menu_bar.system_control_expand.setText("↓System Control↓")
                self.system_control.setFixedSize(self.width(), self.room_control.y() - 90)
                self.refocus_timer.start(30000)  # 15 seconds
                self.forecast.hide()
        except Exception as e:
            logging.exception(e)

    def focus_scene_control(self, force_close=False):
        if self.scene_control.focused or force_close:
            self.scene_control.set_focus(False)
            self.scene_control.hide()
            self.menu_bar.scenes_expand.setText("↑Scene Control↑")
            self.forecast.show()
            self.refocus_timer.stop()
        else:
            self.scene_control.set_focus(True)
            self.scene_control.show()
            # The scene controls max height is the distance from 90 pixels to the top of room control
            self.scene_control.setFixedSize(self.width(), self.room_control.y() - 90)
            self.menu_bar.scenes_expand.setText("↓Scene Control↓")
            self.forecast.hide()
            self.refocus_timer.start(30000)  # 15 seconds

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
