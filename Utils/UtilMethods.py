from PyQt6.QtGui import QPixmap


def parse_net_err_message(message):
    message = message.split("server replied: ")[1]
    return message


def load_no_image(size=None):
    if size is None:
        size = (40, 40)
    with open("Assets/Images/no_image.png", "rb") as f:
        data = f.read()
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        # Resize the image to fit the label
        pixmap = pixmap.scaled(size[0], size[1])
        return pixmap

