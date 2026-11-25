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

En FIR, `same` conserva las primeras N muestras causales. `full` añade la cola. La especificación de diseño es un registro con el filtro como padre. Exportar ese registro con sus dependencias lleva ambos datos. La PSD guarda Fs y las unidades de amplitud si se conocen. El origen temporal de su entrada se recupera desde el padre en Project.

## Referencias numéricas

- **DFT e inversa.** La referencia de fase física usa `Σ x[n] exp(−j 2π k n/N)`. La inversa suma `X[k] exp(j 2π k n/N)/N`. Para fase de registro se usa un índice que comienza en cero. El orden centrado es una permutación de los mismos bins. [Convenciones del piloto](../../DFT_PILOT_API.md)
- **FIR.** `y[n] = Σ b[k] x[n−k]` bajo reposo previo. Para un pasabajos ideal, cada coeficiente de diseño es `2 f₁ sinc(2 f₁ (k−(K−1)/2)) w[k]`. Un rechazo o pasaje de banda combina ideales antes del enventanado. La respuesta a una delta recupera los coeficientes. Para la simetría usada en el ejemplo, el retardo de grupo en banda es `(K−1)/2` muestras.
- **Resampling.** Con kernel simétrico de semilongitud A, la compensación evalúa `y[m] = L Σ x[k] h[A + mM − kL]`. Se conserva el reloj de inicio y la tasa de salida vale `Fs·L/M`. El cálculo polifásico usa por muestra de salida una fase de aproximadamente `K/L` coeficientes. El antialias depende de la transición finita y del tratamiento de extremos.
- **PSD.** Cada bloque de S muestras calcula `|FFT(w·x)|²/(Fs·Σw²)`. Welch promedia los bloques válidos. El costo se aproxima a `O(B S log S)` para B bloques y reutiliza temporales de tamaño S. En el periodograma rectangular, la suma de bins multiplicada por `Fs/S` recupera la potencia media del registro. El plegado unilateral conserva esa suma para entradas reales.
