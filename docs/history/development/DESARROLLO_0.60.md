# SignalLab 0.60 · Cascadas y reloj de señales

## Exactitud de interconexiones

Al copiar filtros digitales en secciones a H1/H2, la interfaz ya no descarta su representación. Una cascada de dos SOS conserva todas las secciones; también se admite combinar un SOS con un bloque real de orden como máximo dos, sin factorizar raíces. La salida conserva SOS para respuesta temporal, frecuencia y exportación. Editar la definición de un bloque reemplaza su realización preservada.

Se reprodujo una cascada Butterworth de órdenes 12+12 en la que expandir todos los coeficientes producía un error máximo de aproximadamente 4.83 frente al producto de las respuestas por secciones. El cálculo por secciones coincide con el producto y con aplicar los dos filtros sucesivamente.

En conexiones que todavía necesitan un polinomio equivalente a partir de entradas SOS, se compara el resultado con los bloques sobre 2049 frecuencias. Si la discrepancia relativa a max(1,|Href|) supera 1e-6, o el resultado no es finito, no se publica un equivalente incorrecto. Esta comprobación detecta pérdida de precisión; no certifica máximos entre puntos ni estabilidad interna.

## Reloj de señales

Desplazamiento e inversión discretos actualizan time_start_s cuando existe sample_rate_hz. Se mantiene fijo el instante asociado a n=0. Para y[n]=x[n−k], el primer instante se desplaza k/Fs. La inversión discreta es respecto de n=0, que puede corresponder a un instante físico distinto de cero. El cambio de tasa y la reconstrucción leen esos datos coherentes.

## Comprobación acotada

Cascada SOS en frecuencia y tiempo; cascada con ganancia; copiar dos filtros, calcular y enviar a Respuesta temporal; edición de bloque reemplazando su definición. Respuesta discreta con historiales reales desde un índice negativo frente a recurrencia directa y suma de componentes; respuesta continua de primer orden desde t=7 frente a 1−exp(−(t−7)). Desplazamiento, doble inversión, diezmado y reconstrucción con reloj conocido.

Continúa abierta la revisión de transformadas/ROC y de los recorridos con distribuciones ideales. No se declara 1.0 por estas comprobaciones parciales.
