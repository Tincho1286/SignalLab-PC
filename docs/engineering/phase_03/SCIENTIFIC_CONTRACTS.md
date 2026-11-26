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

## Bits, reloj y constelaciones en Python

`communications_data` define `BitSequence`, `SymbolSequence`, `SymbolClock` y `ConstellationSpec`. `communications_modulation` genera bits con PCG64 y semilla entera de 0 a 2¹²⁸−1, agrupa y desagrupa palabras MSB primero y produce puntos I/Q. La reproducción usa la versión fijada de NumPy. La rotación se expresa en radianes y la escala geométrica de PSK ya tiene energía unitaria. El contrato de etiqueta usa 32 bits, con reserva de memoria independiente para construir la constelación completa.

```python
from signallab_pc.communications_data import ConstellationSpec, SymbolClock
from signallab_pc.communications_modulation import (
    decide_symbols, group_bits, modulate, parse_bits, ungroup_symbols,
)

spec = ConstellationSpec("psk", 4, rotation_rad=0.7853981633974483)
bits = parse_bits("10 01 11")
symbols = group_bits(bits, spec, clock=SymbolClock(2400))
iq = modulate(symbols, spec)
decoded = ungroup_symbols(decide_symbols(iq, spec))
assert decoded.values.tolist() == bits.values.tolist()
```

La decisión recibe observaciones alineadas, a una muestra por símbolo. En la frontera de sectores PSK selecciona la posición siguiente en sentido antihorario. En cero usa la posición geométrica 0. QAM resuelve el empate hacia el nivel superior de cada eje. Las etiquetas de entrada y los resultados binarios tienen buffers de sólo lectura.

## Canal y alineación

`AWGNSpec` especifica modo de referencia, magnitud en dB, dominio y semilla. El modo SNR mide potencia sobre todo el registro finito o usa la referencia suministrada. Es/N₀ y Eb/N₀ requieren Es discreta y, para Eb/N₀, los bits por símbolo. `NoiseStatistics` distingue potencia medida, potencia de referencia, N₀ y varianzas por cuadratura. Sus varianzas observadas describen los valores de ruido generados antes del redondeo de la suma. La semilla, PCG64, la versión de NumPy y el hash de la señal de entrada quedan en el resultado.

`SynchronizationSpec` distingue el retardo conocido, el alineamiento aportado y la búsqueda por correlación normalizada con un piloto. Los índices de búsqueda y de muestreo se miden desde la primera muestra del registro. El receptor devuelve también el índice absoluto del registro, la fase compensada, la ganancia aplicada, el intervalo y las puntuaciones si estima. Una correlación insuficiente, un máximo ambiguo o un registro incompleto devuelven un estado de indisponibilidad con causa y sin muestras de salida. La búsqueda admite hasta 16 777 216 productos entre ventanas y piloto, además del presupuesto de memoria.
