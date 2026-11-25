# Envolvente operativa

Dimensioná la ejecución con los presupuestos de trabajo de la operación, las entradas y resultados que se retienen y el costo adicional de guardar. La guarda de memoria disponible usa una fracción de admisión y el pool comparte reservas estimadas entre servicios. El perfil de banco usa un hilo BLAS/OMP por proceso.

Los límites del SO y del espacio en disco pueden fallar antes que las estimaciones. Un plazo se comprueba en puntos cooperativos y el proceso simbólico tiene supervisión propia. Todavía no hay cuotas estrictas del SO para las operaciones nativas. El formato JSON sigue dirigido a sesiones interactivas moderadas.

## Envolvente medida en la continuidad

Candidato `faef335bb7892cda92edc50a7c4f417a89b0415c`. Banco con un hilo BLAS y OMP, proceso nuevo por caso, un calentamiento y tres repeticiones. El tamaño indicado es el máximo del perfil verificado, con los parámetros de la tabla. Los límites de admisión reales se calculan con la RAM disponible y el tamaño y la naturaleza de la operación. La tabla no generaliza los tiempos a otros parámetros, máquinas o tipos de datos.

| Operación | Tamaño y presupuesto de trabajo | Mediana Win/Linux (ms) | RSS pico Win/Linux (MiB) | Cancelación Win/Linux (ms) |
| --- | --- | ---: | ---: | ---: |
| DFT | 1 048 576 bins, 128 B × bins, 128 MiB | 62,13 / 77,17 | 178,23 / 187,43 | 28,28 / 50,80 |
| IDFT | 1 048 576 bins, 128 B × bins, 128 MiB | 54,09 / 65,02 | 162,25 / 171,19 | 15,53 / 42,79 |
| FIR | 1 048 576 muestras, 31 coeficientes, 128 B × (salida + coeficientes), 128,00 MiB | 58,55 / 82,68 | 147,69 / 156,27 | 33,11 / 46,89 |
| Resampling | Entrada de 1 048 576, factor 2/3. 256 B × (entrada + salida + coeficientes), 426,68 MiB | 49,52 / 98,92 | 138,27 / 147,27 | 18,05 / 74,14 |
| PSD Welch | 1 048 576 muestras, segmento 256. 256 B × segmento de trabajo, más señal retenida | 244,80 / 269,48 | 138,37 / 147,54 | 1,53 / 12,86 |
| Pipeline | Entrada de 1 048 576, factor 2/3, FIR 31 y PSD 256. Entrada + resultados retenidos + máximo de trabajo, 474,69 MiB | 398,68 / 507,78 | 233,66 / 241,91 | 0,10 / 0,06 |
| SLBIN guardar / abrir | 1 048 576 muestras, 16 777 394 B en disco. 32 B × muestra al guardar y 64 B × muestra al abrir | 106,76 / 90,98 al guardar y 16,70 / 18,91 al abrir | 138,93 / 147,41 al guardar y 138,14 / 147,47 al abrir | 1,30 / 0,65 al guardar |
| Proyecto científico guardar / abrir | Dos registros de 1 048 576 muestras, 33 555 971 B en disco. Apertura admite 3 × muestras en bytes + 8 × manifiesto | 196,55 / 207,60 al guardar y 50,70 / 56,37 al abrir | 178,68 / 187,43 al guardar y 178,51 / 187,13 al abrir | 1,49 / 0,27 al guardar |
| Sesión JSON guardar / abrir | Dos registros de 262 144 muestras, 48,59 / 46,49 MB de disco | 2 089,26 / 2 664,76 al guardar y 376,99 / 638,40 al abrir | 182,71 / 191,59 al guardar y 229,85 / 235,69 al abrir | Se midió la escritura JSON plana por separado |

El RSS incluye intérprete, librerías, entradas y preparativos. El banco informó 67 perfiles por sistema. En 33 de 34 ensayos temporizados el cálculo confirmó la cancelación y conservó los archivos de partida. El resampling de 262 144 muestras en Windows terminó antes del acuse en una medición. La DTFT de 4096 muestras y 4097 puntos canceló a la siguiente frontera de bloque en estos ensayos. El proceso simbólico se detuvo y limpió su temporal entre 57,67 y 64,22 ms en el banco principal. Las llamadas nativas y el guardado en disco pueden demorar hasta el próximo punto de control. El CLI permite fijar un plazo y un presupuesto por solicitud. No hay plazo de pared global para esos motores.

## Admisión y concurrencia

- El escritorio ejecuta un cálculo de herramienta a la vez por ventana. La API permite compartir un `ResourcePool` por proceso. Para usar el perfil del banco de forma concurrente, la suma de reservas y datos retenidos debe caber en el 35 % de RAM disponible. En Linux se usa también el margen más restrictivo de la jerarquía cgroup v2 cuando está disponible. El caso de pipeline de 474,69 MiB necesita unos 1,32 GiB disponibles sin añadir reservas de otros trabajos. Los procesos independientes necesitan coordinación externa para compartir un mismo presupuesto.
- MAT clásico y HDF5 aplican límites efectivos. Archivo hasta 128 MiB, una variable decodificada hasta 64 MiB, hasta 4096 nombres y un lector simultáneo por proceso SignalLab. El subproceso tiene 15 s por petición de catálogo o de lectura y una cuota del SO de hasta 1 GiB, limitada al 35 % de memoria disponible. Si el presupuesto queda por debajo de 256 MiB, se rechaza el inicio. Windows usa memoria comprometida del proceso mediante Job Object. Linux acota el espacio de direcciones mediante RLIMIT_AS. El padre revisa plazo y cancelación con esperas de hasta 50 ms, luego termina al lector si sigue en ejecución. El tiempo de eliminación y recolección del proceso depende del SO. La regresión forzó el vencimiento inmediato y verificó que la lectura válida se pudo reintentar.
- Las cuotas del lector y el aislamiento simbólico justifican mantener separados esos procesos. Las mediciones del Core numérico conservan ejecución local y cancelación cooperativa. Fuera de los perfiles de la tabla, hace falta medir el trabajo nativo concreto antes de fijar un compromiso de latencia o habilitar concurrencia adicional.

[Mediciones de Windows](../validation/evidence/windows-performance-faef335.json) · [Mediciones de Linux](../validation/evidence/linux-performance-faef335.json) · [Modelo de persistencia](../persistence/COMMUNICATIONS_STORAGE_SIZING.md)

## Recuperación y concurrencia en la continuación autónoma

El pool común admite reservas nuevas hasta el 35 % del margen de memoria que estima en el momento de entrada. Las reservas en curso reducen la disponibilidad y se liberan al finalizar, fallar o cancelar. Los servicios numéricos de Core, SLBIN, SLPROJ y la cuota del trabajador MAT comparten ese pool dentro del proceso. El equipo aún puede entrar en presión por datos retenidos por herramientas antiguas, otros procesos o código nativo. En una prueba con pool acotado, guardar un proyecto durante otra reserva rechaza la segunda carga, conserva el archivo previo y permite reintentar al liberar la primera.

Se comparó la escritura JSON en Qt con la recuperación binaria en un hilo dedicado, con dos registros de 262 144 muestras, temporizador preciso de 10 ms y tres repeticiones por modo en `54adaa0`. El peor intervalo de heartbeat pasó de 1 785,5 a 10,6 ms en Windows CI y de 1 788,2 a 10,7 ms en Linux CI. La mediana del tiempo de escritura quedó en 130,7 ms y 50,5 ms. Se investiga cualquier intervalo sostenido superior a 100 ms en este perfil de escritorio. El número medido depende del planificador y no establece un plazo máximo. [Recuperación Windows](../validation/evidence/windows-responsiveness-54adaa0.json) · [Recuperación Linux](../validation/evidence/linux-responsiveness-54adaa0.json)
