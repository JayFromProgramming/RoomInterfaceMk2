from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkRequest, QNetworkAccessManager
import time

network_check_timeout = 0
internet_connected = False
network_check_manager = QNetworkAccessManager()


def format_net_error(message):
    message = str(str(message).split('.')[1])
    # Add a space before each capital letter
    message = ''.join([char if char.islower() else f' {char}' for char in message])[1:]
    message = f"Cause: {message}"
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


def handle_network_check_response(reply):
    global internet_connected
    if str(reply.error()) != "NetworkError.NoError":
        internet_connected = False
        return
    internet_connected = True
    reply.deleteLater()


def has_internet() -> bool:
    global network_check_timeout, internet_connected, network_check_manager
    if time.time() < network_check_timeout:
        return internet_connected
    request = QNetworkRequest(QUrl("https://www.google.com"))
    request.setTransferTimeout(5000)
    network_check_manager.get(request)
    network_check_timeout = time.time() + 10
    return internet_connected


network_check_manager.finished.connect(handle_network_check_response)
