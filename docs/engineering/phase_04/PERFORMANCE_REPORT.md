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

### Windows y Linux en la matriz

Ambos runners usaron `2a0a3fd` y reabrieron los tres perfiles con el mismo informe, reloj y muestras. Los tiempos incluyen las operaciones indicadas en cada columna. RSS incluye el arranque del proceso. Los tamaños de archivo reflejan la compresión en cada entorno.

| Sistema | Símbolos | Cálculo (s) | Guardado (s) | Apertura y verificación (s) | SLPROJ (bytes) | Pico RSS (bytes) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Windows Server 2022 | 128 | 0,027 | 0,026 | 0,017 | 345 440 | 106 401 792 |
| Windows Server 2022 | 2 048 | 0,047 | 0,060 | 0,028 | 3 854 230 | 116 461 568 |
| Windows Server 2022 | 65 536 | 0,809 | 1,102 | 0,317 | 119 867 955 | 466 124 800 |
| Ubuntu 22.04 | 128 | 0,021 | 0,011 | 0,011 | 345 087 | 115 027 968 |
| Ubuntu 22.04 | 2 048 | 0,032 | 0,025 | 0,018 | 3 853 686 | 126 582 784 |
| Ubuntu 22.04 | 65 536 | 0,484 | 0,615 | 0,219 | 119 867 582 | 475 701 248 |

La cancelación de Clarke tardó 0,02662 s en Windows y 0,01437 s en Linux. Durante la entrega del archivo tardó 0,00927 y 0,00692 s. Los intervalos máximos del ciclo de eventos offscreen fueron 0,15939 y 0,10018 s. El archivo existente se conservó en ambos entornos y la reserva ensayada de 350 MiB rechazó un segundo cálculo concurrente y permitió reintentarlo con las mismas huellas. [Windows](evidence/candidate-2a0a3fd/windows-channel-modeling-performance.json) · [Linux](evidence/candidate-2a0a3fd/linux-channel-modeling-performance.json).

## Escalado con trayectorias y réplicas

Se midieron tres tamaños de cada operación en Windows con CPython 3.14.10, Qt bloqueado y un hilo BLAS/OMP. Cada fila corresponde a un proceso nuevo. Para fading Clarke se mantuvieron 32 768 muestras a 96 kHz, Doppler máximo de 64 Hz y potencia media total unitaria. En cada caso se reconstruyó la señal exactamente a partir de los coeficientes entregados y los retardos de cada trayectoria.

| Trayectorias | Tiempo de cálculo (s) | Coeficientes retenidos (MiB) | Pico RSS (MiB) |
| ---: | ---: | ---: | ---: |
| 1 | 0,015 | 0,50 | 105,00 |
| 4 | 0,021 | 2,00 | 107,13 |
| 16 | 0,045 | 8,00 | 113,27 |

La campaña usó un punto a Eb/N₀ de 6 dB y 256 bits por réplica. Se volvió a abrir cada catálogo y se cotejaron todas las corridas. El espacio de archivo creció de 0,15 a 2,37 MiB. La tabla cubre este perfil local, con un número acotado de réplicas.

| Réplicas | Ejecutar y guardar (s) | Reabrir y verificar (s) | Archivos (MiB) | Pico RSS (MiB) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0,119 | 0,016 | 0,15 | 103,48 |
| 4 | 0,272 | 0,041 | 0,60 | 103,97 |
| 16 | 0,967 | 0,141 | 2,37 | 104,38 |

[Mediciones de escalado](evidence/candidate-2a0a3fd/windows-scaling.json) · [Procedimiento](evidence/candidate-2a0a3fd/scaling-audit.py).
