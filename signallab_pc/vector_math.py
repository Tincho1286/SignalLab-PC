"""Math paths rendered by Qt at the display's native resolution."""
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
import math
from matplotlib import rc_context
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import math_to_image
# Explicit import also packages the SVG writer in the portable executable.
from matplotlib.backends import backend_svg
from PySide6.QtCore import QByteArray,QRectF,QSizeF,QUrl
from PySide6.QtGui import QImage,QPixmap,QPainter,QPyTextObject,QTextDocument,QTextFormat
from PySide6.QtSvg import QSvgRenderer

@dataclass(frozen=True)
class VectorFormula:
    svg:bytes
    width:int
    height:int

@lru_cache(maxsize=256)
def render_latex(latex,size=15,color='#e1e7ee'):
    if len(latex)>12000:raise ValueError('Vista matemática extensa')
    stream=BytesIO()
    with rc_context({'mathtext.fontset':'stix','svg.fonttype':'path','savefig.transparent':True,'savefig.facecolor':'none','figure.facecolor':'none'}):
        math_to_image('$'+latex+'$',stream,format='svg',dpi=100,color=color,prop=FontProperties(family='STIXGeneral',size=size))
    data=stream.getvalue();renderer=QSvgRenderer(QByteArray(data))
    if not renderer.isValid():raise ValueError('No se pudo dibujar la fórmula')
    bounds=renderer.viewBoxF()
    # Match the existing logical text size (100 px/in), independently of DPR.
    width=max(1,round(bounds.width()*100/72));height=max(1,round(bounds.height()*100/72))
    if not math.isfinite(width*height) or width*height>16000000:raise ValueError('Vista matemática extensa')
    return VectorFormula(data,width,height)

class MathImageHandler(QPyTextObject):
    """Keep normal HTML image tags, painting formula SVG paths without a bitmap."""
    def __init__(self,document,formulas):
        super().__init__(document);self.formulas=formulas;self.renderers={}
        document.documentLayout().registerHandler(QTextFormat.ObjectTypes.ImageObject,self)
    def prune(self,names):
        for name in list(self.formulas):
            if name not in names:self.formulas.pop(name,None);self.renderers.pop(name,None)
    def image(self,document,name):
        value=document.resource(QTextDocument.ResourceType.ImageResource,QUrl(name))
        if isinstance(value,QPixmap):return value.toImage()
        if isinstance(value,(QByteArray,bytes)):return QImage.fromData(value)
        return value if isinstance(value,QImage) else QImage()
    def intrinsicSize(self,document,position,format):
        image_format=format.toImageFormat();name=image_format.name();formula=self.formulas.get(name)
        if formula:w,h=formula.width,formula.height
        else:
            image=self.image(document,name);ratio=image.devicePixelRatio() or 1;w,h=image.width()/ratio,image.height()/ratio
        width,height=image_format.width(),image_format.height()
        if width<=0:width=height*w/h if height>0 and h else w
        if height<=0:height=width*h/w if width>0 and w else h
        return QSizeF(max(0,width),max(0,height))
    def drawObject(self,painter,rect,document,position,format):
        name=format.toImageFormat().name();formula=self.formulas.get(name)
        painter.save()
        try:
            painter.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.TextAntialiasing|QPainter.RenderHint.SmoothPixmapTransform,True)
            if formula:
                cached=self.renderers.get(name)
                if cached is None or cached[0]!=formula.svg:
                    cached=(formula.svg,QSvgRenderer(QByteArray(formula.svg)));self.renderers[name]=cached
                cached[1].render(painter,QRectF(rect))
            else:
                image=self.image(document,name)
                if not image.isNull():painter.drawImage(QRectF(rect),image)
        finally:painter.restore()
