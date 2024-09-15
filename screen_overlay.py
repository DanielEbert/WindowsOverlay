import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QGraphicsOpacityEffect
from PyQt5.QtGui import QPixmap, QImage, QCursor
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
import mss
import mss.tools

class OverlayWindow(QWidget):
    def __init__(self, capture_rect, display_position, sct, scaling: int = 1, show_mouse_position=False):
        super().__init__()

        self.scaling = scaling
        self.show_mouse_position = show_mouse_position
        self.sct = sct  # Shared mss instance

        # Store the capture rectangle and display position
        self.capture_rect = capture_rect  # (left, top, right, bottom)
        self.display_position = display_position  # (x, y)

        # Set up the window
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Make the window click-through
        self.move(*self.display_position)

        # Set up label to display the image
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.label.setStyleSheet("background: transparent;")

        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.95)
        self.label.setGraphicsEffect(opacity_effect)

        # Set the size of the window
        width = self.capture_rect[2] - self.capture_rect[0]
        height = self.capture_rect[3] - self.capture_rect[1] 
        width *= self.scaling
        height *= self.scaling
        self.resize(width, height)
        self.label.resize(width, height)

        # If show_mouse_position is True, create a mouse position window
        if self.show_mouse_position:
            self.mouse_window = MousePositionWindow()
            self.mouse_window.show()

    def update_image(self):
        # Capture the screen region using mss
        monitor = {
            "left": self.capture_rect[0],
            "top": self.capture_rect[1],
            "width": self.capture_rect[2] - self.capture_rect[0],
            "height": self.capture_rect[3] - self.capture_rect[1]
        }
        sct_img = self.sct.grab(monitor)
        # Convert the raw bytes to QImage
        img = QImage(sct_img.rgb, sct_img.width, sct_img.height, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)

        # Scale the pixmap to double its size
        scaled_pixmap = pixmap.scaled(
            pixmap.width() * self.scaling,
            pixmap.height() * self.scaling,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation  # Use Qt.FastTransformation for better performance if needed
        )

        # Set the pixmap to the label
        self.label.setPixmap(scaled_pixmap)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            if self.show_mouse_position:
                self.mouse_window.close()
            sys.exit()

class MousePositionWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: rgba(0, 0, 0, 0.5);")
        self.resize(150, 50)
        self.move(50, 50)  # Position of the mouse position window

        # Set up label to display the mouse position
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-size: 14px;")
        self.label.resize(150, 50)

        # Set up a timer to update the mouse position
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_mouse_position)
        self.timer.start(30)

    def update_mouse_position(self):
        pos = QPoint(QCursor.pos())
        x = pos.x()
        y = pos.y()
        self.label.setText(f"Mouse Position:\nX: {x}, Y: {y}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            sys.exit()

class Updater(QObject):
    # Create a custom signal to update all windows
    update_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

def main():
    app = QApplication(sys.argv)

    capture_rects = [
        (1356, 1369, 1668, 1420),  # 1-5
        (1772, 1369, 1880, 1420),  # utility
        (1994, 1369, 2042, 1420),  # elite
        (1424, 1306, 1512, 1344),  # special1
        (1614, 1306, 1654, 1344),  # special2
        (1494, 1287, 1586, 1298),  # swords
    ]

    display_positions = [
        (1356 + 186, 1369 - 500 + 100),  # 1-5
        (1772, 1369 - 500),  # utility
        (1994 - 114, 1369 - 500),  # elite
        (1424 + 24 + 100, 1306 - 500 + 70),  # special1
        (1614 + 24,       1306 - 500 + 70),  # special2
        (1494 + 142, 1287 - 500 + 140),  # swords
    ]

    scalings = [1, 1, 1, 1, 1, 2]

    show_mouse_position = False

    sct = mss.mss()  # Create a single mss instance

    windows = []

    for i, capture_rect in enumerate(capture_rects):
        window = OverlayWindow(capture_rect, display_positions[i], sct, scalings[i], show_mouse_position)
        window.show()
        windows.append(window)

    # Create a single timer to update all windows
    updater = Updater()

    def update_all_windows():
        for window in windows:
            window.update_image()

    updater.update_signal.connect(update_all_windows)

    timer = QTimer()
    timer.timeout.connect(updater.update_signal.emit)
    timer.start(30)  # Update every 30 ms (~33 FPS)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
