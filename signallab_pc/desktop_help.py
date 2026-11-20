"""A short, illustrated introduction to the common scientific workspace."""
ARTICLE_ID='reference:Interfaz de trabajo'
FIGURES_ID='reference:Gráficos y cursores'
LIMITS_ID='reference:Valores por continuidad'
LIMITS_HEADING='Indeterminaciones y valores por continuidad'


def sections():
    return [
        dict(title='Interfaz de trabajo',article_id=ARTICLE_ID,route=None,category_label='Primeros pasos',blocks=[
            ('Encontrá la herramienta','Abrí Herramientas para elegir un área. Con Ctrl+K podés buscar por nombre o concepto. Las pestañas superiores te llevan a los cálculos que ya abriste.'),
            ('Cargá los datos y calculá','Elegí la variante debajo del título, por ejemplo Directa o Inversa. Cada variante conserva su propia entrada. Si cambiás a una vista compatible, podés copiarle la definición anterior. Después elegí Calcular o presioná Ctrl+Enter.'),
            ('Leé el último resultado','El informe reúne las fórmulas o valores obtenidos y las condiciones de ese cálculo. Si editás la entrada, el aviso Datos modificados indica que la salida todavía corresponde a la entrada anterior. Recalculá para actualizarla.'),
            ('Precisión de la lectura','Las tablas y las fórmulas numéricas pueden mostrar menos cifras que las almacenadas. Para continuar un cálculo, reutilizá el resultado o exportá sus datos. En una función por tramos se usa la primera condición que se cumple.'),
            ('Reutilizá o guardá','Junto al resultado están Abrir gráfico, Usar… en, Enviar a CAS y Exportar. Cuando hay varias salidas, elegí la que querés usar. Resultados conserva las señales, sistemas y expresiones junto con sus condiciones.'),
            ('Ajustá el espacio de lectura','En una ventana angosta, Alt+1 abre los datos y Alt+2 el resultado. Ctrl+Mayús+R amplía el informe. Para consultar el significado de un campo o el método de cálculo, abrí Ayuda o presioná F1.'),
        ],related=[(FIGURES_ID,'Gráficos y cursores')]),
        dict(title='Gráficos y cursores',article_id=FIGURES_ID,route=None,category_label='Primeros pasos',blocks=[
            ('Elegí la figura','Abrir gráfico muestra la figura en una ventana independiente. La flecha del botón permite elegir entre las figuras del resultado. Si cerrás una figura, podés volver a abrirla desde el mismo botón.'),
            ('Leé el eje antes de comparar','Los tallos representan muestras independientes. En una DFT, k identifica un coeficiente. En una DTFT, ω recorre un eje continuo en rad/muestra. Un panel de fase principal puede presentar saltos de 2π.'),
            ('Medí con dos cursores','Mové el puntero para leer una traza. Un clic fija A y el siguiente fija B. La tabla muestra sus diferencias en los paneles con ejes compatibles. Podés arrastrar un cursor fijo o liberarlos con Esc. En el editor de polos y ceros usá los botones A/B para conservar el clic de diseño.'),
            ('Inspeccioná una curva','Curvas y medidas permite consultar la definición guardada y buscar extremos entre los puntos calculados. Elegí la vista, toda la curva o el tramo entre A y B. Seleccioná una fila para marcarla. Los extremos entre puntos requerirían un análisis adicional.'),
            ('Ajustá la escala','En Escala vertical, activá Detalle vertical para ver variaciones pequeñas. Su umbral visual es 10⁻¹⁰ de la escala de referencia, con un mínimo de 1 para esa referencia. Ajustar rango permite elegir límites manuales o volver al rango completo de dB para ver los nulos representables.'),
        ]),
        dict(title='Valores por continuidad',article_id=LIMITS_ID,route=None,category_label='Primeros pasos',blocks=[
            ('Cuándo se completa un valor','En sin(n)/n, sustituir n=0 da 0/0. SignalLab usa 1 en ese punto porque los límites por ambos lados coinciden y son finitos. El informe registra el punto y el valor usado.'),
            ('Cómo indicar otro valor','Para una secuencia, esta extensión es una convención al ingresar la fórmula. Si querés otro valor en n=0, definilo en Por tramos. Los valores que ya están definidos se conservan, incluido sinc(0)=1.'),
            ('Cuándo queda indefinido','Un polo, un límite infinito o dos límites laterales distintos impiden completar el punto por continuidad. Consultá las condiciones del resultado antes de reutilizar la expresión.'),
        ]),
    ]


def workspace_image():
    from PySide6.QtCore import Qt,QRectF
    from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
    from .theme_tokens import COLORS as C

    image=QImage(960,480,QImage.Format.Format_ARGB32_Premultiplied);image.fill(QColor(C['report']));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,role='text',size=12):
        p.setPen(QColor(C[role]));p.setFont(QFont('Segoe UI',size));p.drawText(QRectF(x,y,w,h),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,value)
    def box(x,y,w,h,role='border',fill='panel'):
        p.setPen(QPen(QColor(C[role]),1.5));p.setBrush(QColor(C[fill]));p.drawRoundedRect(QRectF(x,y,w,h),12,12)
    text(20,6,920,42,'Una disposición común para las herramientas',size=17)
    box(24,62,912,55);text(40,69,480,40,'Herramienta · opciones del cálculo','muted');box(650,72,158,35,'purple','selected');text(650,72,158,35,'Calcular','purple');text(818,72,103,35,'Ayuda · F1','green')
    box(24,134,303,245,'green');text(39,145,273,40,'Datos de entrada','green',15);text(49,198,253,150,'Definición\n\nEje y unidades\n\nParámetros del cálculo')
    box(343,134,593,245,'blue');text(358,145,563,40,'Resultado','blue',15)
    for x,width,label,role in [(360,119,'Abrir gráfico','purple'),(488,155,'Usar… en','green'),(652,119,'Enviar a CAS','blue'),(780,138,'Exportar…','amber')]:
        box(x,199,width,44,role,'input');text(x,202,width,38,label,role,10)
    text(360,258,558,100,'Informe · tablas · vistas del resultado\n\nEl aviso de actualización acompaña al informe.','muted')
    text(24,397,265,55,'Con menos ancho:','muted');box(307,405,293,40,'green','selected');text(307,405,293,40,'Datos de entrada · Alt+1','green');box(614,405,293,40,'blue');text(614,405,293,40,'Resultado · Alt+2','blue')
    p.end();return image
