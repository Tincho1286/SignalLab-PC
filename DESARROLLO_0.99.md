# SignalLab PC 0.99 — escala estable de gráficos

28/10/2026. Se corrige la amplificación visual de residuos diminutos, como 1e−11, por el ajuste automático del eje vertical. Se mantiene la organización de 31 problemas y 76 variantes.

## Comportamiento

Las figuras usan un criterio común para curvas y muestras: si todos los valores o su variación son menores que 1e−10 de una referencia visual, se amplía el rango del eje para evitar que ese detalle ocupe todo el panel. La referencia considera la magnitud representada y al menos una unidad del eje. En paneles de parte real/imaginaria también considera la escala de sus componentes. No es una prueba de que los valores sean errores numéricos.

Esto cubre una parte imaginaria diminuta junto a una señal de amplitud normal y las variaciones de redondeo alrededor de una respuesta constante, por ejemplo un retardo de grupo. Los paneles de módulo no negativo conservan un límite inferior cero al aplicar la escala estable. Los límites y las unidades siguen correspondiendo a los valores reales: no se normaliza la amplitud.

El cambio se realiza sólo sobre los límites automáticos. No se ponen muestras a cero, no se eliminan coeficientes y no se alteran las curvas almacenadas. Tabla, cursor y exportación numérica conservan sus valores. La exportación de la figura utiliza la vista seleccionada.

## Control en la figura

Detalle vertical, en la barra de cada ventana, permite ajustar el eje a sus valores originales para inspeccionar señales realmente pequeñas o sus variaciones. Sólo ajusta verticalmente; conserva el intervalo temporal o de frecuencia. Un aviso al pie indica cuándo está actuando la escala estable y cómo acceder al detalle. El aviso no se superpone al gráfico.

El zoom manual no se deshace en cada repintado. Los ejes y compartidos se evalúan como grupo para que un componente pequeño no recorte otro importante. Se conservan las vistas explícitamente más amplias, incluidas referencias de especificaciones.

## Excepciones

No se impone esta escala a planos de raíces con aspecto igual, coordenadas polares, mapas de color o escalas verticales logarítmicas. Los gráficos identificados como error, diferencia, ruido o SNR mantienen su detalle: en esas herramientas los valores pequeños son precisamente el objeto del estudio. Los paneles sin datos no reciben un ajuste artificial.

Se mejora además el contraste del título de la leyenda sobre el fondo oscuro.

## Comprobación focalizada

Se comprobó un residuo sinusoidal de 1e−11 con tallos y una curva casi constante alrededor de 3. Se conservaron exactamente los valores dibujados. Se comprobó el retorno al detalle, el zoom manual, los ejes y compartidos, el panel de error y las excepciones de raíz/logaritmo. Un recorrido breve con el lienzo Qt confirmó el control, el aviso y la exportación de la vista estable. No se ejecutó una batería general ni una campaña de resoluciones.

La compilación sigue siendo de desarrollo; no declara finalizado el objetivo de 1.0.
