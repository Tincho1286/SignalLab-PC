# Arquitectura de Digital Communications Lab

## Fronteras existentes

El despachador `signallab_pc.__main__` importa Qt sólo para las rutas de escritorio e instalación. DFT y los servicios DSP de Python y CLI importan sus modelos y operaciones por separado. El ejemplo de composición comprobado es `dsp_pipeline`, que calcula con un presupuesto compartido, verifica entradas y parámetros y publica un conjunto de registros mediante `Project.stage_records`. Los hashes de `operation_provenance` abarcan el contenido y los campos relevantes de señales y sistemas.

`Signal` es el contrato de muestras complejas uniformes. Los índices discretos se mantienen enteros y el reloj en segundos se representa con los metadatos actuales. `Transfer` y `apply_fir` proporcionan la ruta causal con longitud completa para conservar colas y retardo. El remuestreo racional existente tiene sus propias condiciones de banda y bordes. El tren de impulsos de símbolos usa inserción exacta de ceros para que el pulso de transmisión defina por sí mismo la respuesta. `estimate_psd` aporta la PSD con el reloj del registro.

El proyecto distingue señales, sistemas y cálculos. `session` mantiene el lector histórico y el adaptador de escritorio. SLBIN intercambia una señal. SLPROJ incorpora las muestras complejas por bloques y contiene el manifiesto del mismo proyecto y espacio de trabajo. El banco `measure_scientific_campaign.py` probó un catálogo de huellas con un SLPROJ por corrida y una corrida activa. Su arquitectura de guardado por corrida y actualización atómica del índice sirve de base para el servicio de barridos. El banco sintético pertenece a la validación.

## Integración del laboratorio

Las operaciones de bits, modulación, pulsos, ruido, recepción y mediciones reciben tipos de dominio independientes de Qt. La capa de aplicación concentra solicitudes, validación, admisión, ejecución, procedencia y composición. Python importa esos servicios y CLI interpreta argumentos y escribe los mismos resultados. Workbench conecta controles y trabajos cancelables con los mismos servicios, y presenta informes y figuras independientes bajo la infraestructura de resultados del escritorio.

El catálogo de Workbench indexará un área de comunicaciones y las operaciones tendrán identificadores de herramienta estables. Cada operación dispondrá de entradas propias y acceso a los resultados compatibles del proyecto. El demostrador expondrá el recorrido completo desde la fuente hasta las mediciones. Las figuras reutilizarán la ventana de gráficos, con líneas I/Q en unidades declaradas, constelación con aspecto igual y ojo alineado al reloj de símbolos. Los gráficos de error conservarán los conteos, el estado estadístico y la distinción entre valores teóricos y observados.

Los experimentos persistentes adaptan sus datos al catálogo de `Project`. Las muestras I/Q conservan su representación `Signal` en SLBIN y SLPROJ. Los cálculos versionados guardan configuración, métricas, referencias y secuencias compactas de bits y etiquetas. El catálogo de barridos referencia cada proyecto por nombre previsto y huella. Serializa un escritor por carpeta, vuelve a abrir cada corrida para verificarla y cambia el índice mediante reemplazo atómico. Al recuperar la campaña, puede incorporar una corrida completa cuyo archivo se confirmó antes de guardar la fila que la identifica.

Para interoperar, SLBIN transporta un único registro científico con unidades y reloj, SLPROJ transporta sus vínculos y las métricas se exportan como CSV. Volcar una campaña completa a CSV multiplicaría los datos y perdería metadatos de adquisición. Los formatos de captura SDR corresponden a la fase prevista para esa interoperabilidad. [Ejemplos](README.md) · [Formatos disponibles](../../file-formats.md)

Una cadena reserva muestras de entrada, resultados retenidos y el máximo de espacio temporal simultáneo antes de asignarlos. El contexto hijo mantiene cancelación y plazo, con progreso de etapas y una reserva de nivel superior. La publicación valida el conjunto después del cálculo y se confirma en una operación atómica. Cada archivo de barrido se verifica antes de incorporarse al catálogo de corridas completas.

La fase extiende el monolito modular y usa los límites ya aprobados en 02C como referencia de medición. El informe de rendimiento acreditará cualquier perfil nuevo. [Expediente de 02C](../phase_02c/README.md) · [Contratos](SCIENTIFIC_CONTRACTS.md)
