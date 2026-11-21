"""Locations and contextual usage for the general CAS worksheet."""
CAS_ROUTE=('Calculadora CAS','cas',0,None)
CAS_SEARCH='calculadora cas xcas algebra simbolica ecuaciones resolver derivadas integrales limites matrices simplificar factorizar desarrollar exacto numeros complejos assume supuestos exp2trig trig2exp'


def cas_sections():
    from .library_cas import BLOCKS
    from .function_reference import function_forms
    from .library_content import read_data

    formula_help = dict(article_id='reference:cas-arguments',title='Argumentos de comandos CAS',
        category='Matemática · Hoja CAS',route=None,reference=True,tools=[['cas',0]],
        blocks=[('Dónde escribirlos','Usá estas fórmulas en una celda de la Calculadora CAS. Cada comando indica qué poner en cada posición.')],
        forms=function_forms(read_data('cas.json','forms')))
    return [dict(title='Calculadora CAS',category='Matemática · Hoja CAS',route=CAS_ROUTE,blocks=BLOCKS),
            formula_help]


def cas_help_image():
    from PySide6.QtCore import QRectF,Qt
    from PySide6.QtGui import QImage,QPainter,QColor,QFont
    from .theme_tokens import COLORS as C
    image=QImage(960,300,QImage.Format.Format_ARGB32);image.fill(QColor(C['report']));p=QPainter(image)
    for index,(source,result,reading) in enumerate([('a := 2','r1 = 2',':= guarda una variable'),('factor(x^2 - a^2)','r2 = (x − 2)(x + 2)','x queda libre; a vale 2'),('subst(r2, x, 3)','r3 = 5','r2 reutiliza la salida anterior')]):
        y=12+index*94;p.setPen(QColor(C['accent']));p.setFont(QFont('Consolas',14));p.drawText(QRectF(18,y,570,30),str(index+1)+'  '+source)
        p.setPen(QColor(C['green']));p.setFont(QFont('Cambria',17));p.drawText(QRectF(60,y+33,530,45),result)
        p.setPen(QColor(C['muted']));p.setFont(QFont('Segoe UI',13));p.drawText(QRectF(625,y+16,310,62),Qt.TextFlag.TextWordWrap,reading)
    p.end();return image
