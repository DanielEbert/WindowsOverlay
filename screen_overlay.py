import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QGraphicsOpacityEffect
from PyQt5.QtGui import QPixmap, QImage, QCursor, QPainter, QPen
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
import mss
import mss.tools

class OverlayWindow(QWidget):
    def __init__(self, capture_rect, display_position, sct, scaling: int = 1, show_mouse_position=False):
        super().__init__()

        self.scaling = scaling
        self.show_mouse_position = show_mouse_position
        self.sct = sct

        self.capture_rect = capture_rect  # (left, top, right, bottom)
        self.display_position = display_position  # (x, y)

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

        width = self.capture_rect[2] - self.capture_rect[0]
        height = self.capture_rect[3] - self.capture_rect[1] 
        width = round(width * self.scaling)
        height = round(height * self.scaling)
        self.resize(width, height)
        self.label.resize(width, height)

        if self.show_mouse_position:
            self.mouse_window = MousePositionWindow(sct)
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

        scaled_pixmap = pixmap.scaled(
            round(pixmap.width() * self.scaling),
            round(pixmap.height() * self.scaling),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation  # Qt.FastTransformation for better performance if needed
        )

        self.label.setPixmap(scaled_pixmap)

    # def keyPressEvent(self, event):
    #     if event.key() == Qt.Key_Escape:
    #         self.close()
    #         if self.show_mouse_position:
    #             self.mouse_window.close()
    #         sys.exit()


class BorderOverlay(QWidget):
    def __init__(self, target_position, target_color_rgb, overlay_position, sct, color=Qt.red, thickness=3, invert_condition = False) -> None:
        super().__init__()

        self.target_position = target_position
        self.target_color_rgb = target_color_rgb
        self.sct = sct
        self.invert_condition = invert_condition

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Make the window click-through
        self.move(overlay_position[0], overlay_position[1])

        overlay_size = (overlay_position[2] - overlay_position[0], overlay_position[3] - overlay_position[1])

        self.resize(*overlay_size)

        # Border properties
        self.color = color
        self.thickness = thickness

        self.visible = False
    
    def update_border(self):
        pixel_rgb = self.sct.grab({'left': self.target_position[0], 'top': self.target_position[1], 'width': 1, 'height': 1}).pixel(0, 0)

        prev_visible = self.visible
        self.visible = pixel_rgb == self.target_color_rgb if not self.invert_condition else pixel_rgb != self.target_color_rgb

        if prev_visible != self.visible:
            self.update()

    def paintEvent(self, event):
        if not self.visible:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Set pen for border
        pen = QPen(self.color, self.thickness)
        painter.setPen(pen)
        # Draw rectangle border
        rect = self.rect().adjusted(round(self.thickness/2), round(self.thickness/2), round(-self.thickness/2), round(-self.thickness/2))
        painter.drawRect(rect)
        painter.end()


class MousePositionWindow(QWidget):
    def __init__(self, sct):
        super().__init__()

        self.sct = sct

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: rgba(0, 0, 0, 0.5);")
        self.resize(150, 50)
        self.move(50, 50)  # Position of the mouse position window

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-size: 14px;")
        self.label.resize(150, 50)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_mouse_position)
        self.timer.start(30)

    def update_mouse_position(self):
        pos = QPoint(QCursor.pos())
        x = pos.x()
        y = pos.y()

        # 1642, 1378
        # pixel = self.sct.grab({'left': 1642, 'top': 1378, 'width': 1, 'height': 1}).pixel(0, 0)

        #1582, 1300
        # full sword: (150, 124, 216)

        # print(x, y, pixel)

        self.label.setText(f"Mouse Position:\nX: {x}, Y: {y}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            sys.exit()

class Updater(QObject):
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
        (1424 + 24 + 70, 1306 - 500 + 60),  # special1
        (1614 + 24 - 7,       1306 - 500 + 60),  # special2
        (1494 + 142, 1287 - 500 + 140),  # swords
    ]

    scalings = [1, 1, 1, 1.3, 1.3, 2]

    show_mouse_position = True

    overlay_base_pos = (1480, 530, 1974, 1050)

    sct = mss.mss()

    sword_border_overlay = BorderOverlay(
        (1582, 1297),
        (150, 124, 216),
        (overlay_base_pos[0] - 10, overlay_base_pos[1] - 10, overlay_base_pos[2] + 10, overlay_base_pos[3] + 10),
        sct
    )
    sword_border_overlay.show()

    e_border_overlay = BorderOverlay(
        (1642, 1378),
        (0, 0, 0),
        overlay_base_pos,
        sct,
        Qt.blue,
        invert_condition=True
    )
    e_border_overlay.show()

    windows = []

    for i, capture_rect in enumerate(capture_rects):
        window = OverlayWindow(capture_rect, display_positions[i], sct, scalings[i], show_mouse_position)
        window.show()
        windows.append(window)

    updater = Updater()

    def update_all_windows():
        for window in windows:
            window.update_image()
        
        sword_border_overlay.update_border()
        e_border_overlay.update_border()

    updater.update_signal.connect(update_all_windows)

    timer = QTimer()
    timer.timeout.connect(updater.update_signal.emit)
    timer.start(30)  # 30 ms rate

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
