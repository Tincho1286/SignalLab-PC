# Latencia de cancelación

`tools/measure_core_hardening.py` usa un temporizador y ejecuta el cálculo real. Las operaciones individuales disparan el temporizador al entrar en `ExecutionContext.run`. Pipeline y escrituras lo disparan al invocar la operación. El informe indica si la operación terminó antes de confirmar la cancelación y comprueba que no cambió el destino. El caso simbólico controla el proceso hijo y la eliminación del directorio temporal.

FFT, filtrado, conversión nativa, `fsync` y copias de objetos pueden retener el control hasta su próximo punto cooperativo. Las observaciones de este ensayo no establecen una latencia máxima.
