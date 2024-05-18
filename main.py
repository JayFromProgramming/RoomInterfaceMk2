import os
import sys
import time
import threading

from PyQt6.QtCore import QTimer, QElapsedTimer, QEvent
from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton, QDialog, QLabel, QVBoxLayout
from PyQt6.QtGui import QFont, QFontDatabase

from Modules.CameraPlayback.WebcamLayout import WebcamLayout

# Replace this with auto-import later
from Modules.DisplayClock import DisplayClock
from Modules.CurrentWeather import CurrentWeather
from Modules.Forecast.ForecastHost import ForecastHost
from Modules.MenuBar import MenuBar
from Modules.RadarDisplay.RadarHost import RadarHost

from Modules.RoomControlModules.RoomControlHost import RoomControlHost

import traceback

from loguru import logger as logging

from Modules.RoomSceneModules.RoomSceneHost import RoomSceneHost
from Modules.SystemControlModules.SystemControlHost import SystemControlHost


class RoomInterface(QApplication):
    t = QElapsedTimer()

    def __init__(self):
        super().__init__([])
        try:
            logging.add("Logs/RoomInterface.log", rotation="1 week")
        except Exception as e:
            print(f"Failed to setup logging: {e}")
        logging.info("RoomInterface started")
        self.window = MainWindow()
        self.window.show()
        # self.watchdog = WatchdogThread(timeout=10, fail_callback=self.watchdog_failed)
        self.feed_timer = QTimer()
        # self.feed_timer.timeout.connect(self.feed_watchdog)
        # self.feed_timer.start(1000)
        # self.watchdog.start()
        self.exec()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.cached_fonts = {}

        self.setWindowTitle("RoomInterfaceMk2")
        self.setGeometry(100, 100, 1024, 600)
        # Set the background color to black
        self.setStyleSheet("background-color: black;")

        self.clock = DisplayClock(self)
        # Move the clock to the upper right corner (dynamic, so it will always be in the upper right corner)
        self.clock.move(self.width() - self.clock.width(), 0)

        # Setup all main modules of the interface
        self.weather = CurrentWeather(self)
        self.weather.move(0, 0)

        self.forecast = ForecastHost(self)
        self.forecast.move(0, 90)

        self.room_control = RoomControlHost(self)
        self.room_control.move(0, self.forecast.height() + self.forecast.y() + 10)

        self.scene_control = RoomSceneHost(self)
        self.scene_control.move(0, 90)

        self.system_control = SystemControlHost(self)
        self.system_control.move(0, 90)

        self.webcam_layout = WebcamLayout(self)
        self.webcam_layout.move(0, 90)

        self.radar_host = RadarHost(self)
        self.radar_host.move(0, 90)
        self.radar_host.hide()

        self.menu_bar = MenuBar(self)
        # Move the menu bar to the very bottom of the window
        self.menu_bar.move(0, self.height() - self.menu_bar.height())

        # Add the menu bar buttons and link them to the appropriate modules
        self.menu_bar.add_flyout_button("System Control", self.system_control, 60)
        self.menu_bar.add_flyout_button("Scene Control", self.scene_control)
        self.menu_bar.add_flyout_button("Room Control", self.room_control, 60)
        self.menu_bar.add_flyout_button("Webcams", self.webcam_layout, 60)
        self.menu_bar.add_flyout_button("Radar", self.radar_host, 75)
        self.system_control.setFixedSize(self.width(), self.room_control.y() - 90)
        self.scene_control.setFixedSize(self.width(), self.room_control.y() - 90)

        self.room_control.set_activity_timer_callback(self.menu_bar.reset_focus_timer)
        self.radar_host.set_activity_timer_callback(self.menu_bar.reset_focus_timer)

        self.show()
        # If running on a linux system, use this to make the window full screen
        if os.name == "posix":
            self.showFullScreen()

    def mousePressEvent(self, a0) -> None:
        self.menu_bar.reset_focus_timer()
        super().mousePressEvent(a0)

    def wheelEvent(self, a0) -> None:
        self.menu_bar.reset_focus_timer()
        super().wheelEvent(a0)

    def get_font(self, name: str):
        # Load the custom font from a file
        if name in self.cached_fonts:
            return self.cached_fonts[name]
        font_id = QFontDatabase.addApplicationFont(f"Assets/Fonts/Jetbrains/{name}.ttf")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                self.cached_fonts[name] = QFont(font_families[0])
                return QFont(font_families[0])
            else:
                print(f"Failed to load the font family: {name}.ttf")
                return QFont()
        else:
            print(f"Failed to load the font: {name}.ttf")
            return QFont()

    def keyReleaseEvent(self, a0) -> None:
        try:
            # On 'R' key press, refresh all data from the server
            if a0.key() == 82:
                self.room_control.reload_schema()
                self.forecast.refresh_forecast()
            super().keyReleaseEvent(a0)
        except Exception as e:
            logging.exception(e)

    def resizeEvent(self, event):
        try:
            self.menu_bar.setFixedSize(self.width(), self.menu_bar.height())
            self.menu_bar.move(0, self.height() - self.menu_bar.height())
            self.clock.move(self.width() - self.clock.width(), 0)
            self.webcam_layout.setFixedSize(self.width(), self.height() - 90 - self.menu_bar.height())
            self.webcam_layout.resizeEvent(event)
            self.forecast.setFixedSize(self.width(), self.forecast.height())
            self.forecast.layout_widgets()
            self.room_control.resizeEvent(event)
            self.scene_control.resizeEvent(event)
        except Exception as e:
            logging.exception(e)


if __name__ == "__main__":
    app = RoomInterface()
    app.exec()
