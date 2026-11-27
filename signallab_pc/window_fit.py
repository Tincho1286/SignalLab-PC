"""Keep normal desktop windows inside the usable area of their monitor."""

from PySide6.QtCore import QEvent, QObject, QSize, QTimer
from shiboken6 import isValid


_DEFAULT_WINDOW_MAXIMUM = QSize(16777215, 16777215)


class WatchWorkArea(QObject):
    def __init__(self, window, fit):
        super().__init__(window)
        self.window = window
        self.handle = None
        self.screen = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(fit)
        window.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Show:
            handle = self.window.windowHandle()
            if handle is not self.handle:
                if self.handle is not None and isValid(self.handle):
                    self.handle.screenChanged.disconnect(self.track_screen)
                self.handle = handle
                if handle is not None:
                    handle.screenChanged.connect(self.track_screen)
            self.track_screen(self.window.screen())
        elif event.type() == QEvent.Type.WindowStateChange:
            self.schedule()
        return False

    def track_screen(self, screen):
        if screen is not self.screen:
            if self.screen is not None and isValid(self.screen):
                self.screen.availableGeometryChanged.disconnect(self.schedule)
            self.screen = screen
            if screen is not None:
                screen.availableGeometryChanged.connect(self.schedule)
        self.schedule()

    def schedule(self, *_):
        self.timer.start(0)


def fit_window(window, preferred_minimum):
    area = window.screen().availableGeometry()
    handle = window.windowHandle()
    border = (window.frameSize() - window.size()).expandedTo(QSize(0, 0))
    if handle is not None:
        margins = handle.frameMargins()
        border = border.expandedTo(QSize(margins.left() + margins.right(), margins.top() + margins.bottom()))
    capacity = (area.size() - border).expandedTo(QSize(1, 1))
    window.setMinimumSize(preferred_minimum.boundedTo(capacity))
    normal = not (window.isMaximized() or window.isFullScreen())
    # Keep layout reflow from growing a window beyond a short work area.
    window.setMaximumSize(capacity if normal and area.height() < 440 else _DEFAULT_WINDOW_MAXIMUM)
    if not normal:
        return
    window.resize(window.size().boundedTo(capacity))
    frame = window.frameGeometry()
    x = max(area.left(), min(frame.left(), area.right() - frame.width() + 1))
    y = max(area.top(), min(frame.top(), area.bottom() - frame.height() + 1))
    if (x, y) != (frame.left(), frame.top()):
        window.move(x, y)
