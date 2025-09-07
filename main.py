import gc
import os
import sys

import psutil
from PyQt6.QtCore import QTimer, QElapsedTimer
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtGui import QFont, QFontDatabase

from Modules.CameraPlayback.WebcamLayout import WebcamLayout

# Replace this with auto-import later
from Modules.DisplayClock import DisplayClock
from Modules.CurrentWeather import CurrentWeather
from Modules.Forecast.ForecastHost import ForecastHost
from Modules.MenuBar import MenuBar
from Modules.RadarDisplay.RadarHost import RadarHost

from Modules.RoomControlModules.RoomControlHost import RoomControlHost

from loguru import logger as logging

from Modules.RoomSceneModules.RoomSceneHost import RoomSceneHost
from Modules.SystemControlModules.SystemControlHost import SystemControlHost
from Utils.UtilMethods import toggle_dev_server, is_using_dev_server


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
        self.weather = CurrentWeather(self)
        self.forecast = ForecastHost(self)
        self.room_control = RoomControlHost(self)
        self.scene_control = RoomSceneHost(self)
        self.system_control = SystemControlHost(self)
        self.webcam_layout = WebcamLayout(self)
        self.radar_host = RadarHost(self)
        self.menu_bar = MenuBar(self)

        # Move the clock to the upper right corner (dynamic, so it will always be in the upper right corner)
        self.clock.move(self.width() - self.clock.width(), 0)
        self.weather.move(0, 0)
        self.forecast.move(0, 90)  # These moves have fixed upper left corners, so they don't need to be dynamic
        self.room_control.move(0, self.forecast.height() + self.forecast.y() + 10)
        self.scene_control.move(0, 90)
        self.system_control.move(0, 90)
        self.webcam_layout.move(0, 90)
        self.radar_host.move(0, 90)
        self.radar_host.hide()

        # Move the menu bar to the very bottom of the window
        self.menu_bar.move(0, self.height() - self.menu_bar.height())

        # Add the menu bar buttons and link them to the appropriate modules
        self.menu_bar.add_flyout_button("System Control", self.system_control, 120)
        self.menu_bar.add_flyout_button("Routines", self.scene_control, 120)
        self.menu_bar.add_flyout_button("Room Control", self.room_control, 90)
        self.menu_bar.add_flyout_button("Webcams", self.webcam_layout, 120)
        self.menu_bar.add_flyout_button("Radar", self.radar_host, 75)
        self.system_control.setFixedSize(self.width(), self.room_control.y() - 90)
        self.scene_control.setFixedSize(self.width(), self.room_control.y() - 90)

        # Allow modules to reset the focus timer on user interaction
        self.room_control.set_activity_timer_callback(self.menu_bar.reset_focus_timer)
        self.radar_host.set_activity_timer_callback(self.menu_bar.reset_focus_timer)

        # Setup debug text timer, so I can see the current CPU and memory usage (validate no memory leaks)
        self.window_title_update_timer = QTimer()
        self.window_title_update_timer.timeout.connect(self.update_window_title)

        self.process = psutil.Process(os.getpid())

        self.show()
        # If running on a linux system, use this to make the window full screen
        if os.name == "posix":  # If you want to run this windowed on linux, pound sand
            self.showFullScreen()
        else:
            self.window_title_update_timer.start(500)

    def mousePressEvent(self, a0) -> None:
        self.menu_bar.reset_focus_timer()
        super().mousePressEvent(a0)

    def wheelEvent(self, a0) -> None:
        self.menu_bar.reset_focus_timer()
        super().wheelEvent(a0)

    def update_window_title(self):
        try:
            cpu_percent = self.process.cpu_percent() / psutil.cpu_count()
            cpu_percent = f"{cpu_percent:.2f}".rjust(5, " ")
            memory_usage = self.process.memory_info().rss
            using_dev_server = " - Alternate Server" if is_using_dev_server() else ""
            # Add the current memory usage to the window title and the current cpu usage
            self.setWindowTitle(f"RoomInterfaceMk2[PID:{os.getpid()}] - CPU: {cpu_percent}% "
                                f"- Memory: {round(memory_usage / 1024 / 1024, 2)}MB{using_dev_server}")
        except Exception as e:
            logging.exception(e)
            self.setWindowTitle("RoomInterfaceMk2 - Unable to get process info")
            self.window_title_update_timer.stop()

    def closeEvent(self, a0) -> None:
        sys.exit()

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

    def reload_all(self):
        self.room_control.reload_schema()
        self.forecast.refresh_forecast()
        self.scene_control.reload()
        self.weather.make_request()
        self.system_control.refresh_interfaces()
        gc.collect()

    def keyReleaseEvent(self, a0) -> None:
        try:
            # On 'R' key press, refresh all data from the server 82
            match a0.key():
                case 68:  # D key
                    toggle_dev_server()
                    self.reload_all()
                case 82:  # R key
                    self.reload_all()
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
    logging.info("Starting RoomInterface")
    app = RoomInterface()
    app.exec()
