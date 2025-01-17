

class WeatherCodes:

    short_lookup_table = {
        "Clear": 0,
        "Sunny": 1,
        "Clouds": [2, 3],
        "Fog": [45, 48],
        "L.Driz": [51, 56],
        "Drizle": 53,
        "H.Driz": [55, 57],
        "L.Rain": 61,
        "Rain": 63,
        "H.Rain": 65,
        "F.Rain": [66, 67],
        "L.Snow": 71,
        "Snow": [73, 77, 85],
        "H.Snow": [75, 87],
        "T-Storm": [80, 81, 82],
        "Hail": [95, 96, 97, 98],
    }

    detailed_lookup_table = {
        "Clear Sky": 0,
        "Few Clouds": 1,
        "Partly Cloudy": 2,
        "Overcast Clouds": 3,
        "Fog": [45, 48],
        "Light Drizzle": 51,
        "Moderate Drizzle": 53,
        "Heavy Drizzle": 55,
        "Light Freezing Drizzle": 56,
        "Heavy Freezing Drizzle": 57,
        "Light Rain": 61,
        "Rain": 63,
        "Heavy Rain": 65,
        "Freezing Rain": 66,
        "Intense Freezing Rain": 67,
        "Light Snow": 71,
        "Snow": 73,
        "Heavy Snow": 75,
        "Snow Grains": 77,  # Not sure what this is
        "Light Rain Showers": 80,
        "Rain Showers": 81,
        "Violent Rain Showers": 82,
        "Snow Showers": 85,
        "Heavy Snow Showers": 87,
        "Thunderstorm": [95, 96, 97, 98],
    }

    owm_icon_conversion = {
        "01": [0, 1],  # Clear Sky
        "02": 2,  # Few Clouds
        "03": 2,  # Scattered Clouds
        "04": 3,  # Broken Clouds
        "09": [61, 63, 65, 66, 67],  # Shower Rain
        "10": [51, 53, 55, 56, 57],  # Rain
        "11": [80, 81, 82, 95, 95, 97, 98],  # Thunderstorm
        "13": [71, 73, 75, 85],  # Snow
        "50": [45, 48],  # Mist
    }

    @staticmethod
    def code_short_lookup(code: int) -> str:
        for key, value in WeatherCodes.short_lookup_table.items():
            if isinstance(value, list):
                if code in value:
                    return key
            elif value == code:
                return key
        return str(code)

    @staticmethod
    def code_to_icon(code: int, is_day: bool) -> str:
        for key, value in WeatherCodes.owm_icon_conversion.items():
            if isinstance(value, list):
                if code in value:
                    return f"{key}d" if is_day else f"{key}n"
            elif value == code:
                return f"{key}d" if is_day else f"{key}n"
        return ""

    @staticmethod
    def code_detailed_lookup(code: int) -> str:
        for key, value in WeatherCodes.detailed_lookup_table.items():
            if isinstance(value, list):
                if code in value:
                    return key
            elif value == code:
                return key
        return str(code)
