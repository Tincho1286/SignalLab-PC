# SignalLab PC 1.0.1 · transiciones especificadas y retardo FIR

Mantenimiento de la línea estable. Se conserva la organización y el alcance de 1.0.

## Caso reportado

Para paso [0.35π,0.60π] y rechazo hasta 0.25π y desde 0.65π, los anchos especificados son:

- Izquierda: 0.35π−0.25π=0.10π, equivalente a 0.314159 rad/muestra.
- Derecha: 0.65π−0.60π=0.05π, equivalente a 0.157080 rad/muestra.

Las franjas del gráfico representan esos intervalos entre bordes. Se aclara en el título, leyenda, carga e informe que son transiciones especificadas; no una medición de la anchura que ocupa la curva diseñada.

La estimación Kaiser usa la transición menor, 0.05π, y la tolerancia menor, 0.01. Los cortes del ideal quedan en los puntos medios 0.30π y 0.625π. Las tolerancias originales de paso 0.05 y rechazo 0.01 se conservan y verifican por separado. Una sola ventana no obliga a ocupar por completo la transición que tiene más margen.

Para obtener dos intervalos especificados de 0.10π, manteniendo los otros tres bordes, el rechazo superior debe comenzar en 0.70π. La aplicación sigue permitiendo transiciones diferentes cuando ésa es la especificación buscada.

## Retardo de grupo

El filtro reportado tiene 91 coeficientes reales exactamente simétricos. Su retardo es constante en 45 muestras, salvo donde la respuesta se anula. La división polinómica producía pequeñas desviaciones numéricas cercanas a ceros del rechazo, de hasta aproximadamente 10⁻⁶ en ese caso, amplificadas por el zoom vertical.

Se aplica el valor exacto de fase lineal a FIR reales con simetría o antisimetría exacta y denominador constante. Se conserva la máscara de puntos indefinidos y el avance temporal. No se fuerza una constante en filtros casi simétricos, IIR u otros sistemas. La etiqueta del retardo se divide en dos líneas para mantener legibilidad.

## Evidencia

Reproducción del caso: los 91 coeficientes son idénticos a 1.0.0. El retardo finito es 45 sin picos espurios. Comprobaciones dirigidas de un cero indefinido, un avance, FIR asimétrico e IIR. Revisión del panel real con los bordes reportados y con 0.70π para comparar márgenes iguales, más la figura a tamaño normal. No se ejecutó una batería general.
