# Contratos del Core

DFT, IDFT, aplicación FIR, ajuste de tasa y PSD validan que sus entradas conservan el contenido durante el cálculo. `store_dft`, `store_signal`, `store_fir_design` y `store_pipeline` validan el resultado durante la publicación. El flujo valida también los parámetros originales y la relación entre etapas. La cancelación atraviesa las comprobaciones por bloques y se verifica antes de publicar los registros.

`Project.add` sigue siendo la frontera general de registros, incluidos resultados legados. Las rutas verificadas entregan evidencia explícita al publicar. Los consumidores que usan directamente los motores científicos siguen teniendo acceso a sus resultados y a la estructura histórica.
