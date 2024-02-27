import json
import time

from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtWidgets import QLabel
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from loguru import logger as logging

from Modules.Forecast.ForecastEntry import ForecastEntry


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
        self.last_scroll = 0
        # self.setStyleSheet("background-color: white")

        self.forecast_widgets = [ForecastEntry(self, i, True) for i in range(48)]
        self.lines = []
        self.layout_widgets()

        # self.upper_line = QLabel(self)
        # self.upper_line.setFixedSize(self.width(), 1)
        # self.upper_line.setStyleSheet("background-color: #ffcd00")
        # self.upper_line.move(0, 0)
        #
        # self.title = QLabel(self)
        # self.title.setFixedSize(100, 10)
        # self.title.setStyleSheet("color: #ffcd00; font-size: 10px; font-weight: bold")
        # self.title.setText("Forecast")
        # self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #
        # # Put the title dead center
        # self.title.move(round((self.width() - self.title.width()) / 2), 0)

        self.lines = []

        self.forecast_manager = QNetworkAccessManager()
        self.forecast_manager.finished.connect(self.handle_forecast_response)

        # Setup timer to refresh the forecast every 15 minutes
        self.refresh_forecast()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_forecast)
        # self.refresh_timer.start(900000)
        self.refresh_timer.start(300000)

        self.scroll_reset_timer = QTimer(self)
        self.scroll_reset_timer.timeout.connect(self.reset_scroll)
        self.scroll_reset_timer.start(500)

    def reset_scroll(self):
        if time.time() - self.last_scroll > 10:
            self.scroll_offset -= 1
            self.layout_widgets()

    def refresh_forecast(self):
        logging.info("Refreshing forecast")
        self.make_request()

    def make_request(self):
        request = QNetworkRequest(QUrl("http://moldy.mug.loafclan.org/weather/available_forecast"))
        self.forecast_manager.get(request)

    def handle_forecast_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Error: {reply.error()}")
                self.refresh_timer.start(5000)
                return
            data = reply.readAll()
            data = data.data().decode("utf-8")
            data = json.loads(data)
            forecasts = data["weather_forecast_list"]
            for widget in self.forecast_widgets:
                widget.deleteLater()
            self.forecast_widgets.clear()
            self.forecast_widgets = [ForecastEntry(self, forecast) for forecast in forecasts]
            reply.deleteLater()
            self.layout_widgets()
        except Exception as e:
            logging.error(f"Error handling icon response: {e}")
            logging.exception(e)
            self.refresh_timer.start(5000)  # Retry in 5 seconds
        else:
            self.refresh_timer.start(300000)

    def layout_widgets(self):
        """
        Lays out the forecast widgets
        :return:
        """
        for widget in self.forecast_widgets:
            widget.hide()

        for line in self.lines:
            line.deleteLater()

        self.lines.clear()

        if not self.forecast_widgets:
            return

        # Determine the current scroll offset
        if self.scroll_offset < 0:
            self.scroll_offset = 0
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

        # self.lines.clear()

    def mousePressEvent(self, ev):
        self.dragging = True
        self.scroll_start = ev.pos().x()
        print("Scroll enter")

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

    def mouseReleaseEvent(self, ev):
        self.dragging = False
        self.parent.resizeEvent(None)
        self.parent.update()
        self.last_scroll = time.time()
        print("Scroll exit")
