# Rendimiento y recuperación de Fase 05

`python -B -X utf8 tools/measure_statistics.py --output work/distribution-audit/statistical-performance.json` ejecuta los perfiles en procesos separados y conserva los resultados en JSON. El supervisor exige el mismo SHA limpio al comienzo y al final. Windows usa el pico de conjunto de trabajo del proceso. Linux usa el máximo residente publicado por `getrusage`. Ambos incluyen la carga de bibliotecas y las comprobaciones del perfil. Cada operación tiene un oráculo y se contrasta con un segundo tamaño al escalar el registro o el número de réplicas. [Protocolo estadístico](STATISTICAL_VALIDATION_PROTOCOL.md)

## Medición de desarrollo en Windows

Estos datos orientan la preparación del candidato. La matriz final medirá las dos plataformas sobre el mismo SHA de publicación.

| Perfil mayor | Carga probada | Tiempo (s) | RSS (MiB) | Mayor reserva solicitada (MiB) |
| --- | --- | ---: | ---: | ---: |
| Generación | 4 × 262 144 muestras gaussianas | 0,05 | 132,6 | 28,01 |
| Gaussiana conjunta y covarianza | 32 768 muestras y 8 componentes | 0,06 | 114,2 | 28,02 |
| Identificación ARMA | 8192 muestras, órdenes (1,1) y reserva del 12,5 % | 0,03 | 103,5 | 7,25 |
| Bartlett | 524 288 muestras, bloques de 2048 | 0,06 | 120,6 | 0,50 |
| Kalman | 4096 mediciones, un estado | 0,49 | 101,4 | 2,63 |
| NLMS | 32 768 muestras, 8 coeficientes y reserva del 12,5 % | 0,35 | 106,7 | 7,00 |
| Monte Carlo | 256 réplicas × 2048 muestras × 4 escenarios | 0,45 | 101,0 | 0,41 |
| Proyecto SLPROJ | 262 144 muestras complejas | 0,11 | 125,9 | 12,00 |

El perfil de Monte Carlo guardó 17 984 bytes de estadísticas por réplica y definición. El archivo SLPROJ ocupó 4 194 779 bytes, con 0,07 s de escritura y 0,02 s de lectura. Se verificaron el eje y el contenido al reabrir. La reserva mide la memoria de trabajo estimada por el motor. El proceso también conserva bibliotecas, entradas, oráculos y otros objetos. Bartlett reserva por bloque y recorre el registro ya cargado. Kalman conserva un historial de estados y covarianzas que crece con el número de mediciones y el cuadrado del tamaño del estado a dimensiones fijas de entrada y salida.

En el Workbench se simuló una campaña de 512 réplicas de 8192 muestras sin abandonar el cálculo en segundo plano. Se observaron 877 pulsos del temporizador de 10 ms, con un intervalo máximo de 115 ms. La medición usa Qt offscreen y una ventana de 940 × 700.

Se midió el tiempo entre la solicitud y la confirmación en puntos cooperativos elegidos. Kalman descartó su salida en menos de 0,1 ms. Monte Carlo detuvo la entrega en menos de 0,3 ms y preservó 64 réplicas completas. Continuar produjo los mismos recuentos que una ejecución nueva. Cancelar la sustitución de una sesión preservó su versión anterior en menos de 1,2 ms. Se rechazó una huella adulterada y se probó el rechazo de una solicitud que competía por la reserva de memoria mientras una campaña trabajaba en otro hilo. Tras finalizar la campaña, el reintento se completó. El plazo de cancelación observado se aplica a estos puntos cooperativos. La espera dentro de una llamada nativa aislada puede ser mayor.
