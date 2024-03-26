import math


def kelvin_to_fahrenheit(kelvin):
    return (kelvin - 273.15) * 9 / 5 + 32


def meters_to_miles(meters):
    return meters * 0.000621371


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
        top, bottom = float(visibility).as_integer_ratio()
        visibility = f"{top}/{bottom} mi"
    return visibility


def wind_direction_arrow(degree):
    def offset(check):
        return (degree - check + 180 + 360) % 360 - 180

    if 22.5 >= offset(0) >= -22.5:
        return "↑"
    elif 22.5 >= offset(45) >= -22.5:
        return "↗"
    elif 22.5 >= offset(90) >= -22.5:
        return "→"
    elif 22.5 >= offset(135) >= -22.5:
        return "↘"
    elif 22.5 >= offset(180) >= -22.5:
        return "↓"
    elif 22.5 >= offset(225) >= -22.5:
        return "↙"
    elif 22.5 >= offset(270) >= -22.5:
        return "←"
    elif 22.5 >= offset(315) >= -22.5:
        return "↖"
    return ""


def mps_to_mph(mps):
    return mps * 2.23694


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
