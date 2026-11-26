# Rendimiento y límites de Fase 04

## Perfil integrado

El perfil fijo usa QPSK Gray, 12 ksímbolos/s, RRC de 81 coeficientes y ocho muestras por símbolo. Fs es 96 kHz. La cadena aplica tres trayectorias LTI, dos ramas de fading Clarke a 64 Hz, un CFO de 19 Hz, fase Wiener, desequilibrio I/Q e interferencia de banda limitada. Se agrega AWGN a Eb/N₀ de 10 dB. Los retardos de ecos son 0, 5 y 9 muestras para multitrayecto y 0 y 4 para fading. El programa de medición guarda la configuración exacta y usa las mismas semillas en ambas plataformas.

Cada tamaño se ejecuta en un proceso nuevo con un hilo BLAS/OMP. El ensayo guarda el proyecto, lo vuelve a abrir y contrasta el informe y las muestras de la salida del canal y del filtro adaptado. El pico RSS incluye el proceso Python, sus bibliotecas, y la superposición de resultados vivos con el proyecto reabierto. La reserva compartida contabiliza estimaciones de memoria activa y cumple una función de admisión cooperativa.

### Exploración inicial en Windows

Resultados de `2644391`. La generación y reapertura se hicieron con las importaciones de Qt bloqueadas. El equipo estaba ejecutando en paralelo la línea base integral, por lo que los tiempos son orientativos.

| Símbolos | Muestras TX | SLPROJ (MiB) | Pico RSS (MiB) | Cálculo (s) | Guardado (s) | Apertura y verificación (s) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | 1 097 | 0,33 | 105,82 | 0,024 | 0,019 | 0,052 |
| 2 048 | 16 457 | 3,68 | 116,19 | 0,041 | 0,047 | 0,032 |
| 65 536 | 524 361 | 114,31 | 449,53 | 0,768 | 1,190 | 0,374 |

La exploración del perfil de 65 536 símbolos registró 0,042 s desde el pedido de cancelación al entrar a una transformada Clarke hasta recuperar el control y 0,012 s al abortar la entrega atómica de SLPROJ. Al cancelar el guardado o rechazarlo por presupuesto, el archivo previo se conservó byte por byte y se reabrió correctamente. El ensayo de concurrencia usó una reserva de 350 MiB de estimaciones. Mientras el primer enlace estaba en la transformada Clarke, se rechazó un segundo enlace del mismo tamaño. Al liberar la reserva se pudieron completar el primer cálculo y el reintento con las mismas huellas.

En Qt offscreen se midió un hueco máximo de 0,152 s en el ciclo de eventos mientras se ejecutaba el perfil integrado. La ventana de prueba tenía 940 × 700 píxeles. Este resultado corresponde al ensayo automatizado. Las comprobaciones de resolución, DPI y comportamiento en escritorio se registran aparte.

## Repetición sobre el candidato

```sh
python -B -X utf8 tools/measure_channel_modeling.py --output work/channel-modeling-performance.json
```

El perfil de calificación admite hasta 65 536 símbolos con los parámetros indicados. Otros tamaños, más etapas, mayores retardos, tasas distintas, Doppler más cercano a Nyquist o importación de señales grandes pueden requerir reservas y archivos mayores. El presupuesto y los plazos operan en los puntos de control del servicio. Una llamada nativa iniciada puede tardar en devolver el control. La medición del candidato debe repetir ambos entornos sobre el mismo commit y verificar los límites de 1,5 s para cancelación y 2 s para el ciclo de eventos. [Criterios](QUALITY_GATE_CRITERIA.md)

La medición local del candidato `2a0a3fd` pasó las comprobaciones de recursos. El mayor perfil archivó y reabrió 119 867 937 bytes y alcanzó un pico RSS de 471 789 568 bytes. Se observaron 0,03650 s de cancelación en Clarke y 0,01042 s en SLPROJ. El mayor intervalo observado en Workbench offscreen fue 0,14567 s. [Mediciones locales de Windows](evidence/candidate-2a0a3fd/windows-local-performance.json)

En Ubuntu 22.04, sobre el mismo commit, el mayor perfil archivó y reabrió 119 867 582 bytes y alcanzó un pico RSS de 475 701 248 bytes. La ejecución de ese perfil duró 0,48421 s y la escritura 0,61468 s. Las cancelaciones de Clarke y de entrega del archivo tardaron 0,01437 y 0,00692 s. Qt offscreen registró un intervalo máximo de 0,10018 s. El rechazo concurrente, la reanudación y la preservación del proyecto pasaron con el presupuesto ensayado. [Mediciones Linux de la matriz](evidence/candidate-2a0a3fd/linux-channel-modeling-performance.json)
