

class WeatherCodes:

    short_lookup_table = {
        "Clear": 0,
        "Sunny": 1,
        "Clouds": [2, 3],
        "Fog": [45, 48],
        "L.Drizzle": 51,
        "Drizle": 53,
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

    @staticmethod
    def lookup(code: int) -> str:
        for key, value in WeatherCodes.short_lookup_table.items():
            if isinstance(value, list):
                if code in value:
                    return key
            elif value == code:
                return key
        return str(code)


