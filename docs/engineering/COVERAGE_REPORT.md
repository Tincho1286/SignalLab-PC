# Cobertura del candidato

La medición del commit de estabilización usa `coverage.py 7.17.5`, ramas activadas y datos paralelos por proceso. La ejecución instrumentada incluye la suite integral y el barrido matemático. [Configuración](../../tools/engineering.coveragerc) · [Baseline](BASELINE_REPORT.md)

Se informan líneas ejecutadas sobre líneas ejecutables y aristas recorridas sobre aristas posibles. Se comprueba la ejecución del worker simbólico dentro de archivos de cobertura separados. La terminación forzada puede impedir que un proceso escriba su último registro de cobertura. El alcance termina en el código Python de la aplicación.

| Métrica | Objetivo orientativo | Criterio |
| --- | ---: | --- |
| Global | 85 % | Líneas de la aplicación. Se informan las ramas en una columna propia. |
| `sampling.py` | 90 % | Líneas del motor más lectura de ramas conflictivas como reloj parcial, decimación y eje de salida. |
| `fourier.py` | 90 % | Líneas del motor incluyendo errores de rejilla, rangos y operaciones con reloj. |
| `filters.py`, `model.py`, `session.py` | Seguimiento | Priorizar tolerancias, invariantes de reloj, metadatos, restauración y entradas inválidas. |

La cobertura inicial de líneas de 77,95 % corresponde a `16ffcba` y tuvo un error ambiental de Git. El denominador y el alcance de proceso cambian en esta fase. Las cifras definitivas deben venir de los reportes Windows/Linux del SHA candidato.

## Diagnóstico de la primera corrida

Sobre `327a62c`, Linux ejecutó 794 pruebas con un fallo de sincronización del menú de gráficos. Se completaron los 150 casos preventivos con éxito. El proceso principal Windows terminó con una excepción nativa. La cobertura que se guardó allí corresponde a procesos que alcanzaron un cierre normal y no sirve como estimación global.

| Módulo | Linux · líneas | Linux · ramas |
| --- | ---: | ---: |
| Aplicación | 31.745/41.099 · 77,24 % | 10.157/15.904 · 63,86 % |
| Sampling | 190/294 · 64,63 % | 65/126 · 51,59 % |
| Fourier | 194/255 · 76,08 % | 37/84 · 44,05 % |
| Filters | 299/339 · 88,20 % | 128/182 · 70,33 % |
| Signal Model | 68/76 · 89,47 % | 26/32 · 81,25 % |
| Session | 20/24 · 83,33 % | 6/10 · 60,00 % |

Sampling deja huecos concentrados en las variantes de cuantización, punto fijo y alias. Parte del hueco de cuantización pertenece a las funciones del panel clásico, mientras que el escritorio principal usa la familia de precisión por separado. La cobertura conserva ambas rutas mientras sean parte del código distribuido. Fourier deja huecos en la energía global, la densidad espectral y la síntesis continua. Son prioridades para añadir oráculos sobre saturación, Parseval, normalización y referencia de reloj. Estas cifras pertenecen a la primera corrida. [Corrida inicial](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45542153305)

En el commit intermedio `e6d0ebc`, ambos sistemas guardaron 124 archivos de cobertura, de los cuales 122 contienen ejecución del worker simbólico. Windows completó la suite con 77,27 % de líneas y 63,90 % de ramas. Linux obtuvo 77,25 % de líneas y 63,88 % de ramas. Ambos registraron el fallo de sincronización del menú documentado en el informe de línea base. [Evidencia intermedia](evidence/intermediate-matrix-e6d0ebc.json)

## Referencia del candidato `1aac793`

| Módulo | Windows · líneas | Windows · ramas | Ubuntu · líneas | Ubuntu · ramas |
| --- | ---: | ---: | ---: | ---: |
| Aplicación | 31.760/41.101 · 77,27 % | 10.162/15.904 · 63,90 % | 31.749/41.101 · 77,25 % | 10.158/15.904 · 63,87 % |
| Sampling | 64,63 % | 51,59 % | 64,63 % | 51,59 % |
| Fourier | 76,08 % | 44,05 % | 76,08 % | 44,05 % |
| Filters | 88,20 % | 70,33 % | 88,20 % | 70,33 % |
| Signal Model | 89,47 % | 81,25 % | 89,47 % | 81,25 % |
| Session | 83,33 % | 60,00 % | 83,33 % | 60,00 % |
| Proceso simbólico | 80,77 % | 72,73 % | 80,77 % | 72,73 % |

Cada runner guardó 122 archivos con ejecución del worker simbólico de 124 archivos de cobertura en total. La matriz completó todos los controles. Los objetivos de cobertura global, Sampling y Fourier siguen abiertos. [Evidencias de la referencia](evidence/final-matrix-1aac793.json)
