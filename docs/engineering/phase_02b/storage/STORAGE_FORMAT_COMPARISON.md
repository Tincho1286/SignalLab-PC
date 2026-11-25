# Comparación de formatos científicos

| Alternativa | Alcance | Lectura parcial e integridad |
| --- | --- | --- |
| JSON | Formato histórico del proyecto. Legible y autoexplicativo. | Recorre el documento completo. Reemplazo atómico actual. |
| NPY | Arreglo con forma y dtype. Adecuado para cálculo. | mmap de rangos y sin procedencia de la señal. Usar `allow_pickle=False`. |
| NPZ | Arreglos en ZIP con compresión opcional. | El miembro comprimido se descomprime. Los tamaños declarados necesitan límites. |
| HDF5 | Arreglos, conjuntos de datos, jerarquía y corte parcial. | Requiere HDF5 y políticas sobre grupos, filtros, enlaces y referencias externas. |
| SigMF | Intercambio I/Q y metadatos de captura. | Lectura por desplazamiento. El par de archivos tiene dos puntos de reemplazo y necesita un contrato de intercambio. |
| Híbrido | Cabecera JSON acotada y datos binarios con tipo explícito. | Desplazamiento calculable. Un hash de contenido valida la lectura íntegra en un archivo. |

Los prototipos auxiliares de benchmark consumen exclusivamente sus propios archivos sintéticos. La [medición](STORAGE_BENCHMARK_REPORT.md) decide la opción experimental. [Documentación NumPy](https://numpy.org/doc/stable/reference/generated/numpy.load.html) · [Especificación SigMF](https://sigmf.org/)
