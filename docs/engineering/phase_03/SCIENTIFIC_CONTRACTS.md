# Contratos científicos de comunicaciones

Convenciones de diseño para la primera revisión. Cada tipo sigue el dominio de su dato y conserva la semántica al cruzar Python, CLI, escritorio y archivos.

| Entidad | Datos y condiciones |
| --- | --- |
| Bits | Vector estrictamente binario y unidimensional, con longitud útil positiva. Agrupamiento MSB primero. Si se permite completar el último grupo, se añaden ceros al final y se guarda el número de bits útiles. |
| Símbolos | Etiquetas enteras válidas en la constelación, orden temporal, bits útiles y tasa de símbolos cuando existe un reloj. Una etiqueta codifica la palabra de bits y se distingue de la posición geométrica usada para el patrón Gray. |
| Constelación | Familia, orden binario, mapeo, rotación en radianes, normalización y geometría determinista. Validar M-PSK con órdenes potencia de dos y QAM cuadrada para `M = 4^k`. Indicar distancia mínima y energía media bajo símbolos equiprobables. |
| I/Q | Registro `Signal` discreto complejo, origen, frecuencia de muestreo en Hz, referencia temporal, tasa de símbolos y muestras por símbolo de valor entero cuando corresponda. Frecuencia central opcional y explícita, independiente de la representación en banda base. |
| Pulso y filtros | Familia y parámetros válidos, grilla simétrica en unidades de período de símbolo, versión FIR causal y retardo en muestras. Normalizaciones seleccionadas por energía unitaria o pico central unitario, con energía y ganancia registradas. |
| Canal y reloj | Modo SNR, Es/N0 o Eb/N0 en dB, semilla y algoritmo, potencia de referencia, tipo real o complejo, energía o bits/símbolo cuando apliquen, varianzas nominal y observada. El reloj de la señal queda explícito. |
| Sincronización | Estado ideal, asistido, estimado o no disponible. Posición en muestras, fase, evidencia o criterio de selección, intervalo buscado y estado de alineación. El modo ideal indica que usa el retardo conocido. El modo asistido identifica los datos suministrados. La estimación registra método y uso del piloto. |
| Calidad | Conteos de bits y símbolos, errores, universo evaluado, exclusiones y referencia. EVM RMS, porcentaje y dB cuando corresponde. Métrica sin referencia, sin energía o sin alineación tiene estado explícito. |
| Experimento | Configuración normalizada, versión, semilla y flujo RNG, revisión del motor, huellas y relaciones de entradas y resultados, parámetros de sincronización y ventanas. |
| Barrido | Configuración base, ejes declarados, orden de recorrida, política de semillas y criterios de detención. Solo incorpora al índice resultados con proyecto validado. |

Las configuraciones distinguen la tasa de bits útil, cuando corresponde, de la tasa nominal sin codificación `Rb = k Rs`. Deben especificar transitorios, muestras y relleno excluidos de cada medición. Un registro guarda valores de energía según la normalización discreta adoptada y la conversión a unidades físicas requiere contexto adicional. [Convenciones matemáticas](MATHEMATICAL_FOUNDATIONS.md)

Las etiquetas de símbolo se guardan con su orden de modulación y número de bits útiles. Los I/Q exportados como `Signal` temporal conservan el índice `n` y documentan el reloj físico. El Core interpreta la unidad `k` como armónicos de Fourier y la reserva para ese uso. Una amplitud de símbolo exportada como señal discreta registra una muestra por símbolo. Un registro sobremuestreado indica el cociente entero entre la tasa de muestras y la de símbolos.

Para persistir entradas compactas, el diseño inicial usa longitud y orden de bits explícitos junto a los bytes codificados. La lectura verifica la longitud esperada antes de decodificar y comprueba que el relleno externo a la secuencia sea cero. Las etiquetas usan un ancho y orden de bytes explícitos. Las relaciones con señales se expresan mediante los padres del proyecto, de modo que importar un subconjunto pueda conservar y verificar su procedencia.
