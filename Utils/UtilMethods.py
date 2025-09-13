from PyQt6.QtCore import QUrl
import PyQt6.QtNetwork as QN
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
import time
import re
from loguru import logger as logging

network_check_timeout = 0
internet_connected = False
use_dev_server = False
network_check_manager = QNetworkAccessManager()


with open("Config/auth.json", "r") as f:
    import json
    auth = json.load(f)


def is_using_dev_server():
    global use_dev_server
    return use_dev_server


def allow_unverified_ssl(allow: bool):
    ssl_config = QN.QSslConfiguration.defaultConfiguration()
    ssl_config.setPeerVerifyMode(QN.QSslSocket.PeerVerifyMode.VerifyNone if allow else QN.QSslSocket.PeerVerifyMode.VerifyPeer)
    QN.QSslConfiguration.setDefaultConfiguration(ssl_config)


def allowing_unverified_ssl() -> bool:
    ssl_config = QN.QSslConfiguration.defaultConfiguration()
    return ssl_config.peerVerifyMode() == QN.QSslSocket.PeerVerifyMode.VerifyNone


def toggle_dev_server():
    global use_dev_server
    use_dev_server = not use_dev_server
    allow_unverified_ssl(use_dev_server)


def get_auth():
    global use_dev_server
    if use_dev_server:
        return auth["dev_auth"]
    return auth["auth"]


def get_host():
    global use_dev_server
    if use_dev_server:
        return auth["dev_host"]
    # If the host is a local IP address enable unverified ssl
    ip_regex = re.compile(r"^(?:http://|https://)?(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?$")
    if ip_regex.match(auth["host"]) and not allowing_unverified_ssl():
        logging.info("Using local IP address, allowing unverified SSL")
        allow_unverified_ssl(True)
    return auth["host"]


def network_error_to_string(response, has_network):
    if response.error() == QNetworkReply.NetworkError.ConnectionRefusedError:
        return f"SERVER DOWN"
    elif response.error() == QNetworkReply.NetworkError.OperationCanceledError and has_network:
        return f"SERVER OFFLINE"
    elif response.error() == QNetworkReply.NetworkError.InternalServerError:
        return f"SERVER ERROR"
    elif response.error() == QNetworkReply.NetworkError.OperationCanceledError and not has_network:
        return f"NETWORK ERROR"
    elif response.error() == QNetworkReply.NetworkError.HostNotFoundError and not has_network:
        return f"NO NETWORK"
    elif response.error() == QNetworkReply.NetworkError.HostNotFoundError and has_network:
        return f"SERVER NOT FOUND"
    elif response.error() == QNetworkReply.NetworkError.TemporaryNetworkFailureError:
        return f"NET FAILURE"
    elif response.error() == QNetworkReply.NetworkError.UnknownNetworkError and not has_network:
        return f"NET FAILURE"
    elif response.error() == QNetworkReply.NetworkError.TimeoutError and has_network:
        return f"SERVER TIMEOUT"
    elif response.error() == QNetworkReply.NetworkError.ServiceUnavailableError:
        return f"ENDPOINT UNAVAILABLE"
    elif response.error() == QNetworkReply.NetworkError.SslHandshakeFailedError:
        return f"ENCRYPTION FAILURE"
    elif response.error() == QNetworkReply.NetworkError.ContentNotFoundError:
        return f"NOT FOUND"
    elif response.error() == QNetworkReply.NetworkError.ContentAccessDenied:
        return f"ACCESS DENIED"
    elif response.error() == QNetworkReply.NetworkError.NoError:
        return f"NO ERROR?"
    elif response.error() == QNetworkReply.NetworkError.ProxyConnectionRefusedError:
        return f"PROXY REFUSED"
    elif response.error() == QNetworkReply.NetworkError.ProxyConnectionClosedError:
        return f"PROXY CLOSED"
    elif response.error() == QNetworkReply.NetworkError.ProxyNotFoundError:
        return f"PROXY NOT FOUND"
    elif response.error() == QNetworkReply.NetworkError.ProxyTimeoutError:
        return f"PROXY TIMEOUT"
    elif response.error() == QNetworkReply.NetworkError.ContentReSendError:
        return f"CONTENT RESEND?"
    else:
        return f"UNKNOWN ERROR"


def clean_error_type(error):
    if error is QNetworkReply.NetworkError.UnknownNetworkError:
        return "UNKNOWN NETWORK ERROR"
    error_str = str(error).split('.')[-1]
    # Split the string at each capital letter and join with a space
    error_str = ''.join([char if char.islower() else f' {char}' for char in error_str])[1:].upper()
    return error_str.replace('ERROR', '').strip()


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
