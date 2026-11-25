# Línea base de rendimiento

El banco local exploratorio en Windows 11 con CPython 3.14.10 usó tres repeticiones. Para 1 048 576 muestras obtuvo DFT 0,13 s, IDFT 0,09 s, FIR 0,14 s, resampling 0,06 s, Welch 0,65 s y pipeline 0,82 s. El pipeline alcanzó 247 640 064 bytes de pico residente con una estimación de 497 744 384 bytes.

La corrida local precede al candidato final. La matriz genera `core-performance.json` en ambos sistemas a partir del SHA bajo evaluación.
