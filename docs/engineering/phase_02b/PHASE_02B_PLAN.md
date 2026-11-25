# Plan de Fase 02B

| Paquete | Depende de | Condición de salida |
| --- | --- | --- |
| WP-02B.00 | Piloto DFT | SHA limpio, referencias contrastadas y controles reproducibles. |
| WP-02B.01 | .00 | Contexto y procedencia compartidos sin Qt, con compatibilidad DFT. |
| WP-02B.02 | .01 | IDFT, FIR, resampling y PSD probados contra referencias independientes. |
| WP-02B.03 | .02 | Demostrador secuencial con reloj, dependencias y publicación íntegra. |
| WP-02B.04 | .03 | Comparación de formatos con mediciones y un máximo de un backend opcional. |
| WP-02B.05 | .04 | Ejecución y persistencia verificadas ante fallos, cancelación y contención. |
| WP-02B.06 | .05 | Contrato público experimental y ejemplos reproducibles. |
| WP-02B.07 | .06 | Matriz sobre un SHA limpio y dictamen de preparación para Fase 03. |

Cada paquete registra el criterio previo y el resultado. El estado por requisito se conserva en la [matriz](PHASE_02B_TRACEABILITY_MATRIX.md). El desarrollo usa `develop`. La autorización abarca la revisión de preparación para Fase 03.
