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

## Envolvente de comunicaciones

Workbench conserva un trabajador de cálculo por ventana. Python y CLI ingresan al presupuesto compartido de su proceso. De forma predeterminada, se admite una estimación de hasta el 35 % de la memoria disponible que informa el sistema, incluida la restricción cgroup en Linux cuando está presente. La API permite fijar un máximo de trabajo y un plazo cooperativo. Las cifras son presupuestos de admisión. El uso máximo real se mide por proceso e incluye dependencias y temporales nativos.

Para `S` símbolos, `L` muestras por símbolo y `T` coeficientes, la salida adaptada usa `(S−1)L+2T−1` muestras para un enlace sin piloto. La admisión considera también los registros intermedios, los componentes I/Q, el ruido y los buffers FIR. Una búsqueda por piloto admite hasta 16 777 216 términos. Un barrido admite hasta 1 024 combinaciones, con un escritor por carpeta y una corrida activa a la vez. El límite de cabecera SLPROJ es de 16 MiB y el de registros es de 10 000. Persistir cada combinación consume espacio proporcional a las muestras retenidas. Por ejemplo, 1 024 archivos iguales al perfil QPSK de 65 536 símbolos ocuparían aproximadamente 34,25 GiB, más los temporales y el catálogo.

FIR, AWGN y persistencia se cancelan en puntos de control. En FIR, una llamada nativa en curso puede tener que volver antes de confirmar la cancelación. Los perfiles grandes verificados corresponden a QPSK a 12 ksym/s, ocho muestras por símbolo y 81 coeficientes. Cambiar modulación, span, reloj, cantidad de símbolos o piloto cambia el presupuesto y puede modificar los tiempos. [Modelos de referencia](MATHEMATICAL_FOUNDATIONS.md) · [Política de recursos de 02C](../phase_02c/resources/OPERATIONAL_ENVELOPE.md)

## Medición del candidato `441f1c2`

La matriz ejecutó `python -B -X utf8 tools/measure_communications.py --output work/distribution-audit/communications-performance.json` desde el SHA limpio. Cada tamaño se midió en un proceso fresco con CPython 3.14.10 y un hilo BLAS/OMP. Las columnas de tiempo están en segundos. El enlace se midió sin Qt y la memoria es el pico RSS de todo el proceso. Cada archivo SLPROJ se reabrió, reconstruyó y comprobó contra el resultado original.

| Sistema | Símbolos | Enlace | Guardado | Reapertura | Pico RSS (MiB) | Archivo (bytes) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Windows | 128 | 0,0083 | 0,0172 | 0,0054 | 99,85 | 108 495 |
| Windows | 2 048 | 0,0150 | 0,0363 | 0,0073 | 101,66 | 1 159 438 |
| Windows | 65 536 | 0,2467 | 0,2251 | 0,0694 | 202,46 | 35 908 593 |
| Linux | 128 | 0,0099 | 0,0104 | 0,0060 | 107,89 | 108 229 |
| Linux | 2 048 | 0,0177 | 0,0136 | 0,0085 | 111,09 | 1 159 175 |
| Linux | 65 536 | 0,2487 | 0,2514 | 0,0861 | 222,73 | 35 908 327 |

En 65 536 símbolos, la modulación y la decisión ocuparon 5,2 y 6,5 ms en Windows y 4,5 y 5,1 ms en Linux. Los FIR de transmisión y recepción sumaron 133,4 y 126,5 ms, respectivamente. El ruido tardó 50,0 y 59,1 ms y las métricas 5,0 y 5,3 ms. Las respuestas adaptadas conservaron 524 441 muestras. El tamaño del archivo es específico de cada ejecución y de sus metadatos.

| Control | Windows | Linux |
| --- | ---: | ---: |
| Cancelación FIR desde la solicitud | 51,59 ms | 44,58 ms |
| Cancelación AWGN desde la solicitud | 0,022 ms | 0,038 ms |
| Cancelación de persistencia antes de confirmar | 0,320 ms | 0,830 ms |
| Ejecutar ocho corridas y verificarlas | 0,468 s | 0,292 s |
| Reabrir las ocho corridas | 0,062 s | 0,065 s |
| Respuesta de Qt offscreen, mayor intervalo de eventos | 59,56 ms | 64,11 ms |

El perfil de escritorio de 131 072 bits completó en 9,14 s en Windows y 11,82 s en Linux. Esa medición incluye la entrega y preparación del resultado en Workbench. El intervalo de eventos cuantifica la respuesta de la interfaz durante el trabajo. Los límites del gate son 1,5 s desde la solicitud de cancelación y 2 s entre eventos en ese perfil. [Ejecución de la matriz](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45834151197)
