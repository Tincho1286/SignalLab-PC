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

## Referencia de `develop` con CPython 3.14.10

| Módulo | Windows · líneas | Windows · ramas | Ubuntu · líneas | Ubuntu · ramas |
| --- | ---: | ---: | ---: | ---: |
| Aplicación | 31.773/40.980 · 77,53 % | 10.078/15.908 · 63,35 % | 31.763/40.980 · 77,51 % | 10.075/15.908 · 63,33 % |
| Muestreo | 280/304 · 92,11 % | 98/130 · 75,38 % | 280/304 · 92,11 % | 98/130 · 75,38 % |
| Fourier | 235/257 · 91,44 % | 51/84 · 60,71 % | 235/257 · 91,44 % | 51/84 · 60,71 % |
| Filters | 88,13 % | 67,03 % | 88,13 % | 67,03 % |
| Signal Model | 89,33 % | 78,12 % | 89,33 % | 78,12 % |
| Session | 83,33 % | 60,00 % | 83,33 % | 60,00 % |
| Proceso simbólico | 80,77 % | 72,73 % | 80,77 % | 72,73 % |

Muestreo y Fourier alcanzaron el 90 % orientativo de líneas con nuevas referencias independientes. La cobertura global sigue por debajo del 85 % orientativo. La actualización del intérprete y los cambios de código alteraron los denominadores de la medición. Cada runner guardó 122 archivos con ejecución del worker simbólico. [Evidencias de `ccb6a86`](evidence/cpython-31410-ccb6a86.json)

## Candidato de cierre `853bd67`

| Módulo | Windows · líneas | Windows · ramas | Ubuntu · líneas | Ubuntu · ramas |
| --- | ---: | ---: | ---: | ---: |
| Aplicación | 31.784/40.980 · 77,56 % | 10.084/15.908 · 63,39 % | 31.772/40.980 · 77,53 % | 10.079/15.908 · 63,36 % |
| Muestreo | 92,11 % | 75,38 % | 92,11 % | 75,38 % |
| Fourier | 91,44 % | 60,71 % | 91,44 % | 60,71 % |
| Filtros | 88,13 % | 67,03 % | 88,13 % | 67,03 % |
| Modelo de señal | 89,33 % | 78,12 % | 89,33 % | 78,12 % |
| Sesión | 83,33 % | 60,00 % | 83,33 % | 60,00 % |
| Proyectos | 95,41 % | 83,33 % | 95,41 % | 83,33 % |
| Diagramas | 92,17 % | 82,56 % | 92,17 % | 82,56 % |
| Motor CAS | 93,35 % | 74,85 % | 93,35 % | 74,85 % |
| Importación al CAS | 85,37 % | 79,55 % | 85,37 % | 79,55 % |
| Condiciones de sistemas | 97,30 % | 92,86 % | 97,30 % | 92,86 % |

Los dos sistemas pasaron 821 pruebas y 150 casos preventivos. En cada sistema, 122 de los 124 archivos de cobertura contienen ejecución del proceso simbólico. Las huellas de fuente coinciden y el candidato usa el mismo denominador que `ccb6a86`. Se cubrieron 11 líneas y 6 ramas adicionales en Windows, y 9 líneas y 4 ramas adicionales en Ubuntu. [Evidencia de cobertura](evidence/phase-01-coverage-853bd67.json)

La excepción al objetivo orientativo del 85 % global representa 3.049 líneas en Windows y 3.061 en Ubuntu. Entre las brechas mayores por archivo están `toolbox.py` con 493 líneas, `course_tools_panel.py` con 250–253, `ui.py` con 249, `workbench.py` con 235 y `pole_zero_editor.py` con 200. Las nuevas pruebas priorizan la semántica de la ROC, la preservación de relojes, el rechazo atómico de proyectos inválidos, la respuesta de sistemas con avances y la reutilización matemática del CAS. La matriz conserva las ramas de interfaz en el denominador. Las pruebas nativas de instaladores y la inspección visual aportan evidencia de integración fuera de la corrida instrumentada. El objetivo global queda abierto sin cambiar el denominador ni los criterios numéricos. [Cierre de Fase 01](PHASE_01_CLOSEOUT.md)
