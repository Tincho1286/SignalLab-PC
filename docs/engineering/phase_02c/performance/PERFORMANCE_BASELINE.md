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
