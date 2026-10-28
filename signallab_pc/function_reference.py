"""Referencia verificada contra engine._FUNCS y symbolic.FUNCTIONS."""

def function_sections():
    pages=[]
    def add(title,blocks,illustration=None):
        pages.append(dict(title=title,category='Funciones de las fórmulas',route=None,purpose=blocks[0][1],usage='',blocks=blocks,reference=True,illustration=illustration))
    add('Guía de funciones y sintaxis',[('Lectura','')],None)
    add('Impulse · impulso discreto',[('Lectura','')],'impulse')
    add('Step y Heaviside · escalón unitario',[('Lectura','')],'step')
    add('Sinc · seno cardinal',[('Lectura','')],'sinc')
    add('Sin, Cos y funciones trigonométricas',[('Lectura','')],None)
    add('Exp, Log, Ln y Sqrt',[('Lectura','')],None)
    add('Abs, Re, Im y Conj · números complejos',[('Lectura','')],None)
    add('Sign, Floor, Ceil y Ceiling',[('Lectura','')],None)
    add('Where y condiciones · funciones por tramos',[('Lectura','')],None)
    add('DiracDelta y Heaviside · cálculo simbólico',[('Lectura','')],None)
    add('Coeficientes · constantes, pi y notación científica',[('Lectura','')],None)
    from .library_concepts import FUNCTION_BLOCKS
    if len(pages)!=len(FUNCTION_BLOCKS):raise ValueError("Revisar correspondencia de páginas de funciones.")
    for page,blocks in zip(pages,FUNCTION_BLOCKS):page.update(blocks=blocks,purpose=blocks[0][1])
    return pages


def reference_diagram(kind):
    import numpy as np
    from PySide6.QtCore import Qt,QRectF,QPointF,QLineF
    from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont,QPainterPath
    image=QImage(900,320,QImage.Format.Format_ARGB32);image.fill(QColor('#1b2027'));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setFont(QFont('Segoe UI',13));p.setPen(QColor('#e1e7ee'))
    title={'impulse':'impulse(n): sólo n = 0 tiene amplitud 1','step':'step(n): el punto n = 0 está incluido','sinc':'sinc(t) = sin(πt)/(πt), con valor 1 en t = 0'}[kind]
    p.drawText(QRectF(35,12,830,40),Qt.AlignmentFlag.AlignLeft,title)
    def xy(x,y):return (450+85*x,225-140*y)
    p.setPen(QPen(QColor('#778493'),1));p.drawLine(QLineF(60,225,840,225));p.drawLine(QLineF(450,65,450,270))
    p.setPen(QPen(QColor('#8ab6df'),3));p.setBrush(QColor('#8ab6df'))
    if kind=='sinc':
        path=QPainterPath()
        for i,x in enumerate(np.linspace(-4,4,401)):
            point=xy(x,np.sinc(x))
            if i==0:path.moveTo(*point)
            else:path.lineTo(*point)
        p.setBrush(Qt.BrushStyle.NoBrush);p.drawPath(path)
    else:
        for n in range(-4,5):
            x,y=xy(n,float(n==0) if kind=='impulse' else float(n>=0));p.drawLine(QLineF(x,225,x,y));p.drawEllipse(QPointF(x,y),5,5)
    p.setPen(QColor('#e1e7ee'))
    for n in range(-4,5):p.drawText(QRectF(xy(n,0)[0]-15,240,40,30),Qt.AlignmentFlag.AlignLeft,str(n))
    p.drawText(QRectF(420,75,25,25),Qt.AlignmentFlag.AlignLeft,'1');p.drawText(QRectF(780,275,70,25),Qt.AlignmentFlag.AlignLeft,'t' if kind=='sinc' else 'n');p.end();return image
