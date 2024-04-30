import datetime
import json
import time

from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel

from loguru import logger as logging

from Utils.WeatherHelpers import kelvin_to_fahrenheit, mps_to_mph, wind_direction_arrow, convert_relative_humidity, \
    visibility_to_text


def ordinal(n):
    return str(n) + ('th' if 4 <= n <= 20 or 24 <= n <= 30 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))


class ForecastFocus(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.font = parent.parent.get_font("JetBrainsMono-Bold")
        self.current_reference_time = None
        self.focused = False
        self.setStyleSheet("background-color: black; border: 2px solid #ffcd00; border-radius: 10px")
        self.setFixedSize(800, 250)

        self.header = QLabel(self)
        self.header.setFont(self.font)
        self.header.setFixedSize(700, 35)
        self.header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.header.setStyleSheet("color: #ffcd00; font-size: 25px; font-weight: bold; border: none;"
                                  " background-color: transparent")
        self.header.setText("Forecast for Loading...")
        self.header.move(10, 0)

        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(100, 100)
        self.icon_label.move(self.width() - self.icon_label.width(), -15)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.icon_label.setStyleSheet("background-color: transparent; border: none")

        self.detailed_status = QLabel(self)
        self.detailed_status.setFont(self.font)
        self.detailed_status.setFixedSize(500, 100)
        self.detailed_status.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.detailed_status.setStyleSheet("color: white; font-size: 23px; font-weight: bold; border: none;"
                                           " background-color: transparent")
        self.detailed_status.setText("Loading...")
        self.detailed_status.move(10, 35)

        self.weather_info = QLabel(self)
        self.weather_info.setFont(self.font)
        self.weather_info.setFixedSize(800, 225)
        self.weather_info.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.weather_info.setStyleSheet("color: white; font-size: 19px; font-weight: bold; border: none;"
                                        " background-color: transparent")
        self.weather_info.setText("Loading...")
        self.weather_info.move(10, 65)

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_forecast_response)

        self.icon_manager = QNetworkAccessManager()
        self.icon_manager.finished.connect(self.handle_icon_response)

        self.show_timer = QTimer(self)
        self.show_timer.timeout.connect(self.hide_focus)
        self.show_timer.setSingleShot(True)
        self.setObjectName("ForecastFocus")

    def hideEvent(self, a0) -> None:
        self.focused = False
        super().hideEvent(a0)
        # Reset the text
        self.header.setText("Forecast for Loading...")
        self.detailed_status.setText("Loading...")
        self.weather_info.setText("Loading...")
        self.icon_label.clear()
        self.show_timer.stop()

    def hide_focus(self):
        self.hide()

    def showEvent(self, a0) -> None:
        self.focused = True
        super().showEvent(a0)
        self.show_timer.start(30000)

    def load(self, reference_time):
        if reference_time is None:
            return
        try:
            self.current_reference_time = reference_time
            ref_time = datetime.datetime.fromtimestamp(reference_time)
            date_suffix = ordinal(ref_time.day)
            # Display the reference time as Day Month Day(suffix), Time AM/PM
            reference_time_str = ref_time.strftime(f"%A, %B {date_suffix}, %I:%M%p")
            self.header.setText(f"Forecast for {reference_time_str}")
            self.make_request(reference_time)
        except Exception as e:
            logging.error(f"Error loading forecast focus: {e}")
            logging.exception(e)

    def make_request(self, reference_time):
        request = QNetworkRequest(QUrl(f"http://{self.parent.auth['host']}/weather/forecast/{reference_time}"))
        self.network_manager.get(request)

    def parse_forecast(self, data):
        output = ""
        try:
            self.detailed_status.setText(f"Expect: {data['detailed_status'].capitalize()}")
            temp = data["temperature"]
            output += f"The temperature will be {round(kelvin_to_fahrenheit(temp['temp']), 2)}°F "
            output += f"with a feels like of {round(kelvin_to_fahrenheit(temp['feels_like']), 2)}°F.\n"

            humidity = data["humidity"]
            indoor_humidity = convert_relative_humidity(humidity, temp["temp"] - 273.15, 16.6667)
            output += f"The humidity will be {humidity}% (~{round(indoor_humidity, 2)}% indoors).\n"

            if data["clouds"] == 0:
                output += "There will be no cloud cover.\n"
            else:
                output += f"There will be {data['clouds']}% cloud cover.\n"

            wind = data["wind"]
            wind_speed = round(mps_to_mph(wind["speed"]), 2)
            direction = wind_direction_arrow(wind["deg"])
            output += f"The wind will be blowing at {direction}{wind_speed} mph"
            if "gust" in wind:
                gust_speed = round(mps_to_mph(wind["gust"]), 2)
                output += f" with gusts up to {gust_speed} mph.\n"
            else:
                output += ".\n"

            visibility = data["visibility_distance"]
            output += f"The expected visibility will be {visibility_to_text(visibility)}.\n"

            if data['precipitation_probability'] > 0:
                output += f"There is a {round(data['precipitation_probability'] * 100)}% chance of precipitation.\n"
            else:
                output += "There is no chance of precipitation.\n"

            self.icon_manager.get(
                QNetworkRequest(QUrl(f"http://openweathermap.org/img/wn/{data['weather_icon_name']}@2x.png")))
        except Exception as e:
            logging.error(f"Error parsing forecast: {e}")
            logging.exception(e)
        finally:
            self.weather_info.setText(output)

    def handle_forecast_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                self.weather_info.setText("Error")
                # Check if the error was server related or client related
                return
            data = reply.readAll()
            data_str = data.data().decode("utf-8")
            self.parse_forecast(json.loads(data_str)["weather_forecast"])
        except Exception as e:
            logging.error(f"Error handling forecast response: {e}")
            logging.exception(e)

    def handle_icon_response(self, response):
        try:
            if str(response.error()) != "NetworkError.NoError":
                # Check if the error was server related or client related
                return
            data = response.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.icon_label.setPixmap(pixmap)
        except Exception as e:
            logging.error(f"Error handling icon response: {e}")
            logging.exception(e)

