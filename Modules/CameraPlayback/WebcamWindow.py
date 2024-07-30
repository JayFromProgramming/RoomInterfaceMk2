
from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtGui import QPixmap

from PyQt6.QtMultimedia import QMediaPlayer, QMediaMetaData
from PyQt6.QtMultimediaWidgets import QVideoWidget

from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel

from loguru import logger as logging


class WebcamWindow(QLabel):

    def __init__(self, parent, source_url, thumbnail_url, name, size=None):
        try:
            super().__init__(parent)
            self.source_url = source_url
            self.media_player = QMediaPlayer()
            self.media_player.setVideoOutput(self)
            self.video_widget = QVideoWidget(self)
            self.thumbnail_label = QLabel(self)
            self.thumbnail_label.move(0, 10)
            self.thumbnail_label.setFixedSize(self.width(), self.height())
            self.video_widget.setFixedSize(self.width(), self.height() - 15)
            self.video_widget.move(0, 15)
            self.media_player.setVideoOutput(self.video_widget)
            self.setFixedSize(round(size[0]), round(size[1]))
            self.name = name
            self.name_label = QLabel(self)
            self.name_label.setText(name)
            self.name_label.setStyleSheet("color: #ffcd00; font-size: 10px; font-weight: bold;"
                                          " border: none; background-color: black")
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.name_label.setFixedSize(self.width(), 14)
            # Center the name label
            self.name_label.move(round((self.width() - self.name_label.width()) / 2), 0)
            self.name_label.show()

            self.media_player.errorOccurred.connect(self.video_player_error)
            self.media_player.metaDataChanged.connect(self.metadata_updated)

            self.current_thumbnail_data = None
            self.thumbnail_grabber = QNetworkAccessManager()
            self.thumbnail_grabber.finished.connect(self.handle_thumbnail_response)
            if thumbnail_url is not None:
                self.video_widget.hide()
                self.thumbnail_grabber.get(QNetworkRequest(QUrl(thumbnail_url)))

            self.thumbnail_update_timer = QTimer(self)
            self.thumbnail_update_timer.timeout.connect(lambda: self.thumbnail_grabber.get(QNetworkRequest(QUrl(thumbnail_url))))
            self.thumbnail_update_timer.start(60000)  # Update the thumbnail every minute

            self.is_playing = False
            self.enlarged = False

        except Exception as e:
            logging.error(f"Failed to initialize webcam window: {e}")
            logging.exception(e)

    def handle_thumbnail_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Cam [{self.name}] Network Error: {reply.error()}")
                self.thumbnail_update_timer.start(1000)
                return
            data = reply.readAll()
            data = data.data()
            self.current_thumbnail_data = data
            # The data is a jpeg byte array, so we need to convert it to a pixmap
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            # Resize the pixmap to fit the label
            pixmap = pixmap.scaled(self.thumbnail_label.width(), self.thumbnail_label.height() - 15,
                                   Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.thumbnail_label.setPixmap(pixmap)
            self.thumbnail_update_timer.start(60000)
        except Exception as e:
            logging.error(f"Error handling thumbnail response: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def release_resources(self):
        self.media_player.stop()
        self.media_player.deleteLater()
        self.thumbnail_grabber.deleteLater()
        self.thumbnail_update_timer.deleteLater()

    def hideEvent(self, event):
        self.thumbnail_update_timer.stop()

    def showEvent(self, event):
        # self.media_player.play()
        self.thumbnail_update_timer.start(60000)

    # def mousePressEvent(self, event):
    #     try:
    #
    #     except Exception as e:
    #         logging.error(f"Error pausing playback: {e}")
    #         logging.exception(e)

    def toggle_playback(self, force_play=False, force_pause=False):
        try:
            # If playback is paused, resume playback
            if self.is_playing:
                self.media_player.stop()
                self.video_widget.hide()
                # Unload the video
                self.media_player.setSource(QUrl())
            else:
                self.media_player.setSource(QUrl(self.source_url))
                self.media_player.play()
                self.video_widget.show()
            self.is_playing = not self.is_playing
        except Exception as e:
            logging.error(f"Error toggling playback: {e}")
            logging.exception(e)

    def video_player_error(self, error):
        logging.error(f"Error playing video {self.source_url}: {error}")
        # Replace the video with the thumbnail
        self.video_widget.hide()
        self.thumbnail_label.show()

    def metadata_updated(self):
        try:
            # Get the metadata
            metadata = self.media_player.metaData()
            # print(metadata.value('')
            # print(metadata)
            if self.media_player.audioOutput() is not None:
                self.media_player.audioOutput().setVolume(0)
        except Exception as e:
            logging.error(f"Error updating metadata: {e}")
            logging.exception(e)

    def resizeEvent(self, a0):
        self.video_widget.setFixedSize(self.width(), self.height() - 15)
        self.thumbnail_label.setFixedSize(self.width(), self.height())
        # Resize the thumbnail to fit the label
        pixmap = QPixmap()
        pixmap.loadFromData(self.current_thumbnail_data)
        pixmap = pixmap.scaled(self.thumbnail_label.width(), self.thumbnail_label.height() - 15,
                               Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.thumbnail_label.setPixmap(pixmap)
        self.name_label.setFixedSize(self.width(), 15)
        self.name_label.move(round((self.width() - self.name_label.width()) / 2), 0)
