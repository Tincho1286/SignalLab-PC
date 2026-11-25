# Reproducibilidad de las mediciones

Ejecutá `python -B -X utf8 tools/measure_core_hardening.py --output work/core-performance.json`. Cada combinación se inicia en otro proceso. Se usa una semilla fija, una ejecución de calentamiento, tres repeticiones y un hilo BLAS/OMP. El informe retiene tiempos individuales, medianas CPU y pared, pico residente, archivos, plataforma y versiones. En simbólico, CPU mide el coordinador y la pared incluye el proceso hijo. Los casos de disco usan caché caliente.

La comparación con Fase 02B usa sólo perfiles y cargas equivalentes. El banco agregado de 02C incorpora verificación de procedencia y costos de proyecto que el banco de núcleos de 02B no separaba.
