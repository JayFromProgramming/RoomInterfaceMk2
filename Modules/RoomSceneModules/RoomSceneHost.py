import json
import os

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QLabel, QMenu, QInputDialog

from Modules.RoomSceneModules.SceneEditor.SceneEditorFlyout import SceneEditorFlyout
from Modules.RoomSceneModules.SceneWidget import SceneWidget
from Utils.ScrollableMenu import ScrollableMenu
from loguru import logger as logging


class RoomSceneHost(ScrollableMenu):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_top_folder = None
        self.setFixedSize(parent.width(), parent.height() - self.y())

        self.setStyleSheet("border: 2px solid #ffcd00; border-radius: 10px")
        if os.path.exists("Config/auth.json"):
            with open("Config/auth.json", "r") as f:
                data = json.load(f)
                self.auth = data["auth"]
                self.host = data["host"]
        else:
            os.makedirs("Config", exist_ok=True)
            with open("Config/auth.json", "w") as f:
                data = {
                    "auth": "",
                    "host": ""
                }
                json.dump(data, f)
                raise Exception("Please fill out the auth.json file with the proper information")

        self.menu = QMenu(self)
        self.menu.setStyleSheet("color: white")
        folder_action = self.menu.addAction("Create Folder")
        folder_action.triggered.connect(self.create_folder)
        new_scene_action = self.menu.addAction("Create New Scene")
        new_scene_action.triggered.connect(lambda: SceneEditorFlyout(self, None, None).show())

        self.back_widget = SceneWidget(self, None, None, is_back_widget=True)

        self.scene_widgets = []

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_network_response)

        self.hide()

        self.retry_timer = QTimer(self)
        self.retry_timer.timeout.connect(self.make_request)
        self.retry_timer.start(5000)
        self.make_request()

    def make_request(self):
        request = QNetworkRequest(QUrl(f"http://{self.host}/scene_get/scenes/null"))
        request.setRawHeader(b"Cookie", bytes("auth=" + self.auth, 'utf-8'))
        self.network_manager.get(request)

    def handle_network_response(self, reply):
        try:
            if str(reply.error()) != "NetworkError.NoError":
                logging.error(f"Error: {reply.error()}")
                self.retry_timer.start(5000)
                return
            data = reply.readAll()
            data = data.data().decode("utf-8")
            data = json.loads(data)
            # logging.debug(f"Data: {data}")
            self.retry_timer.stop()
            if "error" in data:
                logging.error(f"Error: {data['error']}")
                self.retry_timer.start(5000)
                return
            self.handle_scene_data(data["result"])
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
            self.retry_timer.start(5000)
        finally:
            reply.deleteLater()

    def reload(self):
        for widget in self.scene_widgets:
            if widget.is_back_widget:
                continue
            widget.hide()
            widget.deleteLater()
        self.scene_widgets = []
        self.make_request()

    def handle_scene_data(self, data):
        for scene_id, scene in data.items():
            self.scene_widgets.append(SceneWidget(self, scene_id, scene))
        self.scene_widgets.append(self.back_widget)
        self.layout_widgets()

    def resizeEvent(self, a0) -> None:
        super().resizeEvent(a0)
        self.setFixedSize(self.parent.width(), self.height())
        self.layout_widgets()

    def move_widgets(self, offset):
        offset = round(offset)
        for widget in self.scene_widgets:
            widget.move(widget.x(), widget.y() + offset)
        self.scroll_offset = 0

    def create_folder(self):
        """
        Create a popup asking for the folder name and then create a folder scene
        :return:
        """
        try:
            diag = QInputDialog()
            diag.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            diag.setLabelText("Enter the folder name:")
            diag.setOkButtonText("Create")
            diag.setCancelButtonText("Cancel")
            diag.exec()
            folder_name = diag.textValue()
            if folder_name == "":
                return
            SceneEditorFlyout(self, None, {"name": folder_name, "data": "{\"folder\":\"\"}",
                                           "parent": self.current_top_folder}).show()
        except Exception as e:
            logging.error(f"Error creating folder: {e}")
            logging.exception(e)

    def contextMenuEvent(self, ev):
        try:
            self.menu.exec(ev.globalPos())
        except Exception as e:
            logging.error(f"Error in contextMenuEvent: {e}")
            logging.exception(e)

    def open_folder(self, folder_id):
        self.back_widget.scene_id = self.current_top_folder
        self.current_top_folder = folder_id
        self.layout_widgets()

    def layout_widgets(self):
        # Hide all the widgets
        for widget in self.scene_widgets:
            widget.hide()

        current_widgets = [widget for widget in self.scene_widgets if widget.parent_scene == self.current_top_folder or widget.is_back_widget]
        # Sort the scenes by number of triggers (lowest to highest, excluding the new scene widget)
        current_widgets.sort(key=lambda x: (x.is_back_widget, x.is_folder, len(x.data['triggers']) if not x.is_folder else 0))

        # Lay the widgets out row by row with a 10 pixel margin
        y_offset = 20
        x_offset = 5
        center_offset = []
        row_num = 0
        # Start a new row when the widgets won't fit on the current row
        for widget in current_widgets:
            widget.move(x_offset, y_offset)
            widget.row_num = row_num
            widget.show()
            x_offset += widget.width() + 7
            # Wrap around to the next row if the widget won't fit on the current row
            if x_offset + widget.width() > self.width():
                center_offset.append(round((self.width() - x_offset - 5) / 2))
                row_num += 1
                x_offset = 5
                y_offset += widget.height() + 10

        center_offset.append(round((self.width() - x_offset - 5) / 2))
        row_num += 1

        # Center the widgets
        for widget in current_widgets:
            widget.move(widget.x() + center_offset[widget.row_num], widget.y())
