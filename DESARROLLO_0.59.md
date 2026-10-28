# SignalLab 0.59 · Energía y síntesis de Fourier

## Correcciones funcionales

- Síntesis continua y discreta a partir de coeficientes manuales: corregida la copia de la señal con metadatos. Antes producía un error de argumento no admitido; ahora reconstruye sin modificar la entrada.
- Los pesos de deltas de una serie periódica ya no se aceptan como un espectro ordinario para elevar al cuadrado o integrar como densidad de energía.
- La síntesis continua también rechaza pesos de líneas de potencia confundidos con coeficientes armónicos.

## Informe de densidad de energía

El panel calcula |X|² e integra exactamente el intervalo mostrado mediante cuadratura trapezoidal. El informe se mantiene al alternar entre espectro y densidad y se puede copiar/exportar con formato.

Al partir de una secuencia, compara energía temporal y espectral cuando se integra un período completo de 2π. Advierte si hay menos de N subintervalos para un registro de N muestras. Esta condición evita presentar una rejilla insuficiente como validación de Parseval. Para bandas parciales o varios períodos explica por qué no es una comparación de energía total.

Una DFT angular completa informa por separado Σ|X[k]|²/N: los N bins no repiten el extremo final del período. En continuo declara la aproximación rectangular temporal, el intervalo espectral finito y la periodicidad numérica debida al muestreo. No afirma exactitud simbólica ni energía de toda una señal infinita.

## Comprobaciones acotadas

Secuencia compleja con origen negativo y Parseval; caso con rejilla insuficiente; DFT con ceros agregados; rechazo de pesos de deltas; informe al alternar vistas; síntesis manual de un coseno continuo y de una secuencia constante. Se conservaron las entradas originales.

La prioridad sigue siendo funcionalidad y exactitud. Sesiones fuera de requisitos actuales; sin modulación/demodulación ni ampliaciones de Señales Aleatorias.
