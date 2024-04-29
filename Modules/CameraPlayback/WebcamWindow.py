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
            self.media_player = QMediaPlayer()
            self.media_player.setVideoOutput(self)
            self.media_player.setSource(QUrl(source_url))
            self.video_widget = QVideoWidget(self)
            self.video_widget.move(0, 0)
            self.thumbnail_label = QLabel(self)
            self.thumbnail_label.move(0, 0)
            self.thumbnail_label.setFixedSize(self.width(), self.height())
            self.video_widget.setFixedSize(self.width(), self.height() - 15)
            self.video_widget.move(0, 15)
            self.media_player.setVideoOutput(self.video_widget)
            self.setFixedSize(round(size[0]), round(size[1]))
            self.name_label = QLabel(self)
            self.name_label.setText(name)
            self.name_label.setStyleSheet("color: #ffcd00; font-size: 10px; font-weight: bold; border: none; background-color: black")
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.name_label.setFixedSize(self.width(), 14)
            # Center the name label
            self.name_label.move(round((self.width() - self.name_label.width()) / 2), 0)
            self.name_label.show()

            self.current_thumbnail_data = None
            self.thumbnail_grabber = QNetworkAccessManager()
            self.thumbnail_grabber.finished.connect(self.handle_thumbnail_response)
            if thumbnail_url is not None:
                self.video_widget.hide()
                self.thumbnail_grabber.get(QNetworkRequest(QUrl(thumbnail_url)))

            self.thumbnail_update_timer = QTimer(self)
            self.thumbnail_update_timer.timeout.connect(lambda: self.thumbnail_grabber.get(QNetworkRequest(QUrl(thumbnail_url))))
            self.thumbnail_update_timer.start(60000)  # Update the thumbnail every minute

        except Exception as e:
            logging.error(f"Failed to initialize webcam window: {e}")
            logging.exception(e)

    def handle_thumbnail_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Network Error: {reply.error()}")
                return
            data = reply.readAll()
            data = data.data()
            self.current_thumbnail_data = data
            # The data is a jpeg byte array, so we need to convert it to a pixmap
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            # Resize the pixmap to fit the label
            pixmap = pixmap.scaled(self.thumbnail_label.width(), self.thumbnail_label.height(),
                                   Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.thumbnail_label.setPixmap(pixmap)
        except Exception as e:
            logging.error(f"Error handling thumbnail response: {e}")
            logging.exception(e)

    # def hideEvent(self, event):
    #     # self.media_player.stop()
    #     self.name_label.hide()
    #     super().hideEvent(event)
    #
    # def showEvent(self, event):
    #     # self.media_player.play()
    #     self.name_label.show()
    #     super().showEvent(event)

    def mousePressEvent(self, event):
        try:
            # If playback is paused, resume playback
            if self.media_player.isPlaying():
                self.media_player.stop()
                self.video_widget.hide()
            else:
                self.media_player.play()
                self.video_widget.show()
        except Exception as e:
            logging.error(f"Error pausing playback: {e}")
            logging.exception(e)

    def resizeEvent(self, a0):
        self.video_widget.setFixedSize(self.width(), self.height() - 15)
        self.thumbnail_label.setFixedSize(self.width(), self.height())
        # Resize the thumbnail to fit the label
        pixmap = QPixmap()
        pixmap.loadFromData(self.current_thumbnail_data)
        pixmap = pixmap.scaled(self.thumbnail_label.width(), self.thumbnail_label.height(),
                               Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.thumbnail_label.setPixmap(pixmap)
        self.name_label.setFixedSize(self.width(), 15)
        self.name_label.move(round((self.width() - self.name_label.width()) / 2), 0)
