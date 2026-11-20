"""Settings shared by the desktop window and its themes."""
from PySide6.QtCore import QSettings


def desktop_settings():
    return QSettings(QSettings.defaultFormat(), QSettings.Scope.UserScope, 'SignalLab', 'Desktop071')
