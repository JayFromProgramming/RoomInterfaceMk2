import json
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt6.QtWidgets import QLabel, QMenu, QDialog, QLineEdit, QDialogButtonBox, QFormLayout

from loguru import logger as logging

from Modules.RoomControlModules.DeviceControllers.NotInitializedDevice import NotInitializedDevice
from Utils.RoomDevice import RoomDevice

import os

from Utils.UtilMethods import get_host, get_auth

if os.path.exists("Modules/RoomControlModules/DeviceControllers"):
    for file in os.listdir("Modules/RoomControlModules/DeviceControllers"):
        if file.endswith(".py") and not file.startswith("__"):
            __import__(f"Modules.RoomControlModules.DeviceControllers.{file[:-3]}")


class DeviceGroupHost(QLabel):

    def __init__(self, parent=None, group_name=None, center=False):
        super().__init__(parent)
        self.setStyleSheet("border: 2px solid #ffcd00; border-radius: 10px")
        self.group_name = group_name
        self.parent = parent
        self.center = center
        self.setFixedSize(parent.width(), 300)
        self.dragging = False
        self.scroll_offset = 0
        self.scroll_start = 0
        self.last_scroll = 0
        self.device_widgets = []
        self.lines = []
        self.font = self.parent.font
        self.pending_parent_layout = False

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_group_menu)

        self.group_label = QLabel(self)
        self.group_label.setFont(self.font)
        self.group_label.setFixedSize(self.width() - 10, 20)
        self.group_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.group_label.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none; "
                                       "background-color: transparent")
        self.group_label.setText(f"{group_name}")
        self.group_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.group_label.customContextMenuRequested.connect(self.show_group_menu)

        # Move the group label to the middle of the top
        self.group_label.move(round((self.width() - self.group_label.width()) / 2), 0)

        self.no_devices_label = QLabel(self)
        self.no_devices_label.setFont(self.font)
        self.no_devices_label.setFixedSize(self.width(), 30)
        self.no_devices_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.no_devices_label.setStyleSheet(
            "color: white; font-size: 15px; font-weight: bold; border: none; background-color: transparent")
        self.no_devices_label.setText(f"No Devices Found For {group_name}")
        self.no_devices_label.move(round((self.width() - self.no_devices_label.width()) / 2), 20)
        self.no_devices_label.hide()

        self.layout_widgets()

        self.device_names = []
        self.delete_on_rebuild = False

        self.type_manager = QNetworkAccessManager()
        self.type_manager.finished.connect(self.create_widget)

        self.name_manager = QNetworkAccessManager()
        self.name_manager.finished.connect(self.handle_name_response)

        self.group_schema_manager = QNetworkAccessManager()
        self.group_schema_manager.finished.connect(self.handle_group_schema_response)

    def make_name_request(self, device):
        request = QNetworkRequest(QUrl(f"{get_host()}/name/{device}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
        self.name_manager.get(request)

    def handle_name_response(self, reply):
        try:
            original_query = reply.request().url().toString()
            device = original_query.split("/")[-1]
            match reply.error():
                case QNetworkReply.NetworkError.NoError:
                    pass  # No error
                case QNetworkReply.NetworkError.ContentNotFoundError:
                    logging.warning(f"Device name not found for: {device}")
                    reply.deleteLater()
                    return
                case _:
                    logging.error(f"Network error getting device name for {device}: {reply.errorString()}")
                    reply.deleteLater()
                    return
            # Get the data from the reply
            data = reply.readAll()
            for widget in self.device_widgets:
                if widget.device == device:
                    widget.update_human_name(str(data, 'utf-8'))
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def widget_add(self, widget):
        # Make a widget of the same device name isn't already in the list
        for w in self.device_widgets:
            if w.device == widget.device:
                widget.hide()
                widget.deleteLater()
                return
        self.device_widgets.append(widget)
        self.layout_widgets()

    def widgets_delete(self):
        logging.warning(f"Deleting widgets for {self.group_name}")
        for widget in self.device_widgets:
            widget.hide()
            widget.deleteLater()
        self.device_widgets.clear()
        self.layout_widgets()

    def widgets_rebuild(self):
        """
        Called by a widget when it determines that it's type does not match the server's type.
        This will remove all widgets and re-request the device types. This is useful when the server is restarted and
        the device types either change or are not yet loaded.
        :return:
        """
        try:
            logging.warning(f"Queueing rebuild for {self.group_name}")
            self.delete_on_rebuild = True
            for device in self.device_widgets:
                self.add_device(device.device, device.priority, True)
        except Exception as e:
            logging.error(f"Error rebuilding widgets: {e}")
            logging.exception(e)

    def create_widget(self, response):
        try:
            if self.delete_on_rebuild:
                self.widgets_delete()
                self.delete_on_rebuild = False
            original_query = response.request().url().toString()
            priority = response.request().rawHeader(b"Priority").data().decode("utf-8")
            # Get the device name from the query
            device = original_query.split("/")[-1]
            data = response.readAll()
            device_type = data.data().decode("utf-8")
            found = False
            for widget_class in RoomDevice.__subclasses__():
                # Find a widget class that supports the device type
                if widget_class.supports_type(device_type):
                    widget = widget_class(self, device, priority)
                    self.widget_add(widget)
                    found = True
                    break
            if not found:
                widget = NotInitializedDevice(self, device, priority)
                self.widget_add(widget)
                logging.warning(f"Device ({device}) of type [{device_type}] not supported")
            self.layout_widgets()
        except Exception as e:
            logging.error(f"Error handling network response: {e}")
            logging.exception(e)
        finally:
            response.deleteLater()

    def add_device(self, device: str, priority: int = 0, refresh: bool = False):
        request = QNetworkRequest(QUrl(f"{get_host()}/get_type/{device}"))
        request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
        request.setRawHeader(b"Priority", bytes(str(priority), 'utf-8'))
        if not refresh:  # Prevents getting stuck in an infinite loop if we are rebuilding widgets
            self.device_names.append(device)
        self.type_manager.get(request)

    def sort_widgets(self):
        # Sort devices first by size, then type, then name (so the order is consistent independent of the load order)
        self.device_widgets.sort(key=lambda x: (x.width(), x.priority, x.__class__.__name__, x.device), reverse=True)

    def layout_widgets(self):
        if len(self.device_widgets) == 0:
            self.no_devices_label.show()
            height_changed = self.height() != 100
            self.setFixedSize(self.width(), 100)
            if height_changed:
                self._request_parent_layout()
            return
        else:
            self.no_devices_label.hide()

        H_GAP = 5
        V_GAP = 10
        LEFT_PAD = 10
        TOP_PAD = 20
        container_w = self.width()

        self.sort_widgets()

        placed = []  # (x, y, w, h) per widget, indexed parallel to self.device_widgets

        def can_place(x, y, w, h):
            """Check position validity against all placed rects with gap constraints."""
            if x + w > container_w:
                return False
            for px, py, pw, ph in placed:
                sep_x = (x >= px + pw + H_GAP) or (x + w + H_GAP <= px)
                sep_y = (y >= py + ph + V_GAP) or (y + h + V_GAP <= py)
                if not (sep_x or sep_y):
                    return False
            return True

        def find_position(w, h):
            """Topmost-then-leftmost valid position from candidate edges."""
            y_cands = sorted(set(
                [TOP_PAD] + [py + ph + V_GAP for _, py, _, ph in placed]
            ))
            x_cands = sorted(set(
                [LEFT_PAD] + [px + pw + H_GAP for px, _, pw, _ in placed]
            ))
            for y in y_cands:
                for x in x_cands:
                    if can_place(x, y, w, h):
                        return x, y
            # Fallback: below everything
            max_y = max((py + ph + V_GAP for _, py, _, ph in placed), default=TOP_PAD)
            return LEFT_PAD, max_y

        for widget in self.device_widgets:
            x, y = find_position(widget.width(), widget.height())
            widget.move(x, y)
            widget.show()
            placed.append((x, y, widget.width(), widget.height()))

        # Derive row numbers from distinct y positions
        y_positions = sorted(set(y for _, y, _, _ in placed))
        y_to_row = {y: i for i, y in enumerate(y_positions)}
        for i, widget in enumerate(self.device_widgets):
            widget.row_num = y_to_row[placed[i][1]]

        if self.center:
            # Group widget indices by row, compute per-row centering offset
            rows = {}
            for i, widget in enumerate(self.device_widgets):
                rows.setdefault(widget.row_num, []).append(i)

            # Build row bands so tall widgets influence rows they overlap.
            y_positions = sorted(set(y for _, y, _, _ in placed))
            max_bottom = max(y + h for _, y, _, h in placed)
            row_bands = []
            for i, y in enumerate(y_positions):
                bottom = y_positions[i + 1] if i + 1 < len(y_positions) else max_bottom + V_GAP
                row_bands.append((y, bottom))

            for row_num, row_indices in rows.items():
                # Use all widgets overlapping the row band to compute the row's visual bounds.
                row_top, row_bottom = row_bands[row_num]
                overlap_indices = [
                    i for i, (_, y, _, h) in enumerate(placed)
                    if y < row_bottom and (y + h) > row_top
                ]
                if not overlap_indices:
                    continue
                row_left = min(placed[i][0] for i in row_indices)
                row_right = max(placed[i][0] + placed[i][2] for i in row_indices)

                # Center within the padded content area, clamping to avoid crossing padding.
                target_left = LEFT_PAD
                target_right = container_w - LEFT_PAD
                content_w = target_right - target_left
                row_w = row_right - row_left
                if row_w >= content_w:
                    offset = target_left - row_left
                else:
                    # Clamp further to avoid overlapping widgets from other rows that share this band.
                    row_center = (row_left + row_right) / 2
                    min_left = target_left
                    max_right = target_right
                    for i in overlap_indices:
                        if i in row_indices:
                            continue
                        b_left = placed[i][0]
                        b_right = placed[i][0] + placed[i][2]
                        blocker_center = (b_left + b_right) / 2
                        if row_center >= blocker_center:
                            min_left = max(min_left, b_right + H_GAP)
                        else:
                            max_right = min(max_right, b_left - H_GAP)

                    desired_offset = round((target_left + target_right - (row_left + row_right)) / 2)
                    new_left = row_left + desired_offset
                    new_right = row_right + desired_offset
                    if new_left < min_left:
                        desired_offset += min_left - new_left
                    if new_right > max_right:
                        desired_offset -= new_right - max_right
                    offset = desired_offset
                for i in row_indices:
                    w = self.device_widgets[i]
                    w.move(w.x() + offset, w.y())
                    px, py, pw, ph = placed[i]
                    placed[i] = (px + offset, py, pw, ph)

        self.group_label.setFixedSize(container_w - 10, 20)
        self.group_label.move(round((container_w - self.group_label.width()) / 2), 0)

        if placed:
            max_bottom = max(y + h for _, y, _, h in placed)
            new_height = max_bottom + 5
            height_changed = self.height() != new_height
            self.setFixedSize(container_w, new_height)
            self.parent.update()
            if height_changed:
                self._request_parent_layout()

    def _is_special_group(self):
        return self.group_name in ("Starred Devices", "Ungrouped Devices")

    def _get_room_control_host(self):
        widget = self
        while widget is not None:
            if hasattr(widget, "reload_schema"):
                return widget
            parent_attr = getattr(widget, "parent", None)
            if callable(parent_attr):
                widget = parent_attr()
            else:
                widget = parent_attr
        return None

    def _trigger_reload(self):
        room_control = self._get_room_control_host()
        if room_control is not None and hasattr(room_control, "reload_schema"):
            QTimer.singleShot(500, room_control.reload_schema)
        else:
            logging.error("Unable to trigger schema reload: RoomControlHost not found or missing reload_schema method")

    def _dialog_style(self):
        return (
            "QDialog { background-color: #000; color: #ffcd00; }"
            "QLabel { color: #ffcd00; }"
            "QLineEdit { background-color: #111; color: #ffcd00; border: 1px solid #ffcd00; }"
            "QDialogButtonBox QPushButton { background-color: #111; color: #ffcd00; border: 1px solid #ffcd00; padding: 4px 10px; }"
            "QDialogButtonBox QPushButton:pressed { background-color: #222; }"
        )

    def _text_dialog(self, title, label_text, value_text=""):
        dialog = QDialog(self.window())
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.setWindowTitle(title)
        dialog.setStyleSheet(self._dialog_style())
        target_width = max(400, round(self.window().width() * 0.5))
        dialog.resize(target_width, dialog.sizeHint().height())

        layout = QFormLayout(dialog)
        input_box = QLineEdit(dialog)
        input_box.setText(value_text)
        layout.addRow(label_text, input_box)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.setCenterButtons(True)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return input_box.text().strip()

    def _confirm_dialog(self, title, message):
        dialog = QDialog(self.window())
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.setWindowTitle(title)
        dialog.setStyleSheet(self._dialog_style())
        target_width = max(400, round(self.window().width() * 0.5))
        dialog.resize(target_width, dialog.sizeHint().height())

        layout = QFormLayout(dialog)
        layout.addRow(QLabel(message, dialog))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.setCenterButtons(True)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        return dialog.exec() == QDialog.DialogCode.Accepted

    def show_group_menu(self, pos):
        if self._is_special_group():
            return
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background-color: #222; color: #f0f0f0; }"
            "QMenu::item { padding: 6px 16px; }"
            "QMenu::item:selected { background-color: #3a3a3a; }"
        )
        menu.addAction("Rename Group").triggered.connect(self.rename_group)
        menu.addAction("Change Priority").triggered.connect(self.change_group_priority)
        menu.addAction("Delete Group").triggered.connect(self.delete_group)
        if self.sender() is self.group_label:
            global_pos = self.group_label.mapToGlobal(pos)
        else:
            global_pos = self.mapToGlobal(pos)
        menu.exec(global_pos)

    def rename_group(self):
        new_name = self._text_dialog("Rename Group", "New group name:", self.group_name or "")
        if new_name is None or new_name == "" or new_name == self.group_name:
            return
        room_control = self._get_room_control_host()
        schema_data = getattr(room_control, "schema_data", {}) if room_control is not None else {}
        group_priority = None
        for device in (widget.device for widget in self.device_widgets):
            group_priority = schema_data.get(device, {}).get("group_priority", group_priority)
        payload = {
            "group_name": self.group_name,
            "new_group_name": new_name,
            "group_priority": group_priority
        }
        request = QNetworkRequest(QUrl(f"{get_host()}/update_group_schema?interface_name=testing"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
        self.group_schema_manager.post(request, json.dumps(payload).encode("utf-8"))
        self._trigger_reload()

    def change_group_priority(self):
        new_priority_text = self._text_dialog("Group Priority", "New priority:")
        if new_priority_text is None or new_priority_text == "":
            return
        try:
            new_priority = int(new_priority_text)
        except ValueError:
            logging.error("Invalid group priority value entered")
            return
        payload = {
            "group_name": self.group_name,
            "group_priority": new_priority
        }
        request = QNetworkRequest(QUrl(f"{get_host()}/update_group_schema?interface_name=testing"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
        self.group_schema_manager.post(request, json.dumps(payload).encode("utf-8"))
        self._trigger_reload()

    def delete_group(self):
        if not self._confirm_dialog("Delete Group", f"Delete group '{self.group_name}'?"):
            return
        payload = {"group_name": self.group_name}
        request = QNetworkRequest(QUrl(f"{get_host()}/delete_group_schema?interface_name=testing"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setRawHeader(b"Cookie", bytes("auth=" + get_auth(), 'utf-8'))
        self.group_schema_manager.sendCustomRequest(request, b"DELETE", json.dumps(payload).encode("utf-8"))
        self._trigger_reload()

    def handle_group_schema_response(self, reply):
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                logging.error(f"Group schema error: {reply.errorString()}")
                return
            room_control = self._get_room_control_host()
            if room_control is not None and hasattr(room_control, "reload_schema"):
                QTimer.singleShot(500, room_control.reload_schema)
        except Exception as e:
            logging.error(f"Error handling group schema response: {e}")
            logging.exception(e)
        finally:
            reply.deleteLater()

    def _request_parent_layout(self):
        if self.pending_parent_layout:
            return
        self.pending_parent_layout = True

        def _run():
            self.pending_parent_layout = False
            room_control = self._get_room_control_host()
            if room_control is not None and hasattr(room_control, "layout_widgets"):
                room_control.layout_widgets(no_resize=True)
        QTimer.singleShot(0, _run)
