import datetime
import json
import random
import time
from PyQt6.QtCore import QUrl, QDateTime, Qt
from PyQt6.QtWidgets import QLabel
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from loguru import logger as logging

from Modules.Forecast.WeatherCodeEnum import WeatherCodes
from Utils.UtilMethods import load_no_image
from Utils.WeatherHelpers import wind_direction_arrow, celcius_to_fahrenheit, kph_to_mph


class ForecastValue(QLabel):

    def __init__(self, parent=None, value=None, label=None, font=None):
        super().__init__(parent)
        self.setFixedSize(75, 45)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: none; background-color: transparent")
        self.upper_label = QLabel(self)
        self.upper_label.setFixedSize(75, 22)
        self.upper_label.setStyleSheet("color: #ffcd00; font-size: 20px; font-weight: bold;"
                                       "background-color: transparent; border: none; border-radius: none")
        self.upper_label.setFont(font)

        self.lower_label = QLabel(self)
        self.lower_label.setFixedSize(75, 22)
        self.lower_label.setStyleSheet("color: white; font-size: 20px; font-weight: regular;"
                                       " border: none; border-radius: none")
        self.lower_label.setFont(font)

        self.upper_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.lower_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.upper_label.move(0, 0)
        self.lower_label.move(0, self.upper_label.height() + 1)

        self.upper_label.setText(label)
        self.lower_label.setText(value)


class ForecastEntry(QLabel):
    """
    Displays the information for a specific forecast entry
    """

    forecast_width = 75

    def __init__(self, parent=None, reference_time=None, placeholder=False):
        super().__init__(parent)
        if reference_time is None:
            raise ValueError("reference_time must be set")
        self.setFixedSize(self.forecast_width, 275)
        self.parent = parent
        self.placeholder = placeholder
        self.loaded = False
        self.reference_time = reference_time
        self.setObjectName(f"forecast_entry_{reference_time}")

        font = parent.parent.get_font("JetBrainsMono-Bold")

        self.date_label = QLabel(self)
        self.date_label.setFixedSize(75, 20)
        self.date_label.setStyleSheet("color: #ffcd00; font-size: 20px; font-weight: bold;"
                                      " border: none; border-radius: none")
        self.date_label.setFont(font)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.move(0, 0)
        self.date_label.setText("?????")

        self.time_label = QLabel(self)
        self.time_label.setFixedSize(75, 20)
        self.time_label.setStyleSheet("color: #ffcd00; font-size: 20px; font-weight: bold; border: none;")
        self.time_label.setFont(font)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.move(0, self.date_label.height())
        self.time_label.setText("?????")

        self.status_label = QLabel(self)
        self.status_label.setFixedSize(75, 20)
        self.status_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold; border: none;")
        self.status_label.setFont(font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.move(0, self.time_label.height() + self.time_label.y())
        self.status_label.setText("Wait.." if not placeholder else "N/A")

        self.weather_icon = QLabel(self)
        self.weather_icon.setFixedSize(75, 40)
        self.weather_icon.move(0, self.status_label.height() + self.status_label.y())
        self.weather_icon.setStyleSheet("border: none;")
        self.weather_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.weather_icon.setPixmap(load_no_image())

        self.temperature_label = QLabel(self)
        self.temperature_label.setFixedSize(75, 30)
        self.temperature_label.setStyleSheet("color: #ffcd00; font-size: 22px; font-weight: bold; border: none;")
        self.temperature_label.setFont(font)
        self.temperature_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temperature_label.move(0, self.weather_icon.height() + self.weather_icon.y())
        self.temperature_label.setText("N/A" if not placeholder else f"{reference_time}")

        self.humidity_label = ForecastValue(self, "N/A", "Humid.", font)
        self.humidity_label.move(0, self.temperature_label.y() + self.temperature_label.height())

        self.wind_speed_label = ForecastValue(self, "N/A", "Wind", font)
        self.wind_speed_label.move(0, self.humidity_label.y() + self.humidity_label.height())

        self.feels_like_label = ForecastValue(self, "N/A", "Feels", font)
        self.feels_like_label.move(0, self.wind_speed_label.y() + self.wind_speed_label.height())

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_forecast_response)

        self.icon_manager = self.parent.icon_manager

    def load(self):
        if self.loaded or self.placeholder:
            return
        self.loaded = True
        self.make_request(self.reference_time)

    def make_request(self, reference_time):
        request = QNetworkRequest(QUrl(f"http://{self.parent.auth['host']}/weather/forecast/{reference_time}"))
        self.network_manager.get(request)

    def handle_icon_response(self, pixmap):
        try:
            if pixmap is None:
                return
            self.weather_icon.setPixmap(pixmap)
        except Exception as e:
            logging.error(f"Error handling icon response: {e}")
            logging.exception(e)

    def handle_forecast_response(self, response):
        try:
            if str(response.error()) != "NetworkError.NoError":
                self.date_label.setText("NET")
                self.time_label.setText("Error")
                logging.error(f"Error: {response.error()}")
                return
            data = response.readAll()
            data = data.data().decode("utf-8")
            data = json.loads(data)
            self.parse_data(data["weather_forecast"])
        except Exception as e:
            logging.error(f"Error handling forecast response: {e}")
            logging.exception(e)
        finally:
            response.deleteLater()

    def parse_data(self, data):
        """
        Parses the data from the server
        :param data:
        :return:
        """
        try:
            time_parsed = datetime.datetime.fromisoformat(data["time"])  # The timezone is already included in the time but it's utc
            # Convert the time to the local timezone
            time_parsed = time_parsed.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
            reference_time = QDateTime.fromSecsSinceEpoch(int(time.mktime(time_parsed.timetuple())))
            acq_time = data["acquisition_time"]
            # If the acquisition time is more than 2 hours old, then the data is stale and mark it with an * next to the time
            if time.time() - acq_time > 7200:
                self.time_label.setText(reference_time.toString("hAP") + "*")
            else:
                self.time_label.setText(reference_time.toString("hAP"))
            # date is mm/dd
            self.date_label.setText(reference_time.toString("MM/dd"))
            self.status_label.setText(WeatherCodes.code_short_lookup(data["weathercode"]))
            temperature = celcius_to_fahrenheit(data["temperature_2m"])
            self.temperature_label.setText(f"{round(temperature)}°F")
            feels_like = celcius_to_fahrenheit(data["apparent_temperature"])
            # feels_like = calculate_real_feel(data["temperature_2m"], data["relativehumidity_2m"], data["windspeed_10m"])
            chance = data['precipitation_probability']
            if chance > 20:
                self.feels_like_label.upper_label.setText(f"Chance")
                self.feels_like_label.lower_label.setText(f"{round(chance)}%")
            else:
                self.feels_like_label.lower_label.setText(f"{round(feels_like)}°F")

            wind_speed = round(kph_to_mph(data["windspeed_10m"]), 2)
            wind_direction = wind_direction_arrow(data["winddirection_10m"])
            self.wind_speed_label.lower_label.setText(f"{wind_direction}{round(wind_speed)}mph")

            self.humidity_label.lower_label.setText(f"{data['relativehumidity_2m']:0.0f}%")
            is_day = True if data["is_day"] == 1 else False
            self.icon_manager.get_icon(WeatherCodes.code_to_icon(data['weathercode'], is_day), self.handle_icon_response)
            # self.repaint()
        except Exception as e:
            logging.error(f"Error parsing forecast data: {e}")
            logging.exception(e)
            self.status_label.setText("Error")
