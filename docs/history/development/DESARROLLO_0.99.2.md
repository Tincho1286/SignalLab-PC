# SignalLab PC 0.99.2 — reloj físico al reutilizar H(z)

28/10/2026. Se conserva el contexto temporal de los resultados discretos entre herramientas, sin agregar menús. Se mantiene la estética 0.99.1 y el catálogo de 31 problemas y 76 variantes.

## Transferencia y reloj

Transfer incorpora sample_period_s opcional, positivo y finito para H(z). No modifica sus coeficientes, avances, raíces o evaluación en ω rad/muestra. Un H(z) sin período conocido sigue siendo una transferencia sobre índices; no recibe T=1 automáticamente.

El período se conserva al obtener H desde estados, transformar un sistema analógico a digital, enventanar una h[n] con Fs registrada, normalizar ganancia, separar fase, diseñar compensación y cuantizar/ejecutar coeficientes. Las conexiones conservan el reloj único conocido y rechazan dos períodos conocidos incompatibles; no remuestrean bloques automáticamente. Una transferencia vuelve a estados con su T cuando no se indica otro explícitamente.

## Respuesta temporal

Un campo opcional muestra T cuando llega con el sistema y permite editarlo u omitirlo. Si T está vacío, una entrada propia puede aportar su reloj, o el cálculo permanece sólo en índices. Si está definido y la entrada tiene Fs, se exige T=1/Fs dentro del redondeo numérico. Una entrada sin reloj puede interpretarse con el del sistema dentro de ese cálculo, sin sobrescribir su registro original.

Impulso, escalón y respuestas con memoria inicial conservan el reloj en la salida. El gráfico discreto sigue usando n entero; los datos físicos quedan disponibles para reutilización. Los resultados anteriores permanecen disponibles al editar T hasta recalcular. La copia de entradas entre las vistas temporal y de frecuencia conserva el contexto de reloj.

## Archivos y biblioteca

El JSON nativo de una transferencia con T usa versión 3 y registra sample_period_s y advance explícitamente. Se siguen leyendo los formatos 1 y 2 anteriores. Sin T, la exportación mantiene esos formatos según corresponda. SOS, valores complejos y avances conservan su representación.

Las instantáneas tipadas de la biblioteca guardan T, incluido su ausencia explícita. En resultados históricos que no tenían el campo se puede recuperar un período único desde modelos o señales antecesores con reloj registrado; si hay conflicto no se elige uno arbitrariamente. La búsqueda de procedencia usa caché y conjuntos para evitar duplicar recorridos. Un período omitido explícitamente en un resultado nuevo no vuelve a inferirse desde su padre.

Los informes identifican el reloj conocido y mantienen claro que ω sigue en rad/muestra. Las etiquetas de datos se presentan en español.

## Comprobación focalizada

Se comprobó que las muestras y la frecuencia no cambian al asignar T, el paso estados→H→respuesta temporal, la edición y omisión de T, el intercambio con análisis y la conservación al normalizar y conectar. Se comprobó rechazo de señal/bloques con relojes incompatibles, archivos nativos anteriores y formato 3 con SOS/avance, y recuperación en una biblioteca histórica. No se ejecutó una batería general ni una campaña de instalación o resoluciones.

Esta entrega sigue siendo de desarrollo y no declara completado el objetivo de la primera estable.
