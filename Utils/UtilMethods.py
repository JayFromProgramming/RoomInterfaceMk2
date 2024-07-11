from PyQt6.QtGui import QPixmap


def format_net_error(message):
    message = str(str(message).split('.')[1])
    # Add a space before each capital letter
    message = ''.join([char if char.islower() else f' {char}' for char in message])[1:]
    # Remove the word "Error"
    message = message.replace("Error", "")
    message = f"Error: {message}"
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

