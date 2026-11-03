"""Shared local wallpaper behind optional translucent navigation surfaces."""
from pathlib import Path
import os,shutil,tempfile,hashlib,re
from PySide6.QtCore import Qt,QRectF,QSize,QStandardPaths
from PySide6.QtGui import QImageReader,QPixmap,QPainter,QColor
from PySide6.QtWidgets import QWidget,QApplication

_cache={}


def read_photo(path):
    reader=QImageReader(str(path));reader.setAutoTransform(True)
    if not reader.canRead():raise ValueError('No se pudo leer la foto. Elegí una imagen PNG, JPEG, WebP o BMP válida.')
    size=reader.size()
    if not size.isValid():raise ValueError('La imagen no tiene dimensiones válidas.')
    from .resources import ensure_working_set
    ensure_working_set(size.width()*size.height(),bytes_per_sample=4,live_arrays=3)
    screens=QApplication.screens();width=max((round(s.size().width()*s.devicePixelRatio()) for s in screens),default=1920);height=max((round(s.size().height()*s.devicePixelRatio()) for s in screens),default=1080)
    scaled=size.scaled(QSize(width,height),Qt.AspectRatioMode.KeepAspectRatioByExpanding)
    if scaled.width()<size.width() and scaled.height()<size.height():reader.setScaledSize(scaled)
    image=reader.read()
    if image.isNull():raise ValueError('No se pudo decodificar la imagen: '+reader.errorString())
    return QPixmap.fromImage(image)


def pixmap(path):
    if not path:return QPixmap()
    try:
        p=Path(path);signature=(str(p),p.stat().st_mtime_ns,p.stat().st_size)
        if signature not in _cache:
            value=read_photo(p);_cache.clear();_cache[signature]=value
        return _cache[signature]
    except (OSError,ValueError,MemoryError):return QPixmap()


def save_photo(source,directory=None):
    """Copy only into the app's own data directory; never modify the original."""
    if not source:return ''
    path=Path(source).expanduser().resolve();read_photo(path)
    folder=Path(directory) if directory is not None else Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericDataLocation))/'SignalLab'/'appearance'
    folder=folder.resolve();folder.mkdir(parents=True,exist_ok=True)
    suffix=path.suffix.lower()
    if suffix not in ('.png','.jpg','.jpeg','.webp','.bmp'):suffix='.img'
    with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()[:16]
    target=folder/('background-'+digest+suffix)
    if path==target:return str(target)
    handle,name=tempfile.mkstemp(prefix='background-',suffix='.tmp',dir=folder);os.close(handle)
    temporary=Path(name)
    try:shutil.copyfile(path,temporary);os.replace(temporary,target)
    finally:
        if temporary.exists():temporary.unlink()
    _cache.clear()
    return str(target)


def clean_previous(current):
    path=Path(current).resolve() if current else None;folder=(Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericDataLocation))/'SignalLab'/'appearance').resolve()
    if path is not None and path.parent!=folder:return
    if not folder.exists():return
    for old in folder.iterdir():
        if re.fullmatch(r'background(?:-[0-9a-f]{16})?\.(png|jpg|jpeg|webp|bmp|img)',old.name) and old!=path and old.is_file() and old.resolve().parent==folder:
            try:old.unlink()
            except OSError:pass


def paint(painter,rect,colors,config):
    painter.fillRect(rect,QColor(colors['window']));photo=pixmap(config.get('photo',''))
    if photo.isNull():return
    factor=(max if config.get('fit')=='cover' else min)(rect.width()/photo.width(),rect.height()/photo.height())
    width,height=photo.width()*factor,photo.height()*factor
    destination=QRectF(rect.x()+(rect.width()-width)/2,rect.y()+(rect.height()-height)/2,width,height)
    painter.save();painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);painter.setOpacity(config.get('opacity',35)/100)
    painter.drawPixmap(destination,photo,QRectF(photo.rect()));painter.restore()


class BackgroundSurface(QWidget):
    def paintEvent(self,event):
        from .theme_tokens import COLORS
        from . import theme_presets
        painter=QPainter(self)
        config=theme_presets.CUSTOM if theme_presets.CURRENT=='custom' else {}
        if not (config.get('photo') and getattr(self.window(),'_signallab_wallpaper_host',False)):
            paint(painter,QRectF(self.rect()),COLORS,config)
        painter.end()


def paint_window(window):
    from . import theme_presets
    from .theme_tokens import COLORS
    if theme_presets.CURRENT!='custom' or not theme_presets.CUSTOM.get('photo'):return
    painter=QPainter(window);paint(painter,QRectF(window.rect()),COLORS,theme_presets.CUSTOM);painter.end()


def panel_color(color,opacity):
    value=QColor(color);value.setAlpha(round(255*opacity/100));return value


def stylesheet():
    from . import theme_presets
    from .theme_tokens import COLORS
    if theme_presets.CURRENT!='custom' or not theme_presets.CUSTOM.get('photo'):return ''
    opacity=theme_presets.CUSTOM.get('surface_opacity',100)
    def shade(role):
        value=panel_color(COLORS[role],opacity)
        return 'rgba('+','.join(str(v) for v in value.getRgb())+')'
    # Containers reveal the image painted once by the main window. Inputs,
    # reports, figures and popup lists retain their own reading surfaces.
    return '\n'.join([
        'QWidget#desktop,QWidget#workspaceWallpaper {background:transparent;}',
        'QWidget#desktop > QLabel,QWidget#workspaceWallpaper > QLabel {background:'+shade('window')+';padding:4px;border-radius:5px;}',
        'QWidget#documentHeading {background:'+shade('chrome')+';}',
        'QWidget#explorerPanel {background:'+shade('chrome')+';}',
        'QWidget#explorerPanel QTreeWidget {background:transparent;}',
        'QToolBar,QMenuBar,QStatusBar,QDockWidget::title {background:'+shade('chrome')+';}',
        'QFrame#browserSection,QGroupBox {background:'+shade('panel')+';}',
        'QFrame#welcomeCard {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 '+shade('selected')+',stop:.65 '+shade('panel')+',stop:1 '+shade('chrome')+');}',
        'QScrollArea > QWidget > QWidget,QTabWidget::pane,QTabBar#documents {background:transparent;}',
        'QTabBar::tab {background:'+shade('chrome')+';}',
        'QTabBar::tab:selected,QTabBar#documents::tab:selected {background:'+shade('panel')+';}',
    ])


def refresh(window):
    from PySide6.QtWidgets import QScrollArea
    # Some QScrollArea viewports fill their palette before their contents.
    # Restore that flag when leaving the photo theme.
    from . import theme_presets
    active=theme_presets.CURRENT=='custom' and bool(theme_presets.CUSTOM.get('photo'))
    for scroll in window.findChildren(QScrollArea):
        viewport=scroll.viewport()
        if active:
            if not hasattr(viewport,'_signallab_original_fill'):viewport._signallab_original_fill=viewport.autoFillBackground()
            viewport.setAutoFillBackground(False)
        elif hasattr(viewport,'_signallab_original_fill'):
            viewport.setAutoFillBackground(viewport._signallab_original_fill);del viewport._signallab_original_fill
    window.update()
