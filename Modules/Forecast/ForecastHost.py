import datetime
import json
import time

from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from loguru import logger as logging

from Modules.Forecast.ForecastEntry import ForecastEntry
from Modules.Forecast.ForecastFocus import ForecastFocus


class IconManager(QNetworkAccessManager):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.icon_cache = {}
        self.icon_requests = {}  # {icon_id: [callbacks]}
        self.finished.connect(self.handle_response)

    def get_icon(self, icon_id: str, callback):
        if icon_id in self.icon_cache:
            # logging.info(f"Icon {icon_id} found in cache")
            callback(self.icon_cache[icon_id])
            return
        if icon_id in self.icon_requests:
            # logging.info(f"Icon {icon_id} is already being requested")
            self.icon_requests[icon_id].append(callback)
            return
        request = QNetworkRequest(QUrl(f"http://openweathermap.org/img/wn/{icon_id}.png"))
        self.icon_requests[icon_id] = [callback]
        self.get(request)

    def handle_response(self, reply):
        try:
            icon_id = reply.request().url().fileName().split(".")[0]
            callbacks = self.icon_requests[icon_id]
            if reply.error() != QNetworkReply.NetworkError.NoError:
                logging.error(f"Error: {reply.error()}")
                for callback in callbacks:
                    callback(None)
                return
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.icon_cache[icon_id] = pixmap
            for callback in callbacks:
                callback(pixmap)
            self.icon_requests.pop(icon_id)
        except Exception as e:
            logging.error(f"Error handling icon response: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()


class ForecastHost(QLabel):
    """
    This is the base label that all the forecast widgets will be placed on
    It spans the entire width of the window and is 300px tall
    """

    widget_y_offset = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedSize(parent.width(), 275)
        self.dragging = False
        self.scroll_offset = 0
        self.scroll_start = 0
        self.scroll_begin = 0
        self.last_scroll = 0
        # self.setStyleSheet("background-color: white")
        self.forecast_focus = ForecastFocus(self)

        self.icon_manager = IconManager(self)

        self.forecast_widgets = [ForecastEntry(self, i, True) for i in range(48)]
        self.forecasts = []
        self.lines = []
        self.layout_widgets()

        with open("Config/auth.json", "r") as f:
            self.auth = json.load(f)

        # Put the forecast focus on top of the forecast widgets and hide it
        self.forecast_focus.move(20, 20)
        self.forecast_focus.hide()
        self.forecast_focus.raise_()

        self.forecast_manager = QNetworkAccessManager()
        self.forecast_manager.finished.connect(self.handle_forecast_response)

        # Setup timer to refresh the forecast every 15 minutes
        self.refresh_forecast()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_forecast)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.start(300000)

        self.scroll_reset_timer = QTimer(self)
        self.scroll_reset_timer.timeout.connect(self.reset_scroll)
        self.scroll_reset_timer.start(500)

        self.error_label = QLabel(self)
        self.error_label.setFixedSize(600, 80)
        self.error_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold; border: none;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Center the error label
        self.error_label.move((self.width() - self.error_label.width()) // 2,
                              (self.height() - self.error_label.height()) // 2)
        self.error_label.hide()

    def reset_scroll(self):
        if time.time() - self.last_scroll > 10 and self.forecast_focus.isHidden():
            self.scroll_offset -= 1
            self.layout_widgets()

    def refresh_forecast(self):
        logging.info("Refreshing forecast")
        self.make_request()

    def make_request(self):
        request = QNetworkRequest(QUrl(f"http://{self.auth['host']}/weather/available_forecast"))
        self.forecast_manager.get(request)

    def hide_all_widgets(self):
        for widget in self.forecast_widgets:
            widget.hide()
        for line in self.lines:
            line.hide()

    def handle_forecast_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Error: {reply.error()}")
                self.error_label.setText(f"Error fetching forecast\n{reply.error()}")
                self.error_label.show()
                # Hide all the forecast widgets
                self.hide_all_widgets()
                self.refresh_timer.start(5000)
                return
            self.error_label.hide()
            for widget in self.forecast_widgets:
                widget.show()
            data = reply.readAll()
            data = data.data().decode("utf-8")
            data = json.loads(data)
            forecasts = data["weather_forecast_list"]
            for widget in self.forecast_widgets:
                widget.release()
                widget.deleteLater()
            self.forecast_widgets.clear()
            self.forecasts = forecasts
            self.forecast_widgets = [ForecastEntry(self, forecast) for forecast in forecasts
                                     if datetime.datetime.fromisoformat(forecast) > datetime.datetime.utcnow()]
            logging.info(f"Loaded {len(self.forecast_widgets)} forecast widgets")
            reply.deleteLater()
            self.layout_widgets()
        except Exception as e:
            logging.error(f"Error handling icon response: {e}")
            logging.exception(e)
            self.refresh_timer.start(5000)  # Retry in 5 seconds
        else:
            self.refresh_timer.start(300000)  # Refresh every 5 minutes
        finally:
            reply.deleteLater()

    def layout_widgets(self):
        """
        Lays out the forecast widgets
        :return:
        """
        for widget in self.forecast_widgets:
            widget.hide()

        for line in self.lines:
            line.hide()
            line.deleteLater()

        self.lines.clear()

        if not self.forecast_widgets:
            return

        # Determine the current scroll offset
        if self.scroll_offset < 0:
            self.scroll_offset = 0
            self.scroll_reset_timer.stop()
        elif self.scroll_offset > len(self.forecast_widgets) - 1:
            self.scroll_offset = len(self.forecast_widgets) - 1

        # Use the scroll offset to determine which widgets to display
        forecast_widgets = self.forecast_widgets[self.scroll_offset:]

        # Calculate the maximum number of widgets that can fit in the width provided without one of them getting cut off
        padding = 5
        max_widgets = self.width() // (forecast_widgets[0].width() + padding)
        # Calculate what the remaining width is (after the widgets are placed)
        remaining_width = self.width() - (max_widgets * (forecast_widgets[0].width() + padding))
        # Calculate the padding on the left side
        lpadding = remaining_width // 2

        # Draw the left line
        line = QLabel(self)
        line.setFixedSize(1, self.height())
        line.setStyleSheet("background-color: #ffcd00")
        line.move(lpadding - round(padding / 2), 10)
        self.lines.append(line)

        for i, widget in enumerate(forecast_widgets[:max_widgets]):
            widget.move((i * (widget.width() + padding)) + lpadding, 10)
            widget.load()  # Lazy load the forecast data
            widget.show()

            # Draw the vertical line
            line = QLabel(self)
            widget.line = line
            line.setFixedSize(1, self.height())
            line.setStyleSheet("background-color: #ffcd00")
            line.move(widget.x() + widget.width() + round(padding / 2), 10)
            self.lines.append(line)

        for line in self.lines:
            line.show()
            # line.deleteLater()

        # print(f"Drew {len(self.lines)} lines")

        # self.lines.clear()
        self.forecast_focus.raise_()

    def wheelEvent(self, a0) -> None:
        """
        Used to scroll the forecast widgets up and down
        :param a0:
        :return:
        """
        if a0.angleDelta().y() > 0:
            self.scroll_offset -= 1
        else:
            self.scroll_offset += 1
        self.layout_widgets()
        self.last_scroll = time.time()
        self.scroll_reset_timer.start(500)

    def mousePressEvent(self, ev):
        self.dragging = True
        self.scroll_start = ev.pos().x()
        self.scroll_begin = ev.pos().x()
        self.scroll_reset_timer.start(500)

    def mouseMoveEvent(self, ev):
        """
        Used to scroll the forecast widgets if the user is dragging, if the user hits the end of the forecast, the
        forecast will not scroll any further in that direction
        :param ev:
        :return:
        """
        if self.dragging:
            total_drag = ev.pos().x() - self.scroll_start
            if total_drag > 20:
                self.scroll_offset -= 1
                self.layout_widgets()
                self.scroll_start = ev.pos().x()
            elif total_drag < -20:
                self.scroll_offset += 1
                self.layout_widgets()
                self.scroll_start = ev.pos().x()

    def get_clicked_forecast(self, x, y):
        """
        Returns the forecast widget that was clicked
        :param x: The x position of the click
        :param y: The y position of the click
        :return: The forecast widget that was clicked
        """
        for widget in self.forecast_widgets:
            if widget.x() < x < widget.x() + widget.width() and widget.y() < y < widget.y() + widget.height():
                return widget
        return None

    def mouseReleaseEvent(self, ev):
        try:
            self.dragging = False
            self.parent.resizeEvent(None)
            self.parent.update()
            # If the mouse moved less than 20 pixels, then the user clicked
            if abs(ev.pos().x() - self.scroll_begin) < 20:
                if self.forecast_focus.isHidden():
                    logging.info("Showing forecast focus")
                    self.forecast_focus.show()
                    self.forecast_focus.raise_()
                    clicked = self.get_clicked_forecast(ev.pos().x(), ev.pos().y())
                    if clicked:
                        self.forecast_focus.load(clicked.reference_time)
                    else:
                        self.forecast_focus.hide()
                        self.forecast_focus.clear()
                else:
                    logging.info("Hiding forecast focus")
                    self.forecast_focus.hide()
                    self.forecast_focus.clear()
            self.last_scroll = time.time()
        except Exception as e:
            logging.error(f"Error handling mouse release event: {e}")
            logging.exception(e)
            self.dragging = False
            self.parent.resizeEvent(None)
            self.parent.update()
            self.last_scroll = time.time()
