# SignalLab PC 0.61 — ejes e impulsos ideales

- Ejes de secuencias con marcas enteras incluso al ampliar; etiquetas de índice, coeficiente, tiempo, retardo y frecuencia con unidades.
- Frecuencia digital lineal expresada con múltiplos de π rad/muestra. Las muestras DFT no se unen; DTFT y respuestas de filtros conservan su eje continuo.
- Los gráficos temporales en segundos conservan tiempos fraccionarios, incluso si representan muestras.
- Reutilización de Dirac en Fourier, convolución, correlación, cambios de escala/desplazamiento y respuesta LTI continua. Los pesos singulares permanecen separados de la parte regular.
- Energía, Hilbert, STFT y normalización no ignoran términos singulares: informan su limitación.

Comprobación dirigida: sintaxis, Fourier de Dirac desplazado, escala negativa, δ*x=x, respuesta de H(s)=(s+2)/(s+1) a impulso complejo fuera de la rejilla, ejes enteros con zoom, DFT en radianes y render del resultado. No se hizo una campaña general de pruebas.

Sigue siendo una versión previa a 1.0. Pendientes de alcance y exactitud: CIERRE_1.0.md. Sesiones, modulación y ampliaciones de señales aleatorias quedan fuera de esta etapa.

Revisión adicional: densidad de energía de una DFT y cortes FFT del espectrograma conservan muestras sin unir. Los centros de ventanas pares pueden quedar entre índices y no se redondean.
