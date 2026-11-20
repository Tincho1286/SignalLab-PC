"""A short, illustrated introduction to the common scientific workspace."""
ARTICLE_ID='reference:Interfaz de trabajo'


def sections():
    return [dict(title='Interfaz de trabajo',article_id=ARTICLE_ID,route=None,category_label='Primeros pasos',blocks=[
        ('Elegir una herramienta','Las áreas laterales agrupan las tareas por tema. Buscá una operación con Ctrl+K o desde Inicio; la búsqueda también reconoce nombres de sus variantes. Las pestañas superiores permiten volver a los documentos abiertos.'),
        ('Definir el cálculo','Las opciones bajo el título eligen el problema: por ejemplo, transformada directa o inversa, o diseño por bandas o por polos y ceros. En Datos de entrada cargás la definición y sus parámetros. Fórmula y Muestras son entradas propias; Archivo y Resultado permiten incorporar datos existentes. No hace falta calcular primero en otra herramienta.'),
        ('Calcular y leer','El botón de cálculo está arriba a la derecha, junto a Ayuda. Ctrl+Enter ejecuta la misma acción. El resultado aparece con su informe y sus vistas disponibles. Si modificás la entrada, se conserva el cálculo anterior y un aviso indica que debés recalcular para actualizarlo.'),
        ('Trabajar con el resultado','La cabecera reúne Abrir gráfico, Usar señal o sistema en…, Enviar a CAS y Exportar…. Estas acciones usan el último cálculo. En Exportar podés guardar datos o informes y copiar el texto del informe. Cuando hay varias salidas, Trabajar con elige cuál reutilizar o exportar. Usá Ampliar resultado o Ctrl+Mayús+R para leer a todo el ancho. Alt+1 te devuelve a los datos de entrada.'),
        ('Consultar gráficos y ayuda','Los gráficos se abren en ventanas independientes. Podés cerrar una figura y recuperarla con Abrir gráfico; su flecha permite elegir entre las figuras disponibles. Ayuda o F1 abre la explicación de la herramienta con sus esquemas y condiciones. La biblioteca también reúne las funciones admitidas en las fórmulas.'),
        ('Usar una ventana pequeña','Cuando no hay ancho para ambas superficies, Datos de entrada y Resultado se muestran en pestañas. Alt+1 y Alt+2 permiten pasar de una a otra. Cada formulario conserva sus campos al cambiar de tamaño; los controles que no entran se alcanzan desplazando su panel. Los temas cambian el aspecto, sin recalcular los resultados.'),
    ])]


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
