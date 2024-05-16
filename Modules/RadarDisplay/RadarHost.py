import datetime
import json

from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QLabel, QPushButton
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from loguru import logger as logging


class MapTile(QLabel):

    def __init__(self, host, parent=None, x=0, y=0):
        super().__init__(parent)
        self.parent = parent
        self.host = host
        self.setFixedSize(256, 256)
        self.x = x
        self.y = y
        self.setPixmap(QPixmap(f"Assets/MapTiles/{x}-{y}.png"))

        self.radar_images = []
        self.displayed_radar_image = 0

        self.radar_overlay = QLabel(self)
        self.radar_overlay.setFixedSize(256, 256)
        self.radar_overlay.setStyleSheet('background-color: transparent;')

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_response)

        self.outstanding_requests = 0

    def load_radar_overlays(self, timestamps):
        for timestamp in timestamps:
            self.outstanding_requests += 1
            self.network_manager.get(
                QNetworkRequest(QUrl(f"http://{self.host}/weather/radar/{timestamp}/{self.x}/{self.y}/4")))

    def set_radar_overlay(self, timestamp):
        self.displayed_radar_image = timestamp
        for radar_image in self.radar_images:
            if radar_image['timestamp'] == timestamp:
                self.radar_overlay.setPixmap(QPixmap.fromImage(radar_image['image']))
                return
        self.radar_overlay.setPixmap(QPixmap())

    def handle_response(self, reply):
        timestamp = int(reply.url().toString().split('/')[-4])  # Extract the timestamp from the URL
        try:
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Failed to load map tile {self.x}-{self.y}@{timestamp}: {reply.error()}")
                return
            data = reply.readAll()
            image = QImage.fromData(data)
            # Resize the image to 256x256 pixels
            image = image.scaled(256, 256,
                                 Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.radar_images.append({"timestamp": timestamp, "image": image})
            if timestamp == self.displayed_radar_image:
                self.radar_overlay.setPixmap(QPixmap.fromImage(image))
        except Exception as e:
            logging.error(f"Failed to load map tile {self.x}-{self.y}@{timestamp}: {e}")
            logging.exception(e)
        finally:
            self.outstanding_requests -= 1
            reply.deleteLater()


class RadarHost(QLabel):
    max_frames = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedSize(parent.width(), parent.height() - self.y())
        self.maptile_surface = QLabel(self)
        self.maptile_surface.setFixedSize(256 * 4, 256 * 3)
        self.map_tiles = []

        with open("Config/auth.json", "r") as f:
            self.auth = json.load(f)

        self.host = self.auth['host']

        self.focused = False
        self.playing = False

        # Map drag variables
        self.dragging = False
        self.drag_start = (0, 0)

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_response)

        self.timestamp_label = QLabel(self)
        self.timestamp_label.setFixedSize(212, 20)
        self.timestamp_label.move(0, 0)
        self.timestamp_label.setStyleSheet("background-color: black; color: #ffcd00; font-size: 14px;")
        self.timestamp_label.setFont(self.parent.get_font("JetBrainsMono-Regular"))
        self.timestamp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timestamp_label.setText("Loading...")

        self.now_button = QPushButton(self)
        self.now_button.setFixedSize(53, 20)
        self.now_button.move(0, 20)
        self.now_button.setText("Now")
        self.now_button.setStyleSheet("background-color: grey; color: white; font-size: 14px;")
        self.now_button.setFont(self.parent.get_font("JetBrainsMono-Regular"))
        self.now_button.clicked.connect(self.now_button_clicked)

        self.play_pause_button = QPushButton(self)
        self.play_pause_button.setFixedSize(53, 20)
        self.play_pause_button.move(53, 20)
        self.play_pause_button.setText("Play")
        self.play_pause_button.setStyleSheet("background-color: grey; color: white; font-size: 14px;")
        self.play_pause_button.setFont(self.parent.get_font("JetBrainsMono-Regular"))
        self.play_pause_button.clicked.connect(self.play_button_clicked)

        self.next_frame_button = QPushButton(self)
        self.next_frame_button.setFixedSize(53, 20)
        self.next_frame_button.move(106, 20)
        self.next_frame_button.setText("Next")
        self.next_frame_button.setStyleSheet("background-color: grey; color: white; font-size: 14px;")
        self.next_frame_button.setFont(self.parent.get_font("JetBrainsMono-Regular"))
        self.next_frame_button.clicked.connect(self.next_frame)

        self.center_button = QPushButton(self)
        self.center_button.setFixedSize(53, 20)
        self.center_button.move(159, 20)
        self.center_button.setText("Center")
        self.center_button.setStyleSheet("background-color: grey; color: white; font-size: 14px;")
        self.center_button.setFont(self.parent.get_font("JetBrainsMono-Regular"))
        self.center_button.clicked.connect(lambda: self.maptile_surface.move(0, -100))

        self.loading_label = QLabel(self)
        self.loading_label.setFont(self.parent.get_font("JetBrainsMono-Regular"))
        self.loading_label.setFixedSize(300, 30)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: #ffcd00; font-size: 15px; font-weight: bold; border: none;"
                                         " background-color: black")
        self.loading_label.setText("Loading Radar Frames [??/??]")
        self.loading_label.move(round((self.width() - self.loading_label.width()) / 2), 0)
        self.loading_label.hide()

        self.timestamp_list = []
        self.current_frame = 0

        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.next_frame)

        self.loading_check_timer = QTimer(self)
        self.loading_check_timer.timeout.connect(self.check_loading)

        self.activity_timer_callback = None

    def set_activity_timer_callback(self, callback):
        self.activity_timer_callback = callback

    def check_loading(self):
        # Compare the number of frames still loading to the total number of frames to be loaded
        total_tiles = len(self.map_tiles) * len(self.timestamp_list)
        loaded_frames = total_tiles - sum([map_tile.outstanding_requests for map_tile in self.map_tiles])
        self.loading_label.setText(f"Loading Radar Data [{loaded_frames}/{total_tiles}]")
        if all([map_tile.outstanding_requests == 0 for map_tile in self.map_tiles]):
            self.loading_check_timer.stop()
            self.loading_label.hide()

    def now_button_clicked(self):
        self.current_frame = len(self.timestamp_list) - 2
        self.next_frame()

    def play_button_clicked(self):
        self.playing = not self.playing
        if self.playing:
            self.play_pause_button.setText("Pause")
            self.playback_timer.start(500)
        else:
            self.play_pause_button.setText("Play")
            self.playback_timer.stop()

    def set_focus(self, focus) -> None:
        self.focused = focus
        if focus:
            self.load_maptiles()
            self.playing = False
            self.play_pause_button.setText("Play")
            self.show()
        else:
            self.unload_maptiles()
            self.playback_timer.stop()
            self.hide()

    def unload_maptiles(self):
        for map_tile in self.map_tiles:
            map_tile.deleteLater()
        self.map_tiles.clear()

    # Setup mouse events to allow the user to drag the radar map around
    def mousePressEvent(self, event):
        try:
            self.dragging = True
            if self.activity_timer_callback is not None:
                self.activity_timer_callback()
            self.drag_start = (event.pos().x(), event.pos().y())
        except Exception as e:
            logging.error(f"Failed to handle mouse press event: {e}")
            logging.exception(e)

    def mouseMoveEvent(self, event):
        try:
            if self.dragging:
                if self.activity_timer_callback is not None:
                    self.activity_timer_callback()
                dx, dy = event.pos().x() - self.drag_start[0], event.pos().y() - self.drag_start[1]
                self.maptile_surface.move(self.maptile_surface.x() + dx, self.maptile_surface.y() + dy)
                self.drag_start = (event.pos().x(), event.pos().y())
        except Exception as e:
            logging.error(f"Failed to handle mouse move event: {e}")
            logging.exception(e)

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def handle_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Failed to load radar data: {reply.error()}")
                return
            self.loading_check_timer.start(100)
            data = reply.readAll()
            data = json.loads(str(data, 'utf-8'))
            self.timestamp_list = data['weather_radar_list'][-self.max_frames:]
            self.current_frame = len(self.timestamp_list) - 2
            for map_tile in self.map_tiles:
                map_tile.load_radar_overlays(self.timestamp_list.__reversed__())
            self.next_frame()
        except Exception as e:
            logging.error(f"Failed to load radar data: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def next_frame(self):
        try:
            self.current_frame += 1
            self.current_frame %= len(self.timestamp_list)
            for map_tile in self.map_tiles:
                map_tile.set_radar_overlay(self.timestamp_list[self.current_frame])

            time_str = datetime.datetime.fromtimestamp(self.timestamp_list[self.current_frame]).strftime(
                "%Y-%m-%d %I:%M%p")
            self.timestamp_label.setText(f"{time_str} {str(self.current_frame + 1).zfill(2)}"
                                         f"/{len(self.timestamp_list)}")

        except Exception as e:
            logging.error(f"Failed to load next frame: {e}")
            logging.exception(e)

    def load_maptiles(self):
        # All map tiles are 256x256 pixels in size and are stored in 'Assets/MapTiles/{x}-{y}.png'
        # The map is 4 tiles wide and 3 tiles tall (15-18, 22-24)
        for y in range(22, 25):
            for x in range(15, 19):
                self.map_tiles.append(MapTile(self.host, self.maptile_surface, x, y))
        for i, map_tile in enumerate(self.map_tiles):
            map_tile.move((i % 4) * 256,
                          (i // 4) * 256)
        self.maptile_surface.move(0, -100)
        self.loading_label.setText("Acquiring Radar Frame List")
        self.loading_label.show()
        self.network_manager.get(QNetworkRequest(QUrl(f"http://{self.host}/weather/available_radars")))
