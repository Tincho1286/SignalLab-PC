# SignalLab PC 0.99.11 · diseño unificado y formularios despejados

## Un solo lugar para diseñar

Diseñar filtro reúne nueve formas existentes: especificaciones FIR/IIR digitales o analógicas; FIR por cortes/longitud o h[n] propia; editor de polos y ceros; segundo orden digital o analógico; y circuito RC. Modelos de filtros y Diseñar por polos y ceros dejan de repetirse como accesos principales separados. Sus rutas siguen disponibles para búsqueda, ayuda y reutilización.

El selector empieza por Diseñar por. Dominio y Estructura sólo aparecen si aportan una elección real. En FIR por ventana se elige cortes/longitud o h[n]; RC tiene sus parámetros analógicos; el editor de raíces mantiene su elección interna de plano s o z. Segundo orden digital usa frecuencia y Q; el modelo analógico usa frecuencia natural, amortiguamiento y ganancia.

El análisis no se traslada al diseño: Analizar un sistema sigue siendo el lugar para estudiar una H existente, sus polos/ceros y su respuesta. Los resultados diseñados mantienen las acciones directas Analizar, Usar filtro en y Exportar.

## Cada definición conserva sus datos

Cambiar de método no convierte resistencias, tolerancias o raíces en una definición diferente ni copia coeficientes ocultos de un panel anterior. Cada formulario conserva sus parámetros. FIR e IIR por especificaciones pueden copiar las bandas y tolerancias cuando usan las mismas unidades. Cambiar entre analógico y digital no mezcla rad/s y rad/muestra.

Volver desde la especificación analógica a la digital recupera la estructura digital elegida antes si la estructura analógica era una opción forzada. El dominio continúa teniendo prioridad cuando es compatible. Los destinos de reutilización indican Diseñar filtro · Polos y ceros cuando ése es el editor compatible.

## Datos antes que mensajes vacíos

Se retiran los avisos genéricos iniciales repetidos; después de calcular siguen apareciendo Resultado actualizado y Datos modificados. El encabezado de resultados de los diseños clásicos sólo se muestra cuando hay un sistema calculado o cargado. RC conserva su explicación dinámica de componentes y unidades y elimina la descripción estática duplicada.

Se ocultan los botones antiguos de guardado y exportación en la carga de los diseños clásicos. Su resultado calculado ofrece Exportar con filtro JSON y respuesta en frecuencia CSV; no se pierde esa exportación. En el editor de raíces se conservan las acciones específicas de su estudio de frecuencia. Se evita la leyenda vacía cuando no hay raíces y se corrige una descripción de FIR que aún decía ciclos por muestra en vez de rad/muestra.

La ayuda existente incorpora un mapa de colores entre las formas de definir el filtro y la transferencia resultante, conservando sus ilustraciones específicas. No se agrega un botón grande de instrucciones ni una herramienta por cada método.

## Evidencia y alcance

Se comprobaron las nueve rutas en un único documento, búsqueda RC/biquad/raíces, separación del análisis, copia de especificaciones compatibles, recuperación de la estructura digital y conservación del valor R al cambiar de forma. Se recorrió un diseño RC real para comprobar que las acciones de resultado y sus dos exportaciones quedan disponibles después del cálculo. Se comprobó que el estado inicial no ocupa una línea y que modificar datos después de un resultado conserva el aviso de desactualización.

Se revisaron los controles y la ayuda a 800 px de ancho. No se realizó una batería general ni una campaña del portable. Los motores de diseño no cambian sus fórmulas.

El catálogo pasa de 31 a 29 problemas especializados y conserva las 80 variantes, además de la hoja CAS. Se mantiene la paleta y el flujo de versiones con retención local acotada. El objetivo de primera estable continúa abierto.
