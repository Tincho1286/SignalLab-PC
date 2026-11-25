# Benchmark de almacenamiento científico

## Método

`python -B -X utf8 tools/benchmark_scientific_storage.py --output work/storage.json` genera los arreglos con semilla 20261125. Cada caso vive en un proceso nuevo y tiene un calentamiento y tres repeticiones. La evidencia contiene mediana, mínimo y máximo. La lectura mide caché después de escribir. Abrir un proceso nuevo no garantiza caché fría del sistema. El pico residente incluye el intérprete, bibliotecas y arreglos de referencia. Para HDF5 se usa un conjunto de datos sin compresión. NPZ se mide comprimido con ZIP. Los tiempos de escritura incluyen sincronización de archivos. Los prototipos sólo leen sus propios resultados.

Las 10.000.000 de muestras requieren una estimación de 2,56 GB con la regla de 256 bytes por muestra y exceden el tope de 512 MiB por caso. Se midieron 48 combinaciones por plataforma disponible hasta 1.048.576 muestras, con verificación exacta de valores completos y de 32 muestras parciales.

## Windows local

El ejercicio con dos arreglos en una sesión histórica de 65.536 muestras se reprodujo en 1,248 s de publicación y guardado y 0,836 s de reapertura. El archivo midió 13.181.675 bytes. La corrida histórica anterior registró 1,90 s con otra carga del equipo. Para comparar formatos se usó una sola señal por caso.

| Complejo, 65.536 muestras | Escritura mediana | Lectura mediana | Tamaño |
| --- | ---: | ---: | ---: |
| JSON de señal | 397 ms | 86 ms | 4.539.204 bytes |
| NPY | 10 ms | 1 ms | 1.048.704 bytes |
| NPZ | 48 ms | 6 ms | 1.006.275 bytes |
| HDF5 | 11 ms | 2 ms | 1.049.976 bytes |
| SigMF | 16 ms | 1 ms | 1.048.782 bytes |
| Híbrido con digest | 14 ms | 3 ms | 1.048.715 bytes |

Con 1.048.576 complejas, el híbrido prototipo tomó 0,121 s de escritura y 0,033 s de lectura, con 114 MiB de pico residente. JSON de señal tomó 6,090 s y 1,490 s, con 344 MiB de pico. NPZ ocupó menos espacio que NPY para este vector y tardó 0,860 s en escribir. Las diferencias de tamaño entre formatos reales y complejos se informan en la evidencia. JSON usa `Signal`, que materializa pares complejos incluso para entradas reales. [Datos Windows local](../benchmarks/storage-windows-local-a3b6254.json)
