# Rendimiento y recursos de Fase 03

## Referencia previa al laboratorio

La envolvente de 02C documenta FFT, FIR, remuestreo, estimación de PSD, concurrencia, cancelación y persistencia. La campaña sintética verificó 48 proyectos científicos y 288 registros sin mantener toda la campaña en memoria. Esa referencia orienta el presupuesto de I/Q, el filtrado y la persistencia. Las mediciones de comunicaciones se registrarán con sus operaciones y sus parámetros efectivos. [Envolvente de 02C](../phase_02c/resources/OPERATIONAL_ENVELOPE.md) · [Campaña y almacenamiento](../phase_02c/validation/FINAL_VALIDATION_MATRIX.md#distribución-recursos-y-almacenamiento-de-a80508c)

## Perfiles que se medirán

El dimensionamiento inicial usa 128, 2 048 y 65 536 símbolos, 8 muestras por símbolo y un span RRC de 10. Con $S$ símbolos, separación de $L$ muestras y $T$ coeficientes, el tren de impulsos ocupa $(S-1)L+1$ muestras. El FIR completo de transmisión usa $(S-1)L+T$ y el receptor usa $(S-1)L+2T-1$. La estimación incluye registros retenidos, hashes y temporales.

Una prueba local de escritura y reapertura en Windows verificó las muestras, el reloj y la procedencia del proyecto para seis registros sintéticos con esas longitudes. El manifiesto incluyó una secuencia de 2 bits por símbolo empaquetada y una etiqueta de 16 bits por símbolo, ambas codificadas en Base64. Los tiempos corresponden a una observación de escritura y otra de lectura por tamaño.

| Símbolos | Muestras sumadas | Manifiesto (B) | Archivo SLPROJ (B) | Guardado (s) | Apertura (s) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | 4 644 | 2 942 | 77 290 | 0,0388 | 0,0114 |
| 2 048 | 69 924 | 8 708 | 1 127 536 | 0,0107 | 0,0136 |
| 65 536 | 2 228 516 | 199 178 | 35 855 478 | 0,4567 | 0,0912 |

En el caso grande, 48 archivos con ese contenido suman aproximadamente 1,60 GiB. El límite de manifiesto de SLPROJ sigue en 16 MiB. El banco justifica evaluar la codificación compacta de datos discretos con el formato existente. Los ensayos con datos del laboratorio medirán persistencia y cancelación con huellas verificadas, además del consumo de disco con las salidas que se incluyan finalmente.

Se medirá en procesos frescos con versiones, plataforma y configuración numérica registradas. El informe distinguirá modulación, decisión, FIR, ruido, métricas, persistencia, barridos y el tiempo total. Se reportarán pico de memoria, retención por salida, cancelación en etapas distintas y capacidad de respuesta de Workbench. Las mediciones del laboratorio delimitarán los perfiles nuevos.

## Primera medición de modulación y filtrado

En Windows, CPython 3.14.10 y un hilo BLAS/OMP, se ejecutaron las primeras etapas sin importar Qt. El perfil QPSK usó RRC de 81 coeficientes, $β=0,35$, ocho muestras por símbolo y tasa de 12 ksym/s. Estos son tiempos de una corrida por tamaño, incluida la verificación de procedencia de cada FIR.

| Símbolos | Modulación (ms) | Inserción (ms) | FIR TX (ms) | FIR adaptado (ms) |
| ---: | ---: | ---: | ---: | ---: |
| 128 | 0,40 | 2,35 | 6,27 | 2,61 |
| 2 048 | 0,95 | 1,27 | 5,73 | 5,04 |
| 65 536 | 5,30 | 7,89 | 95,92 | 95,22 |

La corrida mayor produjo 524 441 muestras después del filtro adaptado. La cancelación antes y después de cada FIR es cooperativa. La medición de latencia dentro de perfiles completos incorporará el canal, la sincronización y la carga de escritorio.

## Búsqueda inicial de sincronización

El receptor procesa fases de sobremuestreo y ventanas en bloques de hasta 65 536 términos, ampliados al tamaño de una ventana si el piloto es mayor. La cancelación se consulta entre bloques. El límite de trabajo admite 16 777 216 términos por búsqueda. Se comprobó con el perfil máximo siguiente en Windows, un hilo BLAS/OMP, dos muestras por símbolo, fase inyectada de 0,55 rad y desplazamiento en la mitad de la búsqueda.

| Instantes candidatos | Símbolos de piloto | Términos | Tiempo (ms) |
| ---: | ---: | ---: | ---: |
| 256 | 16 | 4 096 | 5,37 |
| 4 096 | 64 | 262 144 | 6,26 |
| 65 536 | 256 | 16 777 216 | 174,52 |
