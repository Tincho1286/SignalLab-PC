# Latencia de cancelación

`tools/measure_core_hardening.py` usa un temporizador y ejecuta el cálculo real. Las operaciones individuales disparan el temporizador al entrar en `ExecutionContext.run`. Pipeline y escrituras lo disparan al invocar la operación. El informe indica si la operación terminó antes de confirmar la cancelación y comprueba que no cambió el destino. El caso simbólico controla el proceso hijo y la eliminación del directorio temporal.

FFT, filtrado, conversión nativa, `fsync` y copias de objetos pueden retener el control hasta su próximo punto cooperativo. Las observaciones de este ensayo no establecen una latencia máxima.

Los dos sistemas cancelaron las ocho pruebas de 262 144 muestras y conservaron el destino. La latencia observada fue de 0,18 a 31,01 ms en Windows y de 0,14 a 23,45 ms en Linux. El proceso simbólico requirió 64,28 ms y 53,62 ms respectivamente, con limpieza del temporal. [Mediciones Windows](../validation/evidence/windows-performance-459b9fc.json) · [Mediciones Linux](../validation/evidence/linux-performance-459b9fc.json)
