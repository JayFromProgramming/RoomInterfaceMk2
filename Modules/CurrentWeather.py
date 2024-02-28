import datetime
import time

from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QRegion, QColor
from PyQt6.QtWidgets import QLabel
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from loguru import logger as logging

import json

from Utils.WeatherHelpers import wind_direction_arrow, kelvin_to_fahrenheit, visibility_to_text


class CurrentWeather(QLabel):
    """
    Creates a surface that contains the current weather in the format:
    {weather_icon} {temperature}°F {weather_description}
                   Feels: {feels}°F Clouds: {Clouds} Humidity {humidity}%
                   Vis: {visibility} Wind: {wind_speed} {wind_direction} {last_updated}
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent")

        # Setup the 3 labels for the rows
        self.weather_label_icon = QLabel(self)
        self.weather_label_icon.setFixedSize(100, 100)
        self.weather_label_icon.move(-15, -15)
        self.weather_label_icon.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # self.weather_label_icon.setStyleSheet("background-color: white;")

        self.weather_header = QLabel(self)
        self.weather_header.setStyleSheet("color: #ffcd00; font-size: 42px; "
                                          "text-align: left; font-weight: bold;")
        self.weather_header.setFixedSize(690, 50)
        self.weather_header.setFont(parent.get_font("JetBrainsMono-Regular"))
        self.weather_header.move(75, 0)
        self.weather_header.setText("Loading...")

        self.weather_row_1 = QLabel(self)
        self.weather_row_1.setStyleSheet("color: white; font-size: 15px")
        self.weather_row_1.setFixedSize(600, 20)
        self.weather_row_1.setFont(parent.get_font("JetBrainsMono-Regular"))
        self.weather_row_1.move(75, self.weather_header.height())
        self.weather_row_1.setText("Feels: N/A; Clouds: N/A; Humidity: N/A")

        self.weather_update_time = QLabel(self)
        self.weather_update_time.setStyleSheet("color: grey; font-size: 15px")
        self.weather_update_time.setFixedSize(71, 20)
        self.weather_update_time.setFont(parent.get_font("JetBrainsMono-Regular"))
        self.weather_update_time.move(2, self.weather_header.height() + self.weather_row_1.height())
        self.weather_update_time.setText("Loading")

        self.weather_row_2 = QLabel(self)
        self.weather_row_2.setStyleSheet("color: white; font-size: 15px")
        self.weather_row_2.setFixedSize(600, 20)
        self.weather_row_2.setFont(parent.get_font("JetBrainsMono-Regular"))
        self.weather_row_2.move(75, self.weather_row_1.y() + self.weather_row_1.height())
        self.weather_row_2.setText("Loading Vis: N/A; Wind: N/A; Twilight: N/A")

        # Set the size of the label
        self.setFixedSize(690, 200)

        # Create the network manager
        self.weather_manager = QNetworkAccessManager()
        self.icon_manager = QNetworkAccessManager()
        self.weather_manager.finished.connect(self.handle_weather_response)
        self.icon_manager.finished.connect(self.handle_icon_response)
        self.make_request()

        # Setup the timer to refresh the weather every 30 seconds
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.make_request)
        self.refresh_timer.start(30000)

    def make_request(self):
        """Makes a request to the given URL"""
        logging.info("Making request to get current weather")
        request = QNetworkRequest(QUrl("http://moldy.mug.loafclan.org/weather/now"))
        # request.setRawHeader(b"Cookie", b"auth=5149e8d1606397fddc35cf0303b98c1318b963c3c0e6069fcabb8d970c8fe9bd")
        self.weather_manager.get(request)

    def handle_weather_response(self, reply):
        """Handles the response from the server"""
        try:
            # Check if the server replied ok
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Error: {reply.error()}")
                self.weather_header.setText("Network Error")
                self.weather_row_1.setText(str(reply.error()))
                self.weather_row_2.setText("Weather data unavailable")
                return
            data = reply.readAll()
            data = data.data().decode("utf-8")
            data = json.loads(data)
            self.parse_data(data)
            reply.deleteLater()
        except Exception as e:
            logging.error(f"Error handling weather response: {e}")
            logging.exception(e)

    def handle_icon_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                print(f"Error: {reply.error()}")
                return
            pixmap = QPixmap()
            pixmap.loadFromData(reply.readAll())
            self.weather_label_icon.setPixmap(pixmap)
            reply.deleteLater()
        except Exception as e:
            logging.error(f"Error handling icon response: {e}")
            logging.exception(e)

    def parse_data(self, data):
        """Parses the data from the server"""
        try:
            temperature = kelvin_to_fahrenheit(data["temperature"]["temp"])
            feels_like = kelvin_to_fahrenheit(data["temperature"]["feels_like"])
            wind_speed = data["wind"]["speed"]
            wind_direction = wind_direction_arrow(data["wind"]["deg"])
            visibility = visibility_to_text(data["visibility_distance"])
            status = str(data["detailed_status"]).capitalize()
            last_updated = time.strftime("%I:%M%p", time.localtime(data["reference_time"]))
            sunrise = datetime.datetime.fromtimestamp(data["sunrise_time"])
            sunset = datetime.datetime.fromtimestamp(data["sunset_time"])
            reference_time = datetime.datetime.fromtimestamp(data["reference_time"])

            if sunrise < reference_time < sunset:
                sunrise_or_sunset = "sunset_time"
            else:
                sunrise_or_sunset = "sunrise_time"
            twilight_string = "Sunrise" if sunrise_or_sunset == "sunrise_time" else "Sunset"
            twilight = time.strftime("%I:%M%p", time.localtime(data[sunrise_or_sunset]))

            self.weather_update_time.setText(last_updated)
            self.weather_header.setText(f"{temperature:.0F}°F {status}")
            self.weather_row_1.setText(f"Feels: {feels_like:04.1f}°F; Clouds: {data['clouds']:02}%; Humidity: {data['humidity']}%")
            self.weather_row_2.setText(f"Vis: {visibility}; Wind: {wind_direction}{wind_speed:04.1f}mph; {twilight_string}: {twilight}")
            self.icon_manager.get(QNetworkRequest(QUrl(f"http://openweathermap.org/img/wn/{data['weather_icon_name']}@2x.png")))
        except Exception as e:
            logging.error(f"Error parsing weather data: {e}")
            logging.exception(e)
