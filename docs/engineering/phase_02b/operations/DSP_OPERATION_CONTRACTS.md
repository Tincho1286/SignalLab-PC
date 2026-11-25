# Contratos DSP

**Criterios previos de WP-02B.02.** Cada adaptador preserva las convenciones existentes de GUI, valida sus parámetros, estima temporales y publica una salida interoperable. La comparación usa fórmulas y vectores independientes. La composición de resultados se difiere a WP-02B.03.

| Operación | Contrato, convención y dominio |
| --- | --- |
| IDFT | Espectro discreto complejo, orden y fase de origen originales. División por N y restauración opcional de origen y reloj. FFT inversa, costo O(N log N). |
| Diseño FIR | Tipo, longitud, cortes en ciclos/muestra, ventana y beta. Núcleo ideal sinc desplazado a (K−1)/2 con ventana simétrica. Ganancia sin normalización automática. Costo O(K). |
| Aplicación FIR | FIR digital causal y reposo inicial. Registro mismo tamaño o convolución completa con K−1 muestras de cola. Mantiene índice y reloj. El modelo se evalúa con recurrencia directa, O(NK). |
| Resampling | Multiplicador y divisor positivos reducidos por MCD. FIR Kaiser polifásico, extensión nula o lineal y retardo compensado. Salida ceil(NL/M), origen de índice 0 y mismo primer instante físico cuando se conoce. |
| PSD | Welch o periodograma con ventana simétrica y norma Fs·Σw². Conserva el estimador histórico de potencia por compatibilidad. Rejilla Hz y vista bilateral centrada o unilateral para señales estrictamente reales. La unilateral suma el par interior y conserva DC y Nyquist. |

Se eligieron adaptadores específicos sobre una clase única de resultados. Las salidas numéricas son `Signal`; la respuesta de diseño es `Transfer` con especificación tipada. Las frecuencias físicas requieren reloj compatible. Los cálculos conservan la precisión compleja de los motores y rechazan resultados fuera de float64. Las pruebas detallan los casos límite. [Validación](DSP_MATHEMATICAL_VALIDATION.md)
