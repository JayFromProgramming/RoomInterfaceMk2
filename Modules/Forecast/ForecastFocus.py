import datetime
import json
import time

from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel

from loguru import logger as logging

from Modules.Forecast.WeatherCodeEnum import WeatherCodes
from Utils.UtilMethods import load_no_image
from Utils.WeatherHelpers import kelvin_to_fahrenheit, mps_to_mph, wind_direction_arrow, convert_relative_humidity, \
    visibility_to_text, mm_to_inches, celcius_to_fahrenheit, kph_to_mph


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
        self.header.move(10, 5)

        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(100, 100)
        self.icon_label.move(self.width() - self.icon_label.width() - 10, 10)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.icon_label.setStyleSheet("background-color: transparent; border: none")
        self.icon_label.setPixmap(load_no_image((55, 55)))

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

        self.acquisition_time_label = QLabel(self)
        self.acquisition_time_label.setFont(self.font)
        self.acquisition_time_label.setFixedSize(300, 35)
        self.acquisition_time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.acquisition_time_label.setStyleSheet("color: grey; font-size: 10px; font-weight: bold; border: none;"
                                                  " background-color: transparent")
        self.acquisition_time_label.setText("Acquired: ???")
        self.acquisition_time_label.move(self.width() - self.acquisition_time_label.width() - 10,
                                         self.height() - self.acquisition_time_label.height() - 10)

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
        self.icon_label.setPixmap(load_no_image((55, 55)))
        self.icon_label.move(self.width() - self.icon_label.width() - 10, 10)
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
            ref_time = datetime.datetime.fromisoformat(reference_time)
            ref_time = ref_time.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
            date_suffix = ordinal(ref_time.day)
            # Display the reference time as Day Month Day(suffix), Time AM/PM
            if ref_time.timestamp() <= 30:
                reference_time_str = "\"The Beginning of Time\""
            else:
                reference_time_str = ref_time.strftime(f"%A, %B {date_suffix}, %I%p")
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
            print(data)
            if 'acquisition_time' in data and data['acquisition_time'] is not None:
                acquisition_time = datetime.datetime.fromtimestamp(data['acquisition_time'])
                date_suffix = ordinal(acquisition_time.day)
                acquisition_time_str = acquisition_time.strftime(f"%A, %B {date_suffix}, %I:%M%p")
                self.acquisition_time_label.setText(f"Acquired: {acquisition_time_str}")
            else:
                self.acquisition_time_label.setText("Acquired: Not Available")

            self.detailed_status.setText(f"Expect: {WeatherCodes.code_detailed_lookup(data['weathercode'])}")
            output += f"The temperature will be {round(celcius_to_fahrenheit(data['temperature_2m']), 2)}°F "
            output += f"with a feels like of {round(celcius_to_fahrenheit(data['apparent_temperature']), 2)}°F.\n"

            humidity = data["relativehumidity_2m"]
            indoor_humidity = convert_relative_humidity(humidity, data["temperature_2m"], 16.6667)
            output += f"The humidity will be {humidity}% (~{round(indoor_humidity, 2)}% indoors).\n"

            if data["cloudcover"] == 0:
                output += "There will be no cloud cover.\n"
            else:
                output += f"There will be {data['cloudcover']}% cloud cover.\n"

            wind_speed = round(kph_to_mph(data["windspeed_10m"]), 2)
            direction = wind_direction_arrow(data["winddirection_10m"])
            output += f"The wind will be blowing at {direction}{wind_speed} mph"

            gust_speed = round(kph_to_mph(data["windgusts_10m"]), 2)
            output += f" with gusts up to {gust_speed} mph.\n"

            visibility = data["visibility"]
            output += f"The expected visibility will be {visibility_to_text(visibility)}.\n"

            rain, snow, percip = data["precipitation"], data["snowfall"], ""
            if snow > 0:
                percip = f"{mm_to_inches(snow, round_to=3)}in of snow"
            elif rain > 0:
                percip = f"{mm_to_inches(rain, round_to=3)}in of rain"
            else:
                percip = "precipitation"

            if data['precipitation_probability'] > 10:
                output += f"There is a {data['precipitation_probability']}% chance of " \
                    f"{percip}\n"
            else:
                output += "There is no chance of precipitation.\n"
            icon = WeatherCodes.code_to_icon(data['weathercode'], True if data['is_day'] == 1 else False)
            self.icon_manager.get(
                QNetworkRequest(QUrl(f"http://openweathermap.org/img/wn/{icon}@2x.png")))
        except Exception as e:
            logging.error(f"Error parsing forecast: {e}")
            logging.exception(e)
        finally:
            self.weather_info.setText(output)

    def handle_forecast_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                self.weather_info.setText(f"Error: {reply.error()}")
                # Check if the error was server related or client related
                return
            data = reply.readAll()
            data_str = data.data().decode("utf-8")
            self.parse_forecast(json.loads(data_str)["weather_forecast"])
        except Exception as e:
            logging.error(f"Error handling forecast response: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def handle_icon_response(self, response):
        try:
            if str(response.error()) != "NetworkError.NoError":
                # Check if the error was server related or client related
                return
            data = response.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.icon_label.setPixmap(pixmap)
            self.icon_label.move(self.width() - self.icon_label.width(), -15)
        except Exception as e:
            logging.error(f"Error handling icon response: {e}")
            logging.exception(e)
        finally:
            response.deleteLater()
