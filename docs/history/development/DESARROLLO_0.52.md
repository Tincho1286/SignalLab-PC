# SignalLab 0.52 · Escritorio de laboratorio

## Cambio de entorno

Se reemplaza el catálogo de tarjetas 0.51 por un escritorio con explorador de herramientas acoplable, documentos en pestañas, barra de acciones y espacio de trabajo con resultados calculados. Se pueden mover, desacoplar u ocultar los paneles; Vista permite restablecer la distribución. F11 concentra el documento y F1 abre la ayuda. Cerrar una pestaña conserva sus datos durante la sesión. La geometría y disposición de paneles se recuerdan en este equipo; los formularios no se guardan al cerrar la aplicación.

Estilo nuevo: gris grafito neutro, controles rectangulares compactos, acento ámbar y figuras sobre papel claro. Se mantienen la independencia de las herramientas y la reutilización explícita.

Referencias de diseño consultadas:
- MATLAB: https://www.mathworks.com/help/matlab/matlab_env/change-the-desktop-layout.html
- GNU Octave: https://docs.octave.org/v9.4.0/Octave-Workspace-Windows.html
- GNU Radio: https://wiki.gnuradio.org/index.php/FAQ

Se toman patrones de organización de escritorio; esta entrega no implementa un nuevo editor de conexiones por arrastre como GNU Radio Companion.

## Gráficos

Las leyendas de ejes se reúnen fuera del trazado, con una columna propia. El diseño se recalcula al dibujar, redimensionar y exportar. Las etiquetas largas se distribuyen en varias líneas y se reservan márgenes para títulos y unidades. Las figuras ampliadas conservan los mismos datos y vuelven a su panel al cerrar.

En FIR se eliminan controles repetidos de salida, se agrupan las opciones de representación y se conserva visible Calcular a 1366 × 768. Las fórmulas usan fondo transparente para conservar contraste en los informes oscuros.

## Revisión acotada

- Cálculo de FIR Blackman con 51 coeficientes.
- Comprobación geométrica de que la leyenda no intersecta los ejes en una ventana ampliada de 817 píxeles de ancho.
- Ampliación y retorno del lienzo; capturas del escritorio, FIR, muestreo y ayuda a 1366 × 768.
- No se ejecutó una batería numérica completa ni se certificaron todos los paneles, escalas DPI o tamaños de pantalla.

Continúa como vista previa; no se declara versión estable 1.0.
