import math


def kelvin_to_fahrenheit(kelvin):
    return (kelvin - 273.15) * 9 / 5 + 32

def celcius_to_fahrenheit(celcius):
    return celcius * 9 / 5 + 32

def meters_to_miles(meters):
    return meters * 0.000621371

def mm_to_inches(mm, round_to=2):
    return round(mm * 0.0393701, round_to)


def visibility_to_text(visibility):
    visibility = meters_to_miles(visibility)
    if visibility > 6:
        visibility = "Clear"
    elif visibility % 1 == 0:
        visibility = f"{int(visibility)} mi"
    elif visibility > 1:
        visibility = f"{round(visibility, 2)} mi"
    elif len(str(float(round(visibility, 2)).as_integer_ratio()[0])) > 4:
        visibility = f"{round(visibility, 2)} mi"
    else:
        top, bottom = float(round(visibility, 2)).as_integer_ratio()
        visibility = f"{top}/{bottom} mi"
    return visibility


def wind_direction_arrow(degree):
    def offset(check):
        return (degree - check + 180 + 360) % 360 - 180

    if 22.5 >= offset(0) >= -22.5:
        return "↓"
    elif 22.5 >= offset(45) >= -22.5:
        return "↙"
    elif 22.5 >= offset(90) >= -22.5:
        return "←"
    elif 22.5 >= offset(135) >= -22.5:
        return "↖"
    elif 22.5 >= offset(180) >= -22.5:
        return "↑"
    elif 22.5 >= offset(225) >= -22.5:
        return "↗"
    elif 22.5 >= offset(270) >= -22.5:
        return "→"
    elif 22.5 >= offset(315) >= -22.5:
        return "↘"
    print(f"Unknown wind direction: {degree}")
    return "?"


def mps_to_mph(mps):
    return mps * 2.23694

def kph_to_mph(kph):
    return kph * 0.621371


def convert_relative_humidity(R1, T1, T2):
    """
    @param R1: Relative humidity in environment 1 (as a fraction)
    @param T1: Temperature in environment 1  (in Celsius)
    @param T2: Temperature in environment 2  (in Celsius)
    @return: Relative humidity in environment 2 (as a fraction)
    """
    # Calculate saturation vapor pressure at temperature T1
    Ps1 = 0.611 * math.exp(17.27 * T1 / (T1 + 237.3))

    # Calculate saturation vapor pressure at temperature T2
    Ps2 = 0.611 * math.exp(17.27 * T2 / (T2 + 237.3))

    # Calculate vapor pressure in environment 1
    Pv1 = R1 * Ps1 / 100

    # Calculate relative humidity in environment 2
    R2 = Pv1 / Ps2 * 100

    return R2


def calculate_real_feel(temp, wind_speed, humidity):
    """
    @param temp: Temperature in Celsius
    @param wind_speed: Wind speed in m/s
    @param humidity: Relative humidity as a percentage 0-1
    @return: Real feel temperature in Celsius
    """
    # Calculate wind chill
    wind_chill = 13.12 + 0.6215 * temp - 11.37 * wind_speed ** 0.16 + 0.3965 * temp * wind_speed ** 0.16

    # Calculate heat index
    heat_index = -8.78469475556 + 1.61139411 * temp + 2.33854883889 * humidity - 0.14611605 * temp * humidity - 0.012308094 * temp ** 2 - 0.0164248277778 * humidity ** 2 + 0.002211732 * temp ** 2 * humidity + 0.00072546 * temp * humidity ** 2 - 0.000003582 * temp ** 2 * humidity ** 2

    # Calculate real feel
    real_feel = (wind_chill + heat_index) / 2

    return real_feel
