"""Native vector accents and clear task cards for the Studio home screen."""
import math
from PySide6.QtCore import Qt,QPointF,QSize
from PySide6.QtGui import QPainter,QPainterPath,QColor,QLinearGradient,QPen
from PySide6.QtWidgets import QFrame,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QSizePolicy
from .theme_tokens import COLORS as C
from .design import icon


class StudioHero(QFrame):
    def __init__(self):super().__init__();self.setObjectName('studioHero')
    def paintEvent(self,event):
        super().paintEvent(event);p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);rect=self.rect().adjusted(1,1,-1,-1);p.setPen(Qt.PenStyle.NoPen);gradient=QLinearGradient(0,0,self.width(),self.height());start,end=QColor(C['selected']),QColor(C['panel'])
        from . import theme_presets
        if theme_presets.CURRENT=='custom' and theme_presets.CUSTOM.get('photo'):
            from .wallpaper import panel_color
            start,end=panel_color(start.name(),theme_presets.CUSTOM.get('surface_opacity',100)),panel_color(end.name(),theme_presets.CUSTOM.get('surface_opacity',100))
        gradient.setColorAt(0,start);gradient.setColorAt(1,end);p.setBrush(gradient);p.drawRoundedRect(rect,26,26)
        if self.width()>700:
            left=self.width()*.60;right=self.width()-30;axis_y=88;scale=38;color=QColor(C['green']);color.setAlpha(90);p.setPen(QPen(color,1));p.drawLine(QPointF(left,axis_y),QPointF(right,axis_y));path=QPainterPath()
            for i in range(181):
                x=left+(right-left)*i/180;y=axis_y-scale*math.sin(i/180*math.pi*4)
                if i:path.lineTo(x,y)
                else:path.moveTo(x,y)
            p.setPen(QPen(color,2));p.drawPath(path);color=QColor(C['purple']);color.setAlpha(150);p.setPen(QPen(color,2));p.setBrush(color)
            for i in range(16):
                x=left+(right-left)*i/15;y=axis_y-scale*math.sin(i/15*math.pi*4);p.drawLine(QPointF(x,axis_y),QPointF(x,y));p.drawEllipse(QPointF(x,y),3,3)
        p.end()


class QuickAction(QPushButton):
    def __init__(self,title,description,symbol,role,callback):
        super().__init__();self.symbol=symbol;self.role=role;self.setObjectName('quickAction');self.setAccessibleName(title);self.setCursor(Qt.CursorShape.PointingHandCursor);self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred);root=QHBoxLayout(self);root.setContentsMargins(16,16,16,16);root.setSpacing(12);badge=QLabel();self.badge=badge;badge.setPixmap(icon(symbol,C[role]).pixmap(30,30));badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);root.addWidget(badge);copy=QVBoxLayout();copy.setSpacing(4)
        for text,name in ((title,'quickTitle'),(description,'quickDescription')):
            label=QLabel(text);label.setObjectName(name);label.setWordWrap(True);label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents);copy.addWidget(label)
        root.addLayout(copy,1);self.clicked.connect(callback)
    def sizeHint(self):return self.layout().sizeHint().expandedTo(QSize(170,82))
    def refresh_theme(self):self.badge.setPixmap(icon(self.symbol,C[self.role]).pixmap(30,30))
