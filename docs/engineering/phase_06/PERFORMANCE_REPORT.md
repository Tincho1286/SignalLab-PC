# Protocolo de rendimiento

`tools/measure_rf.py` ejecuta dos tamaños por perfil en procesos separados con un hilo numérico. Cada prueba verifica al menos una relación física o matemática antes de registrar el tiempo. Se registra RSS máximo del proceso, mayor reserva observada en el perfil y parámetros. Las reservas son estimaciones de admisión. RSS incluye el intérprete y las bibliotecas que importa el perfil.

| Perfil | Tamaño base / doble |
| --- | --- |
| Conversión y medidas de red | 2 048 / 4 096 frecuencias de cuatro puertos |
| Cascada de dos líneas | 8 192 / 16 384 frecuencias |
| Intercambio Touchstone | 4 096 / 8 192 frecuencias de dos puertos |
| Bessel de orden ocho | 8 192 / 16 384 frecuencias para el retardo |
| Espectros | Registros de 8 192 / 16 384 muestras, Zoom FFT y contorno radial |
| Incertidumbre | 16 / 32 perturbaciones y 24 / 48 réplicas |
| Proyecto | 16 384 / 32 768 frecuencias de dos puertos en SLPROJ |

La cancelación mide el intervalo desde la señal hasta el descarte cooperativo en una importación iniciada. El ensayo vuelve a abrir el archivo para comprobar recuperación. El Workbench mide arranque, primera apertura por herramienta, navegación entre documentos abiertos y render por separado. El perfil automatizado de Qt usa offscreen.

## Resultados del candidato

SHA `1eb462e24034a9c7f41183b4da4654334460d07c`. [Ejecución](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46094545163)

| Plataforma | Arranque | Primera apertura, máximo | Navegación abierta, mediana/máximo | Render | Cancelación | RSS de escritorio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Windows Server 2022 | 212.84 ms | 236.67 ms | 21.32 ms / 131.10 ms | 62.42 ms | 0.11 ms | 284.2 MiB |
| Ubuntu 22.04 | 167.43 ms | 128.18 ms | 3.63 ms / 38.84 ms | 45.47 ms | 0.06 ms | 311.8 MiB |

| Plataforma | Perfil doble | Tiempo | RSS máximo | Mayor reserva individual |
| --- | --- | ---: | ---: | ---: |
| Windows Server 2022 | multiport | 23.29 ms | 106.4 MiB | 8.44 MiB |
| Windows Server 2022 | cascade | 25.85 ms | 108.9 MiB | 6.56 MiB |
| Windows Server 2022 | touchstone | 259.79 ms | 103.7 MiB | 2.81 MiB |
| Windows Server 2022 | filter | 7.20 ms | 100.6 MiB | 3.13 MiB |
| Windows Server 2022 | spectral | 54.25 ms | 102.0 MiB | 4.53 MiB |
| Windows Server 2022 | uncertainty | 95.48 ms | 100.4 MiB | 0.39 MiB |
| Windows Server 2022 | archive | 185.48 ms | 120.1 MiB | 16.50 MiB |
| Ubuntu 22.04 | multiport | 14.19 ms | 116.0 MiB | 8.44 MiB |
| Ubuntu 22.04 | cascade | 17.42 ms | 118.7 MiB | 6.56 MiB |
| Ubuntu 22.04 | touchstone | 232.02 ms | 113.7 MiB | 2.81 MiB |
| Ubuntu 22.04 | filter | 7.10 ms | 110.2 MiB | 3.13 MiB |
| Ubuntu 22.04 | spectral | 30.40 ms | 111.3 MiB | 4.53 MiB |
| Ubuntu 22.04 | uncertainty | 41.67 ms | 110.0 MiB | 0.39 MiB |
| Ubuntu 22.04 | archive | 103.23 ms | 134.3 MiB | 16.50 MiB |
