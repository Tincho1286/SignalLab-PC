# Línea base de rendimiento

El banco local exploratorio en Windows 11 con CPython 3.14.10 usó tres repeticiones. Para 1 048 576 muestras obtuvo DFT 0,13 s, IDFT 0,09 s, FIR 0,14 s, resampling 0,06 s, Welch 0,65 s y pipeline 0,82 s. El pipeline alcanzó 247 640 064 bytes de pico residente con una estimación de 497 744 384 bytes.

El candidato `459b9fc` completó 57 perfiles en cada plataforma. El tiempo es la mediana de tres repeticiones.

| Operación | Tamaño de entrada | Windows | Ubuntu |
| --- | ---: | ---: | ---: |
| DFT | 1 048 576 | 0,086 s | 0,093 s |
| IDFT | 1 048 576 | 0,081 s | 0,078 s |
| FIR | 1 048 576 | 0,085 s | 0,076 s |
| Cambio de tasa 2/3 | 1 048 576 | 0,069 s | 0,121 s |
| Welch | 1 048 576 | 0,449 s | 0,439 s |
| Pipeline | 1 048 576 | 0,599 s | 0,658 s |
| Publicación de DFT | 262 144 | 0,990 s | 1,297 s |
| Guardado de sesión | 262 144 | 3,809 s | 3,951 s |
| Reapertura de sesión | 262 144 | 2,815 s | 3,393 s |
| Escritura SLBIN | 1 048 576 | 0,097 s | 0,033 s |
| Lectura SLBIN | 1 048 576 | 0,020 s | 0,031 s |
| Transformada simbólica de referencia | Un proceso hijo | 0,933 s | 0,866 s |

El pipeline alcanzó 244,6 MB de pico residente en Windows y 253,2 MB en Ubuntu. El JSON de dos registros a 262 144 muestras ocupó 48,6 MB y 46,5 MB, respectivamente. El SLBIN de una señal del mismo tamaño ocupó aproximadamente 4,19 MB en ambos. Estos perfiles incluyen distintos números de registros y metadatos. [Banco Windows](../validation/evidence/windows-performance-459b9fc.json) · [Banco Linux](../validation/evidence/linux-performance-459b9fc.json)

## Comparación con el candidato faef335

Los perfiles equivalentes de `54adaa0` usan las mismas entradas, un hilo BLAS/OMP, un calentamiento y tres repeticiones. El cambio a NumPy 2.5.5 y SciPy 1.18.1 mantiene tiempos y RSS similares en los motores principales. La presión de I/O en runners compartidos afecta las mediciones de guardado. La comparación requiere repetir en el mismo equipo si una diferencia supera el umbral de investigación.

| Operación | Perfil | Windows faef335 → 54adaa0 | Linux faef335 → 54adaa0 |
| --- | --- | ---: | ---: |
| DFT | 1 048 576 bins | 62,13 → 58,26 ms | 77,17 → 75,81 ms |
| IDFT | 1 048 576 bins | 54,09 → 52,93 ms | 65,02 → 62,37 ms |
| FIR | 1 048 576 muestras | 58,55 → 58,72 ms | 82,68 → 79,56 ms |
| Welch | 1 048 576 muestras | 244,80 → 249,17 ms | 269,48 → 264,51 ms |
| Pipeline | 1 048 576 muestras | 398,68 → 391,39 ms | 507,78 → 510,46 ms |
| SLPROJ guardar | Dos registros de 1 048 576 | 196,55 → 207,22 ms | 207,60 → 163,46 ms |
| SLPROJ abrir | Dos registros de 1 048 576 | 50,70 → 50,83 ms | 56,37 → 56,14 ms |
| JSON abrir | Dos registros de 262 144 | 376,99 → 356,89 ms | 638,40 → 626,91 ms |

El pipeline usó 233,34 MiB en Windows y 241,02 MiB en Linux, frente a 233,66 y 241,91 MiB. El banco añadió importación MAT clásica y HDF5. Los artefactos conservan los tiempos de cada repetición, RSS, hardware, sistema, dependencias y semilla. [Banco Windows](../validation/evidence/windows-performance-54adaa0.json) · [Banco Linux](../validation/evidence/linux-performance-54adaa0.json)
