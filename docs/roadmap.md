# Mejoras de claridad y precisión

La prioridad es consolidar las herramientas existentes: resultados fáciles de interpretar, condiciones matemáticas visibles y carga de datos coherente. Las propuestas siguientes no agregan categorías duplicadas.

## Incorporado en 1.2.2 preliminar

- **Condiciones reunidas:** dominio, ROC, causalidad y estabilidad BIBO en análisis, Resultados y polos/ceros. Si no se conoce la ROC, se indica lo que no puede determinarse. La evaluación formal de H sobre la frontera de Fourier se distingue de una transformada convergente.
- **ROC analógica reutilizable:** semiplano derecho, izquierdo o franja que contiene una línea σ. Se conserva al copiar un sistema o exportarlo; no se supone causalidad sólo por escribir H(s).
- **Extremos de filtros refinados:** bordes, frecuencias alrededor de los polos y búsqueda local de máximos/mínimos. El informe indica frecuencia, margen frente a tolerancias y alcance de la estimación. Se incluye el límite analógico en infinito.
- **Desarrollo opcional de Z y Laplace:** pestaña separada con definición, soporte, convergencia y pasos registrados. La inversión racional bilateral conserva sus fracciones parciales; los pares geométricos muestran sus términos y desplazamientos. No se inventa una descomposición cuando el motor no la registra.
- **Entradas más claras:** los campos escalares incorrectos quedan señalados y conservan su texto. Los coeficientes indican posición y formato admitido. La selección por fórmula no valida campos de coeficientes ocultos.

## Próximas propuestas

| Prioridad | Mejora | Beneficio y alcance |
| --- | --- | --- |
| Alta | Comparación directa de resultados | Elegir dos resultados compatibles y superponerlos con unidades, escala y referencia de fase comunes; informar diferencias sin ocultar desfasajes o cambiar orígenes. Se integra en Resultados. |
| Alta | Diagnóstico de sensibilidad numérica | Explicar cuándo pequeñas variaciones de coeficientes desplazan mucho los polos o alteran tolerancias. Ampliar el análisis de precisión existente; sugerir secciones de segundo orden cuando corresponda. |
| Alta | Residuo de ecuaciones | Para EDO y ecuaciones en diferencias, ofrecer el residuo normalizado y las condiciones iniciales utilizadas. Diferenciar una identidad simbólica de una comprobación sobre un intervalo. |
| Media | Medición coherente en todas las figuras | Cursores vinculados entre módulo, fase y retardo; lectura de frecuencia, unidades y puntos indefinidos. Conservar la selección de muestras enteras en señales discretas. |
| Media | Unidades y reloj más visibles | Mostrar junto a cada entrada si trabaja en rad/s, rad/muestra, segundos o índices; advertir conversiones que requieren T o Fs y pedirlos sólo cuando son necesarios. |
| Media | Desarrollos explicativos en más herramientas | Extender el registro de pasos a convolución, Fourier y ecuaciones, aprovechando cálculos intermedios reales. Mantener el resultado principal conciso. |
| Media | Ayuda con casos completos | Una figura y un ejemplo resuelto por concepto, enlazados desde la herramienta correspondiente. Explicar por qué se elige una ROC o ventana, además de cómo cargarla. |
| Media | Estado del cálculo simbólico | Identificar la etapa en curso —normalización, polos, descomposición o reconstrucción— para entender una demora. Conservar cancelación y resultados previos. |

## Criterios matemáticos

La estabilidad indicada es entrada–salida; una cancelación en la transferencia no demuestra estabilidad interna. La ubicación de polos bajo hipótesis causal se presenta separada de una ROC bilateral elegida.

El refinamiento de extremos sigue siendo numérico: una búsqueda local no prueba haber encontrado todos los extremos. No se presenta como certificación global ni como demostración de orden mínimo. Los resultados próximos a un límite se informan como tales.

Referencias de implementación: [SciPy: búsqueda escalar local](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize_scalar.html) y [evaluación de respuesta digital](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.freqz.html).
