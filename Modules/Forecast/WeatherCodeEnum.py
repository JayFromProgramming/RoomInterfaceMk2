

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
        "Snow": 73,
        "H.Snow": 75,
        "Storm": [80, 81, 82],
        "T-Storm": [95, 96, 97, 98],
    }

    owm_icon_conversion = {
        "01": 0,  # Clear Sky
        "02": 2,  # Few Clouds
        "03": 2,  # Scattered Clouds
        "04": 3,  # Broken Clouds
        "09": [61, 63, 65, 66, 67],  # Shower Rain
        "10": [51, 53, 55, 56, 57],  # Rain
        "11": [80, 81, 82, 95, 95, 97, 98],  # Thunderstorm
        "13": [71, 73, 75],  # Snow
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


