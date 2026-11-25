# Rendimiento de Fase 02B

## Comparación de almacenamiento

Se reprodujo el costo de sesión histórica y se midieron 48 combinaciones por plataforma. Los resultados conservan la diferencia entre almacenamiento de una señal y un proyecto con dos arreglos. La lectura íntegra del prototipo con digest mantuvo equivalencia exacta. [Benchmark multiplataforma](../storage/STORAGE_BENCHMARK_REPORT.md)

## Backend experimental y demostrador

Medición local en Windows 11 sobre `8ad3066`, con entrada compleja de 65.536 muestras, una pasada de calentamiento y cinco repeticiones. Para reproducir, generar partes real e imaginaria con NumPy RNG 20261125 y medir `save_json` y `save_binary_signal` con `perf_counter` en temporales del mismo volumen. Reabrir cada archivo con su API de lectura, verificar sus muestras y registrar tamaño. El flujo usa 12.000 muestras/s, relación 2/3, FIR de 31 coeficientes y Welch por defecto.

| Caso | Escritura mediana | Lectura mediana | Tamaño |
| --- | ---: | ---: | ---: |
| JSON de señal | 643,4 ms | 137,5 ms | 4.539.263 bytes |
| SLBIN con integridad completa | 13,6 ms | 4,1 ms | 1.048.796 bytes |

El flujo completo en memoria tomó 46,3 ms de mediana, entre 45,6 y 48,7 ms. La reserva estimada fue 31.128.064 bytes y se refiere a entrada, resultados retenidos y temporales. El guardado de Project sigue usando JSON y se mide aparte. [Mediciones locales](../benchmarks/core-production-windows-8ad3066.json)
