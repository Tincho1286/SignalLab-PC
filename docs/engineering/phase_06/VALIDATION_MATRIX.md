# Matriz de validación RF

| Control | Oráculo o recorrido | Evidencia reproducible |
| --- | --- | --- |
| RF-01 · Contratos | Mutación de entradas, fases y unidades. Reflexión de resistencias, abierto, corto y adaptación | `test_rf_network` |
| RF-02 · Redes | Divisor serie, derivación, cascada, terminación multipuerto, singularidades, nulos y pendiente | `test_rf_network` y demostrador A |
| RF-03 · Líneas | Cuarto y media onda, condición sin distorsión, ajuste directo de admitancias y cruce de Smith | `test_rf_line_matching` y demostrador B |
| RF-04 · Filtros | Polinomio Bessel inverso, sustituciones de frecuencia, derivada de fase, impulso y escalón | `test_rf_link_bessel`, regresiones LTI y demostrador C |
| RF-05 · Enlace | Espacio libre, ruido acumulado por etapa, proyección armónica y potencia en W/dBm | `test_rf_link_bessel` y demostrador D |
| RF-06 · Fourier | Sumatoria compleja con origen, polinomio de Laurent, seno fuera de bin y vector de concentración DPSS | `test_advanced_fourier` y demostrador E |
| RF-07 · Experimentos | Diferencias finitas contra derivadas cerradas, trayectoria de Friis y réplicas interrumpidas frente a completas | `test_rf_experiments` |
| RF-08 · Operación y almacenamiento | RI/MA/DB, Z/Y normalizados, orden de puertos, documentos dañados, hash, paridad CLI/Python y Workbench | `test_touchstone_rf_storage`, `test_rf_application`, `test_rf_workbench` y demostrador F |

La ejecución `tools/qualify_rf.py` usa los registros integrales del candidato. Los demostradores guardan sus controles numéricos, tolerancias y huellas por plataforma.
