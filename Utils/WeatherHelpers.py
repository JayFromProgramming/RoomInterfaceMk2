def kelvin_to_fahrenheit(kelvin):
    return (kelvin - 273.15) * 9 / 5 + 32


def visibility_to_text(visibility):
    if visibility > 6:
        visibility = "Clear"
    elif visibility % 1 == 0:
        visibility = f"{int(visibility)} mi"
    elif visibility > 1:
        visibility = f"{round(visibility, 2)} mi"
    elif len(str(float(visibility).as_integer_ratio()[0])) > 4:
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
