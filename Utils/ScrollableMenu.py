import time

from PyQt6.QtCore import QTimer, QElapsedTimer
from PyQt6.QtWidgets import QLabel
from loguru import logger as logging


class ScrollableMenu(QLabel):

    def __init__(self, parent=None, font=None):
        super().__init__(parent)
        self.parent = parent
        self.dragging = False
        self.focused = False
        if font is not None:
            self.font = font
        else:
            self.font = self.parent.get_font("JetBrainsMono-Bold")

        # Scroll related variables
        self.scroll_offset = 0
        self.scroll_start = 0
        self.scroll_velocity = 0  # Pixels per second
        self.scroll_velocity_decay = 0.9  # Percentage of velocity to keep each frame
        self.scroll_max_velocity = 100  # Pixels per second
        self.scroll_total_offset = 0
        self.last_scroll = time.time()

        self.scroll_motion_timer = QTimer(self)
        self.scroll_motion_timer.timeout.connect(self.scroll_motion)

    def set_focus(self, focus):
        # timer = QElapsedTimer()
        # timer.start()
        self.focused = focus
        self.resizeEvent(None)
        self.layout_widgets()
        # logging.debug(f"Setting focus to {focus} took {timer.elapsed()}ms")

    def mousePressEvent(self, event):
        try:
            if not self.focused:
                return
            self.dragging = True
            self.scroll_start = event.pos().y()
            self.last_scroll = time.time()
            self.scroll_total_offset = 0
            self.scroll_motion_timer.stop()
        except Exception as e:
            logging.error(f"Error handling mouse press event: {e}")
            logging.exception(e)

    def mouseMoveEvent(self, ev):
        try:
            if self.dragging:
                # Offset the entire room control host by the difference in the y position
                self.scroll_offset += ev.pos().y() - self.scroll_start
                self.scroll_total_offset += self.scroll_offset
                # Calculate the velocity of the scroll
                t_delta = time.time() - self.last_scroll
                if t_delta > 0:  # Avoid division by zero
                    self.scroll_velocity = (ev.pos().y() - self.scroll_start) / t_delta
                    self.scroll_start = ev.pos().y()
                    # Move the widgets by the scroll offset
                    self.move_widgets(self.scroll_offset)
        except Exception as e:
            logging.error(f"Error handling mouse move event: {e}")
            logging.exception(e)

    def mouseReleaseEvent(self, ev):
        try:
            self.dragging = False
            # Start the scroll motion timer to decay the scroll velocity and move the widgets
            self.last_scroll = time.time()
            self.scroll_total_offset += self.scroll_offset
            # Check if the total scroll motion was less than 5 pixels
            # logging.debug(f"Scroll total offset: {self.scroll_total_offset}")
            if abs(self.scroll_total_offset) < 5:
                # If it was, emit the click event
                # logging.debug("Emitting click event")
                super().mouseReleaseEvent(ev)
            else:
                self.scroll_motion_timer.start(round(1000 / 60))
        except Exception as e:
            logging.error(f"Error handling mouse release event: {e}")
            logging.exception(e)

    def wheelEvent(self, a0) -> None:
        try:
            if not self.focused:
                return
            self.scroll_offset += a0.angleDelta().y() / 5
            self.move_widgets(self.scroll_offset)
        except Exception as e:
            logging.error(f"Error handling wheel event: {e}")
            logging.exception(e)

    def scroll_motion(self):
        try:
            # Decay the scroll velocity
            self.scroll_velocity = max(-self.scroll_max_velocity, min(self.scroll_max_velocity, self.scroll_velocity))
            self.scroll_velocity *= self.scroll_velocity_decay
            # Move the widgets by the scroll velocity
            self.scroll_offset += self.scroll_velocity
            self.move_widgets(self.scroll_offset)
            # If the scroll velocity is less than 1 pixel per second, stop the scroll motion timer
            if abs(self.scroll_velocity) < 1:
                self.scroll_motion_timer.stop()
        except Exception as e:
            logging.error(f"Error handling scroll motion: {e}")
            logging.exception(e)

    def move_widgets(self, y):
        raise NotImplementedError("This method must be implemented by the child class")

    def layout_widgets(self):
        raise NotImplementedError("This method must be implemented by the child class")
