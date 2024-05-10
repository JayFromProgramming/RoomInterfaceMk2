import os
import sys
import time
import threading

from PyQt6.QtCore import QTimer, QElapsedTimer, QEvent
from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton, QDialog, QLabel, QVBoxLayout
from PyQt6.QtGui import QFont, QFontDatabase

from Modules.CameraPlayback.WebcamLayout import WebcamLayout
from Modules.CameraPlayback.WebcamWindow import WebcamWindow
# Replace this with auto-import later
from Modules.DisplayClock import DisplayClock
from Modules.CurrentWeather import CurrentWeather
from Modules.Forecast.ForecastHost import ForecastHost
from Modules.MenuBar import MenuBar

from Modules.RoomControlModules.RoomControlHost import RoomControlHost

import traceback

from loguru import logger as logging

from Modules.RoomSceneModules.RoomSceneHost import RoomSceneHost
from Modules.SystemControlModules.SystemControlHost import SystemControlHost


# class WatchdogThread(threading.Thread):
#
#     def __init__(self, timeout=60, fail_callback=None):
#         super().__init__(name="WatchdogThread", daemon=True)
#         self.running = True
#         self.last_feed = time.time()
#         self.timeout = timeout
#         self.fail_callback = fail_callback
#
#     def run(self):
#         logging.info("Watchdog thread started")
#         while self.running:
#             if time.time() - self.last_feed > self.timeout:
#                 if self.fail_callback is not None:
#                     self.fail_callback()
#                     time.sleep(self.timeout)
#             time.sleep(1)
#
#     def stop(self):
#         self.running = False
#
#     def feed(self):
#         self.last_feed = time.time()
from Utils.PopupManager import PopupManager


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

    # def feed_watchdog(self):
    #     self.watchdog.feed()
    #
    # def watchdog_failed(self):
    #     # If the watchdog fails that means that an event in the qt event loop has locked up the main thread
    #     # We need to log what the current event is and then restart the application
    #     logging.error("Watchdog failed, attempting to find root cause before restarting")
    #     try:
    #         main_thread_id = threading.main_thread()
    #         logging.error(f"At time of failure there were {len(sys._current_frames())} threads running"
    #                         f" and the main thread id is {main_thread_id.ident}")
    #         for thread_id, frame in sys._current_frames().items():
    #             if thread_id == main_thread_id.ident:
    #                 logging.error("Main thread stack trace:")
    #                 traceback.print_stack(frame)
    #     except Exception as e:
    #         logging.error(f"Error logging stack: {e}")
    #     logging.error("Restarting application")
    #     exit(-1)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.cached_fonts = {}

        self.setWindowTitle("RoomInterfaceMk2")
        self.setGeometry(100, 100, 1024, 600)
        # Set the background color to black
        self.setStyleSheet("background-color: black;")

        PopupManager.instance()
        PopupManager.instance().add_parent(self)
        PopupManager.instance().show()
        # Set the popup manager to be the top layer


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

        self.webcam_layout = WebcamLayout(self)
        self.webcam_layout.move(0, 90)
        # self.webcam_layout.show()

        self.menu_bar = MenuBar(self)
        # Move the menu bar to the very bottom of the window
        self.menu_bar.move(0, self.height() - self.menu_bar.height())

        self.menu_bar.add_flyout_button("System Control", self.system_control, 60)
        self.menu_bar.add_flyout_button("Room Control", self.room_control, 60)
        self.menu_bar.add_flyout_button("Scene Control", self.scene_control)
        self.menu_bar.add_flyout_button("Webcams", self.webcam_layout)
        self.system_control.setFixedSize(self.width(), self.room_control.y() - 90)
        self.scene_control.setFixedSize(self.width(), self.room_control.y() - 90)

        self.show()
        # If running on a linux system, use this to make the window full screen
        if os.name == "posix":
            self.showFullScreen()

        PopupManager.instance().raise_()

    def mousePressEvent(self, a0) -> None:
        self.menu_bar.reset_focus_timer()
        super().mousePressEvent(a0)

    # def focus_room_control(self, force_close=False):
    #     if self.room_control.focused or force_close:
    #         self.room_control.move(0, self.forecast.height() + self.forecast.y() + 10)
    #         self.room_control.set_focus(False)
    #         self.menu_bar.room_control_expand.setText("↑Room Control↑")
    #         self.forecast.show()
    #         self.refocus_timer.stop()
    #     else:
    #         self.room_control.move(0, 90)
    #         self.room_control.set_focus(True)
    #         self.menu_bar.room_control_expand.setText("↓Room Control↓")
    #         self.refocus_timer.start(60000)  # 15 seconds
    #         self.forecast.hide()

    # def focus_system_control(self, force_close=False):
    #     try:
    #         if self.system_control.focused or force_close:
    #             self.system_control.set_focus(False)
    #             self.system_control.hide()
    #             self.menu_bar.system_control_expand.setText("↑System Control↑")
    #             self.forecast.show()
    #             self.refocus_timer.stop()
    #         else:
    #             self.system_control.set_focus(True)
    #             self.system_control.show()
    #             self.menu_bar.system_control_expand.setText("↓System Control↓")
    #             self.system_control.setFixedSize(self.width(), self.room_control.y() - 90)
    #             self.refocus_timer.start(60000)  # 15 seconds
    #             self.forecast.hide()
    #     except Exception as e:
    #         logging.exception(e)

    # def focus_scene_control(self, force_close=False):
    #     if self.scene_control.focused or force_close:
    #         self.scene_control.set_focus(False)
    #         self.scene_control.hide()
    #         self.menu_bar.scenes_expand.setText("↑Scene Control↑")
    #         self.forecast.show()
    #         self.refocus_timer.stop()
    #     else:
    #         self.scene_control.set_focus(True)
    #         self.scene_control.show()
    #         # The scene controls max height is the distance from 90 pixels to the top of room control
    #         self.scene_control.setFixedSize(self.width(), self.room_control.y() - 90)
    #         self.menu_bar.scenes_expand.setText("↓Scene Control↓")
    #         self.forecast.hide()
    #         self.refocus_timer.start(120000)

    # def focus_webcam_layout(self, force_close=False):
    #     if self.webcam_layout.focused or force_close:
    #         self.webcam_layout.set_focus(False)
    #         self.webcam_layout.hide()
    #         # self.menu_bar.webcam_expand.setText("↑Webcams↑")
    #         self.forecast.show()
    #         self.refocus_timer.stop()
    #     else:
    #         self.webcam_layout.set_focus(True)
    #         self.webcam_layout.show()
    #         # self.menu_bar.webcam_expand.setText("↓Webcams↓")
    #         self.webcam_layout.setFixedSize(self.width(), self.height() - 90 - self.menu_bar.height())
    #         self.forecast.hide()
    #         self.refocus_timer.start(120000)

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

    # def keyReleaseEvent(self, a0) -> None:
    #     try:
    #         if a0.key() == 16777220:  # Enter key
    #             self.focus_room_control()
    #         elif a0.key() == 16777221:  # Shift key
    #             self.focus_scene_control()
    #         elif a0.key() == 16777222:  # Ctrl key
    #             self.focus_system_control()
    #         elif a0.key() == 87:
    #             self.focus_webcam_layout()
    #         super().keyReleaseEvent(a0)
    #     except Exception as e:
    #         logging.exception(e)

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
