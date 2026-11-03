"""Esquemas explicativos y significados de entradas en la ayuda contextual."""
from PySide6.QtCore import QRectF,Qt,QLineF
from PySide6.QtGui import QImage,QPainter,QColor,QPen,QFont
from .band_edges import bands_image,KINDS,EXPLAIN
from .tool_help_catalog import GUIDES

PARAMETERS={
('course_tools','fir'):[('Tipo de filtro','Pasa bajos conserva frecuencias bajas; pasa altos conserva altas; pasa banda conserva una franja; rechaza banda elimina una franja.'),('Frecuencias numeradas','Son los límites entre paso, transición y rechazo, no una lista de cortes intercambiables. Cada casilla admite un valor mayor que 0 y menor que π rad/muestra. Ejemplos: 0.8, pi/4, 0.3*pi. Se exige 1 < 2, y también 2 < 3 < 4 en filtros de banda.'),('Variación permitida en paso δp','Es una cantidad de amplitud, no dB. Con 0.05, el módulo permitido es de 0.95 a 1.05. Menor variación suele requerir más coeficientes.'),('Máximo permitido en rechazo δs','Es la amplitud que puede quedar respecto de una ganancia de referencia 1. Con 0.01 puede quedar como máximo el 1 %, equivalente a −40 dB. Menor valor exige mayor rechazo.'),('Ventana','La ventana multiplica una respuesta ideal truncada. Cambiarla modifica la transición y la ondulación; no cambia el significado de los bordes.'),('Cantidad de coeficientes','Longitud de h[n]. Por ejemplo 51 implica orden 50. Cero solicita estimación Kaiser; con otras ventanas indicá una longitud o una búsqueda.'),('Buscar longitud hasta','Cero desactiva la búsqueda. Un entero positivo fija la mayor longitud que se probará. La primera aceptada depende de la ventana y de la rejilla de comprobación; no es un mínimo universal.')],
('course_tools','iir'):[('Tipo de filtro y frecuencias','Usá el dibujo: las casillas siguen el eje de izquierda a derecha. No se escriben listas. Cada frecuencia debe estar entre 0 y π rad/muestra, sin incluir extremos; admite números o expresiones como pi/4.'),('Pérdida permitida en paso δp','Con 0.05, el módulo se diseña entre 0.95 y 1. Es amplitud lineal, no porcentaje escrito como 5 ni decibelios.'),('Máximo permitido en rechazo δs','Con 0.01 puede quedar como máximo el 1 % de amplitud respecto de una ganancia de referencia 1. El valor debe ser mayor que 0 y menor que 1; además el rechazo debe quedar por debajo del mínimo permitido en paso.'),('Método','Butterworth no presenta ondulación; Chebyshev I la permite en paso, Chebyshev II en rechazo y el elíptico en ambas bandas. Comparar calcula las cuatro familias con las mismas especificaciones.'),('Período T','Sólo se solicita al convertir un prototipo analógico. Se expresa en segundos y debe ser positivo. No es una frecuencia de corte.')],
('course_tools','fft'):[('Longitud observada L','Cantidad de muestras de entrada que se usan; cero usa todas. No puede superar la longitud disponible.'),('Cantidad de puntos FFT','Debe ser al menos L. Si es mayor, se agregan ceros: aparecen más puntos de frecuencia, sin aumentar la duración observada.'),('Ventana y β','La ventana pondera las muestras. β sólo corresponde a Kaiser y controla su forma.'),('Frecuencias para DTFT','Cantidad de puntos de la curva continua; no cambia el número de muestras de la señal ni la resolución de la observación.')],
('systems',0):[('Tipo y cortes','El tipo decide qué banda se conserva. Un corte delimita la transición de este diseño por ventana; no equivale a especificar dos límites separados de paso y rechazo.'),('Coeficientes','Cantidad de muestras de la respuesta al impulso del FIR.'),('Ventana y β','La ventana determina la forma del truncamiento; β sólo se usa en Kaiser.')],
('systems',1):[('Frecuencia central','Ubicación angular de la característica del filtro, entre 0 y π rad/muestra.'),('Q','Factor de calidad: controla la concentración alrededor de la frecuencia central. Debe ser positivo. En el pasabanda de esta herramienta, la ganancia de pico es Q.')],
('systems',2):[('R','Resistencia en ohmios. Debe ser positiva.'),('C','Capacitancia en faradios. Debe ser positiva.'),('Etapas','Número de bloques RC ideales en cascada.'),('Frecuencia de corte','Frecuencia donde el módulo de una etapa pasa bajos cae a 1/√2 de su ganancia de paso.')],
('systems',3):[('Dominio','H(s) para continuo; H(z) para discreto.'),('Numerador b','Determina ceros y ganancia. En continuo las potencias de s descienden; en discreto aparecen 1, z⁻¹, z⁻²…'),('Denominador a','Determina los polos. Su primer coeficiente no puede ser cero; el programa normaliza los coeficientes por ese valor.')],
('systems',4):[('Inicio y final de frecuencia','Intervalo que querés observar: rad/s en continuo, rad/muestra en discreto. La escala logarítmica requiere un inicio positivo.'),('Cantidad de puntos','Cuántas frecuencias se evalúan para dibujar. Aumentarla mejora el muestreo del gráfico, no el filtro.'),('Numerador y denominador','Definen el sistema que se evalúa, o se copian desde un diseño anterior.')],
('systems',6):[('Ceros','Puntos donde se anula la transferencia. El eje horizontal es la parte real y el vertical la imaginaria.'),('Polos','Singularidades de la transferencia. Para un sistema digital causal estable deben quedar dentro del círculo de radio 1.'),('Ganancia','Factor que multiplica la transferencia completa; no desplaza polos ni ceros.'),('Pares conjugados','Al usar pares complejos conjugados se pueden obtener coeficientes reales.')],
('systems',9):[('Sistema','Transferencia del sistema continuo o discreto. Puede cargarse desde un diseño anterior.'),('Entrada','Impulso, escalón o una señal definida por vos.'),('Duración / muestras','Intervalo mostrado. Si la respuesta continúa después, aumentá el intervalo.'),('Valores anteriores','Entradas y salidas previas al inicio del registro. No equivalen a agregar muestras a la señal de entrada.')],
('sampling',0):[('x(t)','Fórmula de la señal continua, con t en segundos.'),('Fs','Cantidad de muestras por segundo. La separación temporal es T=1/Fs.'),('Inicio y cantidad','Instante de la primera muestra y cuántas muestras tomar.')],
('sampling',1):[('Frecuencia del tono','Frecuencia de la sinusoidal analizada, en la unidad indicada.'),('Fs','Tasa de muestreo. Distintas sinusoides pueden producir las mismas muestras cuando aparece aliasing.')],
('sampling',2):[('Factor','Entero que indica cuántas muestras se descartan o se insertan.'),('Método','Diezmar toma una de cada M; expandir inserta ceros; interpolar estima valores. Para evitar aliasing al reducir tasa hace falta filtrado.')],
('sampling',3):[('Muestras','Valores discretos a partir de los que se estima una curva continua.'),('Tasa e intervalo','La tasa define dónde estaban las muestras; el intervalo define qué parte de la reconstrucción se dibuja.')],
('sampling',4):[('Bits y rango','Determinan los niveles de amplitud disponibles. Más bits permiten niveles más próximos.'),('Saturación','Los valores que exceden el rango se limitan a sus extremos.'),('SNR','Relación entre la potencia de la señal y la del error de cuantización; no es una medida de frecuencia.')],
('fourier',0):[('ω inicial / final','Intervalo angular del espectro que se dibuja, en rad/muestra. Un período habitual es de −π a π.'),('Puntos de frecuencia','Cantidad de evaluaciones de la DTFT. Es independiente de la cantidad de muestras de la entrada.'),('Superponer DFT','Añade las muestras de DFT como tallos a la misma curva DTFT; no conecta sus muestras para sustituirla.')],
('fourier',7):[('Segmento','Cantidad de muestras por tramo analizado. Tramos más largos separan mejor frecuencias próximas, pero permiten menos promedios.'),('Solapamiento','Cantidad de muestras compartidas entre segmentos consecutivos; debe ser menor que el segmento.'),('Ventana','Ponderación aplicada a cada segmento antes de calcular su espectro.'),('Quitar media','Resta el promedio de cada segmento. Cambia la componente de frecuencia cero y la potencia analizada.')],
('frequency_filter',0):[('Valor','Ganancia H dentro de un tramo; puede ser compleja para modificar módulo y fase.'),('Cuando','Condición sobre w, la frecuencia angular. Por ejemplo abs(w) <= pi/4.'),('En los demás casos','Valor fuera de los tramos definidos; cero bloquea esas frecuencias.'),('Inicio, paso y puntos de h','Intervalo temporal de la respuesta al impulso que se aproxima. No son los bordes de la banda de paso.')],
('rational_resampling',0):[('L y M','La tasa de salida es la de entrada multiplicada por L/M. Se usan enteros positivos.'),('Filtro antialias','Limita la banda para reducir la superposición espectral al cambiar de tasa.')],
('course_tools','band'):[('Frecuencia inferior y superior','Extremos de la banda donde se integra |X|². Deben quedar dentro del espectro disponible y estar ordenados.')],
('course_tools','gain'):[('Frecuencia angular','Punto donde querés fijar el módulo de H.'),('Módulo objetivo','Ganancia de amplitud deseada, positiva. No puede normalizarse una frecuencia donde H sea cero.')],
('course_tools','inverse_z'):[('Región de convergencia','Determina qué secuencia corresponde a la transferencia. Exterior, interior o círculo unidad tienen interpretaciones distintas.'),('Radio','Radio del contorno para integrar. No debe atravesar polos.'),('Inicio y muestras','Tramo de la secuencia bilateral que se aproxima; puede incluir índices negativos.'),('Puntos del contorno','Resolución de la integración, no longitud de la salida.')],
}

FLOWS={
'frequency_filter':('H(ω): valor y condición','Y(ω) = H(ω) X(ω)','h, espectro y salida'),
'sampling':('Señal y tasa Fs','T = 1/Fs','Muestras / reconstrucción'),
'rational_resampling':('Secuencia y factores L, M','Filtrado y cambio de tasa','Tasa nueva: Fs · L/M'),
'fourier':('Señal y eje temporal','Transformación de Fourier','Espectro y eje de frecuencia'),
'course_tools':('Datos y parámetros','Cálculo de la herramienta','Gráfico, informe y resultados'),
'correlation':('Dos señales y sus ejes','Desplazar y comparar','Correlación por retardo'),
'random_correlation':('Realización y media','Correlación / covarianza','Estimación por retardo'),
'state_space':('A, B, C, D y entradas','Evolución del estado x','Salidas y = Cx + Du'),
'systems':('Coeficientes o diseño','Sistema H','Respuesta / señal filtrada'),
'symbolic':('Fórmula y condiciones','Transformación algebraica','Expresión y condiciones'),
'convolution_algebra':('x y h con sus soportes','Integrar x(τ)h(t−τ)','Salida en función del tiempo'),
'random':('Modelo o muestras','Generación / estadística','Realización o estimaciones')}

def flow_image(route,purpose):
    title,kind,task,_=route
    texts=GUIDES[kind,task]['flow']
    image=QImage(960,230,QImage.Format.Format_ARGB32);image.fill(QColor('#1b2027'));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setFont(QFont('Segoe UI',14))
    for i,text in enumerate(texts):
        x=15+i*320;p.setPen(QPen(QColor('#778493'),1));p.setBrush(QColor('#222831'));p.drawRoundedRect(QRectF(x,30,285,170),8,8)
        p.setPen(QColor('#e1e7ee'));p.drawText(QRectF(x+15,42,255,145),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,text)
        if i<2:
            p.setPen(QPen(QColor('#79c4ad'),2));p.drawLine(QLineF(x+290,115,x+315,115));p.drawLine(QLineF(x+308,109,x+315,115));p.drawLine(QLineF(x+308,121,x+315,115))
    p.end();return image

def _diagrams_for(section):
    if section.get('illustration'):
        from .function_reference import reference_diagram
        caption='Azul: parte ordinaria de la señal. Verde: posición y peso del impulso ideal. La flecha indica área, no una altura finita ni una muestra de la rejilla.' if section['illustration']=='dirac' else 'Esquema de la función elemental. Los tallos representan muestras independientes.'
        return [('Representación',reference_diagram(section['illustration']),caption)]
    route=section['route']
    if route and route[1]=='window_signal':
        from .window_signal_help import window_signal_image
        return [('Longitud e índices de una ventana',window_signal_image(),'Azul: rectangular. Verde: Hann. Ámbar: Hamming. Las tres tienen L=17 muestras sobre n=−8…8. Las muestras no se conectan. La ventana generada es simétrica y finita; no se repite automáticamente fuera de ese intervalo.')]
    if route and route[1:3]==('systems',6):
        from .root_entry_help import root_entry_image
        return [('Cargar una raíz exacta',root_entry_image(),'Azul: parte real e imaginaria. Ámbar: el mismo punto por módulo y ángulo en radianes. Verde: conjugado opcional. Agregar incorpora filas; Calcular actualiza el sistema. El selector de ejes del gráfico no cambia el formato del formulario.')]
    if route and route[1]=='difference_equation':
        from .difference_help import difference_image
        return [('Coeficientes, historial y solución',difference_image(),'Azul: ecuación y comienzo n₀. Ámbar: valores anteriores conocidos. Verde: valores calculados. La primera condición es y[n₀−1], no y[n₀]. La longitud del gráfico no limita la solución algebraica.')]
    if route and route[1] in ('random_model','random_correlation'):
        from .random_model_help import model_image
        cross=route[1]=='random_correlation';fit=route[2]=='fit'
        caption='Azul: x[n]. Verde: y[n]. Se comparan sólo índices observados en ambos registros. El retardo k indica qué muestra de x se multiplica por y; la correlación cruzada no tiene por qué ser par.' if cross else 'Azul: entrada o registro. Ámbar: modelo o ecuaciones de estimación. Verde: proceso y estadísticas obtenidas. El ejemplo AR(1) aclara el signo de a[1]; no reemplaza tus datos.'
        return [('Correlación de dos registros' if cross else 'Leer el modelo y sus coeficientes',model_image(cross=cross,fit=fit),caption)]
    if route and ((route[1]=='basic' and route[2] in ('shift','reverse','scale','parity')) or route[1]=='time_transform'):
        from .transform_help import transform_help_image
        operation=route[2] if route[1]=='basic' else {0:'affine',1:'shift',2:'reverse',3:'scale',4:'parity'}[route[2]]
        return [('Transformación del eje y los valores',transform_help_image(operation,route[1]=='time_transform'),'Azul: registro de entrada. Verde: salida o parte par. Violeta: parte impar. Las figuras mantienen la misma escala de amplitud y tiempo/índice. Los tallos son muestras discretas; las líneas continuas representan el modelo lineal entre puntos. El informe de tu cálculo indica el intervalo y paso reales.')]
    if route and route[1:3]==('basic','sum'):
        from .windowing_help import windowing_help_image
        return [('Sumar en el mismo índice',windowing_help_image(sum_mode=True),'Azul: primera señal x[n]. Ámbar: segunda señal v[n]. Verde: suma de los valores correspondientes. Las tres figuras usan la misma escala de amplitud. La salida cubre ambos registros y cada entrada vale cero fuera de sus datos. En continuo se aplica la misma suma temporal sobre una rejilla interpolada; los impulsos Dirac se mantienen separados de las muestras.') ]
    if route and route[1:3] in (('signal_product',0),('fir_window',0)):
        from .windowing_help import windowing_help_image
        return [('Enventanado punto a punto',windowing_help_image(),'Azul: señal o h[n] cargada. Ámbar: ventana alineada sobre los mismos índices. Verde: producto de los valores de cada índice. En este ejemplo n₀=−2 y N=5; retardar dos muestras lleva el registro resultante a n=0…4. En FIR, L se elige independientemente de h[n]; el ejemplo usa L=5 y n_w=−2. La fórmula se evalúa en ese intervalo; un registro finito vale cero fuera de sus datos.')]
    if route and route[1:3] in (('inverse_dtft',0),('dtft_symbolic',1)):
        from .inverse_dtft_help import inverse_dtft_help_image
        return [('Un período y sus muestras',inverse_dtft_help_image(),'Azul: X(ω) durante un período de 2π, en rad/muestra. Verde: la secuencia resultante en índices enteros, también negativos. En el ejemplo, la banda |ω|≤π/3 produce x[0]=1/3 y x[n]=sin(πn/3)/(πn) para n≠0. El intervalo de salida no recorta la secuencia teórica.')]
    if route and route[1]=='cas':
        from .cas_reference import cas_help_image
        return [('Leer la hoja',cas_help_image(),'Entradas azules, salidas verdes y aclaraciones grises. Cada resultado mantiene su referencia rN.') ]
    if route and route[1]=='system_analysis':
        from .frequency_help import bode_help_image
        from .mathematical_help import z_plane_image
        from .realization_diagram import realization_help_image
        return [('H(s), H(z) y respuesta en frecuencia',z_plane_image(),'Las mallas recorren el plano s o z. La respuesta en frecuencia recorre el eje imaginario o el círculo unitario y requiere una ROC compatible.'),('Módulo, fase y márgenes',bode_help_image(),'Ejemplo ilustrativo L(s)=2/[s(s+1)(s+2)], con realimentación negativa unitaria. Verde: cruce de ganancia y margen de fase. Ámbar: cruce de fase y margen de ganancia. Las frecuencias están en rad/s y la fase en radianes. Los resultados numéricos de tu sistema se consultan en su informe.'),('Leer una realización',realization_help_image(),'Ejemplo discreto: b=[0.25,0.5,0.25], a=[1,−0.4,0.1]. Verde: dos retardos y sus estados q[1],q[2]. Ámbar: multiplicaciones por −a[k], que alimentan el sumador de entrada. Azul: multiplicaciones por b[k], que forman la salida. Las flechas verticales de cada columna suman hacia arriba; no se conectan muestras temporales en este esquema de bloques.')]
    if route and route[1:3]==('course_tools','phase'):
        from .compensation_plot import compensation_help_image
        from .reconstruction_help import reconstruction_help_image
        return [('Qué no determina el módulo',reconstruction_help_image(),'Azul y ámbar tienen el mismo módulo. Los retardos cambian la fase y el retardo de grupo; no pueden recuperarse sólo desde la amplitud. La reconstrucción fija hipótesis y convenciones explícitas.'),('Diseñar un compensador FIR',compensation_help_image(),'El sistema H se conserva. Se agrega C en cascada para aproximar una ganancia y un retardo en una banda. El ajuste es aproximado: la comparación y sus errores muestran el resultado obtenido. La modalidad de fase mínima y paso todo sigue disponible en el selector Estudio.')]
    if route and route[1:3]==('sampling',5):
        from .precision_help import precision_help_image
        from .arithmetic_help import arithmetic_help_image
        return [('Dónde se redondea al filtrar',arithmetic_help_image(),'El producto, la suma y la memoria tienen conversiones distintas. Los bits extra pertenecen al acumulador. La comparación conserva la misma realización para distinguir almacenamiento y ejecución.'),('Leer una palabra flotante',precision_help_image(),'El signo, el exponente y la fracción forman el valor representado. Un formato almacena sólo ciertos números: al convertir aparece un error. El mismo efecto aplicado a coeficientes puede cambiar la respuesta y los polos de un filtro; la segunda modalidad permite compararlos.')]
    if route and route[1]=='course_tools' and route[2] in ('fir','iir','analog'):
        from .mathematical_help import amplitude_image
        return [('Amplitudes y tolerancias',amplitude_image(),'Cada banda de paso tiene su amplitud y sus límites. El esquema ilustra tolerancias absolutas; el selector permite también fracciones relativas y dB.')]+[(title,bands_image(kind,analog=route[2]=="analog"),' · '.join(f'{i+1}: {label}' for i,label in enumerate(labels))) for kind,(title,labels,_) in KINDS.items()]
    if route and route[1:3]==('transform_lab','z'):
        return illustrated_diagrams(section)+[('Cómo elegir la región de convergencia',roc_image(),'La misma X(z) racional puede representar tres secuencias distintas. Las cruces son polos en z=0.5 y z=2; la zona coloreada es la ROC. Un radio como r=1 selecciona el anillo 0.5<|z|<2. El radio no es un polo ni el borde del anillo.')]
    if route and route[1]=='tool_group':return [('Flujo de trabajo',flow_image(route,section['purpose']),'Las opciones conservan sus entradas. Enviar un resultado copia los datos a la opción elegida.') ]
    if route:return illustrated_diagrams(section)
    return []

def parameter_blocks(section):
    if not section['route']:return []
    _,kind,task,_=section['route'];guide=GUIDES[kind,task]
    # Las fichas específicas tienen precedencia; los detalles adicionales se conservan.
    rows=list(guide['parameters'])
    if kind=='course_tools' and task in ('fir','iir'):rows+=PARAMETERS[kind,task]
    return [('Qué significa cada dato','\n'.join(name+': '+meaning for name,meaning in rows)),('Cómo leer el resultado',guide['reading'])]


def illustrated_diagrams(section):
    """Figuras estáticas con leyendas: no modifican los datos de la herramienta."""
    import math
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QPainterPath
    route=section['route'];kind=route[1];task=route[2]
    if route[1:3]==('course_tools','convert'):
        from .conversion_help import conversion_help_image
        return [('Mapeo y corte efectivo',conversion_help_image(),'Ω se expresa en rad/s, T en segundos y ω en rad/muestra. El producto ΩT es un ángulo en radianes. La curva azul corresponde a la sustitución bilineal. La verde muestra una frecuencia principal de la invarianza al impulso: al superar π aparece plegado. La frecuencia efectiva de media potencia se mide sobre la transferencia obtenida y puede diferir de esa referencia.')]
    if route[1:3]==('transform_lab','laplace'):
        from .laplace_help import laplace_help_image
        return [('ROC y soporte temporal',laplace_help_image(),'Las cruces marcan polos en s=−1 y s=2. La zona verde es la ROC bilateral: −1<Re(s)<2. La línea σ=0.5 queda dentro de esa zona. El polo azul queda a su izquierda y genera exp(−t)·u(t); el violeta queda a su derecha y genera exp(2t)·u(−t). Esta señal tiene X(s)=1/(s+1)−1/(s−2). Los bordes de la ROC no se incluyen.')]
    if route and ((route[1]=='basic' and route[2] in ('shift','reverse','scale','parity')) or route[1]=='time_transform'):
        from .transform_help import transform_help_image
        operation=route[2] if route[1]=='basic' else {0:'affine',1:'shift',2:'reverse',3:'scale',4:'parity'}[route[2]]
        return [('Transformación del eje y los valores',transform_help_image(operation,route[1]=='time_transform'),'Azul: registro de entrada. Verde: salida o parte par. Violeta: parte impar. Las figuras mantienen la misma escala de amplitud y tiempo/índice. Los tallos son muestras discretas; las líneas continuas representan el modelo lineal entre puntos. El informe de tu cálculo indica el intervalo y paso reales.')]
    if route and route[1:3]==('basic','sum'):
        from .windowing_help import windowing_help_image
        return [('Sumar en el mismo índice',windowing_help_image(sum_mode=True),'Azul: primera señal x[n]. Ámbar: segunda señal v[n]. Verde: suma de los valores correspondientes. Las tres figuras usan la misma escala de amplitud. La salida cubre ambos registros y cada entrada vale cero fuera de sus datos. En continuo se aplica la misma suma temporal sobre una rejilla interpolada; los impulsos Dirac se mantienen separados de las muestras.') ]
    if route and route[1:3] in (('signal_product',0),('fir_window',0)):
        from .windowing_help import windowing_help_image
        return [('Enventanado punto a punto',windowing_help_image(),'Azul: señal o h[n] cargada. Ámbar: ventana alineada sobre los mismos índices. Verde: producto de los valores de cada índice. En este ejemplo n₀=−2 y N=5; retardar dos muestras lleva el registro resultante a n=0…4. En FIR, L se elige independientemente de h[n]; el ejemplo usa L=5 y n_w=−2. La fórmula se evalúa en ese intervalo; un registro finito vale cero fuera de sus datos.')]
    if route and route[1:3] in (('inverse_dtft',0),('dtft_symbolic',1)):
        from .inverse_dtft_help import inverse_dtft_help_image
        return [('Un período y sus muestras',inverse_dtft_help_image(),'Azul: X(ω) durante un período de 2π, en rad/muestra. Verde: la secuencia resultante en índices enteros, también negativos. En el ejemplo, la banda |ω|≤π/3 produce x[0]=1/3 y x[n]=sin(πn/3)/(πn) para n≠0. El intervalo de salida no recorta la secuencia teórica.')]
    teal='#79c4ad';blue='#8ab6df';amber='#dfb374';ink='#e1e7ee'
    image=QImage(960,420,QImage.Format.Format_ARGB32);image.fill(QColor('#1b2027'));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    def text(x,y,w,h,value,color=ink,size=14):
        p.setFont(QFont('Segoe UI',size));p.setPen(QColor(color));p.drawText(QRectF(x,y,w,h),Qt.TextFlag.TextWordWrap,value)
    def line(x,y,xx,yy,color=ink,width=2):p.setPen(QPen(QColor(color),width));p.drawLine(QLineF(x,y,xx,yy))
    def curve(points,color):
        path=QPainterPath();path.moveTo(*points[0])
        for point in points[1:]:path.lineTo(*point)
        p.setPen(QPen(QColor(color),3));p.setBrush(Qt.BrushStyle.NoBrush);p.drawPath(path)
    spectral=kind in ('fourier','fourier_symbolic','dtft_symbolic') or (kind=='basic' and task in ('dft','idft')) or (kind=='course_tools' and task in ('fft','band','lines'))
    systems=kind in ('systems','system_analysis','state_space','interconnection','frequency_filter','filter_lab') or kind=='course_tools'
    if kind=='transform_lab':
        z=task=='z';title='De una expresión a su transformada, y de vuelta';caption='La expresión y las condiciones forman el resultado. En Z, otra región de convergencia puede dar otra señal; Laplace se interpreta aquí de forma unilateral/causal.'
        for x,label,color in [(40,'x[n] y soporte' if z else 'x(t), t ≥ 0',teal),(535,'X(z) y ROC' if z else 'X(s) y condiciones',blue)]:
            p.setPen(QPen(QColor(color),2));p.setBrush(QColor('#222831'));p.drawRoundedRect(QRectF(x,65,380,115),8,8);text(x+20,95,340,65,label,color,24)
        line(420,100,535,100,amber);line(535,150,420,150,amber);text(430,65,100,40,'Directa',amber,12);text(430,155,100,40,'Inversa',amber,12)
        text(45,230,860,65,'X(z) = Σ x[n] z^(−n)' if z else 'X(s) = ∫₀∞ x(t) exp(−st) dt',ink,22)
        text(45,310,860,90,'La ROC se expresa mediante |z|, no mediante z real. El intervalo de muestras sólo controla la visualización.' if z else 'La inversa causal usa x(t)=0 para t<0. Una expresión sin resolver se informa, no se sustituye por un resultado supuesto.',ink,16)
    elif kind=='course_tools' and task=='convert':
        title='Dos formas de convertir una respuesta analógica';caption='Verde: respuesta analógica Ha. Azul: respuesta digital Hd. Naranja: dato que controla la conversión. Una respuesta ideal no implica una realización FIR/IIR finita.'
        text(40,15,400,45,'Bilineal: cambia el eje de frecuencia',teal,17)
        text(40,75,390,80,'Ha(jΩ) → Hd(exp(jω))',blue,21)
        text(40,165,390,65,'Ω = (2/T) tan(ω/2)',amber,22)
        text(40,255,390,105,'T: segundos entre muestras. Los cortes se mueven; no se suman réplicas.',ink,16)
        line(475,25,475,385,'#778493')
        text(505,15,410,45,'Invarianza: suma réplicas',teal,17)
        line(520,160,910,160,'#778493')
        for center,color in [(575,blue),(715,teal),(855,blue)]:
            curve([(center-50,160),(center-50,90),(center+50,90),(center+50,160)],color)
        text(505,185,410,55,'Separación: 2π/T rad/s',amber,19)
        text(505,255,410,105,'Ωmáx declara el soporte: fuera, Ha=0. Si las réplicas se superponen aparece aliasing.',ink,16)
    elif kind=='course_tools' and task=='bandpass_sampling':
        title='Banda de la señal y frecuencia de muestreo';caption='Esquema de soporte espectral de una señal real. Verde: banda positiva; azul: su reflejo negativo. Ωs separa las réplicas generadas al muestrear; no es el ancho B.'
        line(65,230,900,230,'#778493');line(480,80,480,250,'#778493')
        for left,right,color in [(180,320,blue),(640,780,teal)]:
            p.setPen(QPen(QColor(color),2));p.setBrush(QColor(color));p.drawRect(QRectF(left,130,right-left,100))
        text(120,250,270,55,'−ΩH            −ΩL',blue);text(600,250,300,55,'ΩL                ΩH',teal)
        text(465,255,50,40,'0');text(800,250,130,45,'Ω (rad/s)')
        line(640,100,780,100,amber,3);text(590,35,330,55,'B = ΩH − ΩL',amber)
        text(70,325,820,70,'Ωs = 2π Fs. Las tasas admisibles evitan que las bandas repetidas se superpongan.',ink,16)
    elif kind=='systems' and task==6:
        title='Cómo leer el plano de polos y ceros';caption='Ejemplo digital: círculos = ceros, cruces = polos. Para estabilidad causal, todos los polos deben quedar dentro del círculo unidad.'
        line(65,215,510,215,'#778493');line(285,50,285,370,'#778493');p.setPen(QPen(QColor('#778493'),2));p.setBrush(Qt.BrushStyle.NoBrush);p.drawEllipse(QPointF(285,215),140,140)
        for y in (155,275):line(350,y-7,364,y+7,amber,3);line(350,y+7,364,y-7,amber,3)
        p.setPen(QPen(QColor(teal),3));p.drawEllipse(QPointF(145,215),8,8)
        text(560,65,370,60,'○ Cero: anula H(z)',teal);text(560,145,370,70,'× Polo: determina modos de la respuesta',amber);text(560,245,370,90,'Círculo: |z| = 1\nEjes: parte real e imaginaria',blue)
    elif spectral:
        title='Eje de frecuencia y amplitud';caption='Esquema ilustrativo, no resultado calculado. Una curva representa una evaluación sobre frecuencias; los tallos indican muestras discretas del espectro.'
        line(60,305,900,305,'#778493');line(70,75,70,315,'#778493')
        pts=[(80+i*3,295-165*math.exp(-((i-80)/25)**2)-100*math.exp(-((i-180)/18)**2)) for i in range(265)];curve(pts,teal)
        for i in range(0,265,12):
            x,y=pts[i];line(x,305,x,y,blue);p.setBrush(QColor(blue));p.drawEllipse(QPointF(x,y),4,4)
        text(110,20,410,45,'Verde: curva del espectro',teal);text(535,20,390,45,'Azul: valores discretos',blue);text(100,330,780,65,'Horizontal: frecuencia angular ω. Vertical: módulo |X|; en densidad de energía se representa |X|².',ink)
    elif systems:
        title='Del sistema a su respuesta';caption='La transferencia describe el sistema. Su respuesta en frecuencia y su respuesta temporal son vistas distintas del mismo modelo.'
        for x,label,color in [(40,'Entrada\nx(t) o x[n]',blue),(350,'Sistema\nH(s) o H(z)',teal),(660,'Salida\ny(t) o y[n]',amber)]:
            p.setPen(QPen(QColor(color),2));p.setBrush(QColor('#222831'));p.drawRoundedRect(QRectF(x,95,255,130),10,10);text(x+20,118,215,90,label,color,18)
        line(295,160,350,160);line(605,160,660,160)
        text(55,265,850,100,'Coeficientes o parámetros → modelo del sistema → gráfico e informe. Para filtrar o simular una respuesta necesitás además definir la entrada.',ink,16)
    else:
        title='Qué representa cada muestra';caption='Ejemplo de lectura del eje, no resultado calculado. Los tallos no unen muestras vecinas: cada punto representa un valor en su propio índice o instante.'
        line(65,225,900,225,'#778493');line(75,60,75,340,'#778493')
        curve([(90+i*3,225-100*math.sin(i/23)) for i in range(265)],'#778493')
        for i in range(17):
            x=90+48*i;y=225-100*math.sin((x-90)/69);line(x,225,x,y,teal);p.setBrush(QColor(teal));p.setPen(QColor(teal));p.drawEllipse(QPointF(x,y),5,5)
        text(90,15,700,45,'Verde: amplitud de cada muestra',teal);text(130,350,760,55,'Horizontal: índice n o tiempo t. Vertical: valor de la señal.',ink)
        if kind in ('sampling','rational_resampling'):
            line(378,90,426,90,amber,3);text(450,65,430,75,'Separación temporal: T = 1/Fs',amber)
        else:text(90,280,790,55,'Origen + (cantidad − 1) × paso = último punto',amber)
    p.end()
    result=[(title,image,caption)]
    # Cada página conserva su esquema específico de entrada, operación y salida.
    result.append(('Recorrido de esta herramienta',flow_image(route,section['purpose']),GUIDES[kind,task]['reading']))
    return result


def roc_image():
    """Three valid annuli for two real poles; boundaries are excluded."""
    from PySide6.QtCore import QPointF
    image=QImage(960,420,QImage.Format.Format_ARGB32);image.fill(QColor('#1b2027'))
    p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for i,(title,condition,color) in enumerate([('Exterior','|z| > 2','#79c4ad'),('Interior','|z| < 0.5','#8ab6df'),('Anillo','0.5 < |z| < 2','#dfb374')]):
        left=i*320;center=QPointF(left+155,165)
        p.setFont(QFont('Segoe UI',15));p.setPen(QColor(color));p.drawText(QRectF(left+15,8,280,35),Qt.AlignmentFlag.AlignCenter,title)
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(color).darker(230))
        if i==0:p.drawRect(QRectF(left+20,45,270,245))
        else:p.drawEllipse(center,23 if i==1 else 92,23 if i==1 else 92)
        if i!=1:
            p.setBrush(QColor('#1b2027'));p.drawEllipse(center,92 if i==0 else 23,92 if i==0 else 23)
        p.setPen(QPen(QColor('#778493'),1));p.drawLine(QLineF(left+20,165,left+290,165));p.drawLine(QLineF(left+155,45,left+155,290))
        p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor('#778493'),1,Qt.PenStyle.DashLine))
        for r in (23,92):p.drawEllipse(center,r,r)
        p.setPen(QPen(QColor('#e1e7ee'),2))
        for x in (left+178,left+247):
            p.drawLine(QLineF(x-5,160,x+5,170));p.drawLine(QLineF(x-5,170,x+5,160))
        p.setPen(QColor('#e1e7ee'));p.setFont(QFont('Segoe UI',11))
        for x,label in [(left+168,'0.5'),(left+238,'2')]:p.drawText(QRectF(x,178,35,25),label)
        if i==2:
            p.setPen(QPen(QColor(color),2,Qt.PenStyle.DotLine));p.drawEllipse(center,46,46)
            p.setFont(QFont('Segoe UI',11));p.drawText(QRectF(left+205,88,70,30),'r = 1')
        p.setPen(QColor(color));p.setFont(QFont('Segoe UI',17));p.drawText(QRectF(left+15,310,280,42),Qt.AlignmentFlag.AlignCenter,condition)
        p.setPen(QColor('#e1e7ee'));p.setFont(QFont('Segoe UI',12));p.drawText(QRectF(left+18,360,275,50),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,['Términos derechos','Términos izquierdos','Combinación bilateral'][i])
    p.end();return image


def diagrams_for(section):
    diagrams=_diagrams_for(section);route=section.get('route')
    if route:
        from .tool_catalog import locate
        entry=locate(route)
        if entry and entry['title']=='Diseñar filtro' and route[1:3]!=('systems',6):
            from .filter_design_help import filter_design_image
            diagrams=[('Elegir cómo diseñar',filter_design_image(),'Cada entrada describe un problema diferente: bandas y tolerancias, respuesta FIR, raíces o parámetros de un modelo. Todos generan un filtro reutilizable. Cambiar de método conserva sus datos; no convierte automáticamente una definición en otra. El análisis de un filtro existente está en Analizar un sistema.')]+diagrams
        if entry and entry['title']=='Transformada de Fourier':
            from .fourier_choice_help import fourier_choice_image
            diagrams=[('Elegir transformada y dirección',fourier_choice_image(),'DFT: coeficientes de un registro. DTFT: curva periódica de una secuencia. Continua: tiempo en segundos y frecuencia en rad/s. Directa va de señal a espectro; Inversa recorre el camino contrario. FFT calcula la DFT, no define otra transformada.')]+diagrams
    return diagrams
