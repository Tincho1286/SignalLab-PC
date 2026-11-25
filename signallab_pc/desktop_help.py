"""A short, illustrated introduction to the common scientific workspace."""
ARTICLE_ID='reference:Interfaz de trabajo'
FIGURES_ID='reference:Gráficos y cursores'
LIMITS_ID='reference:Valores por continuidad'
LIMITS_HEADING='Indeterminaciones y valores por continuidad'


def sections():
    return [
        dict(title='Interfaz de trabajo',article_id=ARTICLE_ID,route=None,category_label='Primeros pasos',blocks=[
            ('Encontrá la herramienta','Elegí un área en la barra lateral y filtrá su catálogo. Ctrl+K abre Acceso rápido desde cualquier página. Podés buscar una variante, como DTFT inversa algebraica, volver a un documento abierto o ingresar el nombre de un resultado de la sesión.'),
            ('Guardá tus variantes frecuentes','La estrella junto al título agrega la variante actual a Favoritos. En Inicio y en Acceso rápido podés volver a abrirla con un clic. Las entradas se guardan por separado en la sesión.'),
            ('Cargá los datos y calculá','El menú Variante está debajo del título. Podés abrirlo con Alt+V desde Datos de entrada o Resultado. Cada variante conserva sus parámetros y su último cálculo. Usá Copiar entrada si querés traer datos compatibles de la variante anterior. Para calcular, presioná Ctrl+Enter.'),
            ('Escribí una fórmula','Funciones muestra plantillas para la variable del campo. Por ejemplo, en una secuencia podés insertar Step(n). Sintaxis y argumentos abre la referencia para completar la fórmula. Para una función por tramos, Vista matemática muestra la definición que se va a usar.'),
            ('Leé el último resultado','El informe reúne las fórmulas o valores obtenidos y las condiciones de ese cálculo. Si editás la entrada, el aviso Datos modificados indica que la salida todavía corresponde a la entrada anterior. Recalculá para actualizarla.'),
            ('Precisión de la lectura','Las tablas y las fórmulas numéricas pueden mostrar menos cifras que las almacenadas. Para continuar un cálculo, reutilizá el resultado o exportá sus datos. En una función por tramos se usa la primera condición que se cumple.'),
            ('Reutilizá o guardá','Junto al resultado están Abrir gráfico, Usar… en, Enviar a CAS y Exportar. En Resultados, Abrir herramienta vuelve a la operación. Recorrido muestra los datos de origen y los resultados que los usaron.'),
            ('Ajustá el espacio de lectura','En una ventana angosta, elegí Datos de entrada o Resultado. Las vistas del resultado se agrupan en el selector Vista cuando hace falta espacio. Alt+1 abre los datos, Alt+2 lleva al resultado y Ctrl+Mayús+R lo amplía.'),
            ('Consultá la ayuda','F1 abre la guía de la herramienta. En este artículo lleva a sus apartados y Volver al cálculo recupera la herramienta con los datos que ya cargaste.'),
        ],related=[(FIGURES_ID,'Gráficos y cursores')]),
        dict(title='Gráficos y cursores',article_id=FIGURES_ID,route=None,category_label='Primeros pasos',blocks=[
            ('Elegí la figura','Abrir gráfico muestra la figura en una ventana independiente. La flecha del botón ofrece las figuras disponibles y, cuando el gráfico se obtiene de una fórmula, permite ajustar el intervalo. Solo figura o F11 alterna entre la vista amplia y los controles.'),
            ('Leé el eje antes de comparar','Los tallos representan muestras independientes. En una DFT, k identifica un coeficiente. En una DTFT, ω recorre un eje continuo en rad/muestra. Un panel de fase principal puede presentar saltos de 2π.'),
            ('Medí con dos cursores','Mové el puntero para leer una traza. Un clic fija A y el siguiente fija B. La tabla muestra sus diferencias en los paneles con ejes compatibles. Podés arrastrar un cursor fijo o liberarlos con Esc. En el editor de polos y ceros usá los botones A/B para conservar el clic de diseño.'),
            ('Elegí una curva superpuesta','Curva · Automática usa el punto más cercano al puntero. Si elegís una curva, la guía se ajusta a sus puntos. Por ejemplo, al elegir DFT recorre sus bins. La tabla conserva la coordenada de cada curva cuando sus puntos caen en frecuencias distintas.'),
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
    box(24,62,912,55);text(40,69,480,40,'Herramienta activa','muted');box(650,72,158,35,'purple','selected');text(650,72,158,35,'Calcular','purple');text(818,72,103,35,'Ayuda · F1','green')
    box(24,134,98,245,'border','chrome');text(29,149,88,46,'Inicio',size=11);text(29,213,88,92,'Áreas\nde trabajo','muted',10)
    box(136,134,260,245,'green');text(144,145,244,40,'Datos de entrada','green',14);text(144,198,244,150,'Variantes del cálculo\n\nDefinición\n\nEje, unidades y parámetros')
    box(410,134,526,245,'blue');text(420,145,506,40,'Resultado','blue',15)
    for x,width,label,role in [(425,117,'Abrir gráfico','purple'),(551,115,'Usar… en','green'),(675,117,'Enviar a CAS','blue'),(801,120,'Exportar…','amber')]:
        box(x,199,width,44,role,'input');text(x,202,width,38,label,role,10)
    text(425,258,496,100,'Informe · tablas · vistas del resultado\n\nEl aviso de actualización acompaña al informe.','muted')
    text(24,397,258,55,'En ventanas angostas','muted');box(307,405,293,40,'green','selected');text(307,405,293,40,'Datos de entrada · Alt+1','green');box(614,405,293,40,'blue');text(614,405,293,40,'Resultado · Alt+2','blue')
    p.end();return image
