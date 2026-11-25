# Ejecución del flujo DSP

`DSPPipelineRequest` fija la entrada, los factores racionales, el filtro, el modo de salida, la longitud DFT y la configuración de PSD. El reloj del filtro se valida contra la salida del resampling. La amplitud puede requerir una unidad explícita. El progreso distribuye cuatro intervalos de 25 puntos. Todos los controles comparten plazo y evento.

`run_pipeline` calcula fuera de Project. `store_pipeline` publica etapas, filtro y señal de entrada como una transacción y conserva relaciones directas. La CLI usa un archivo temporal y reemplaza el destino tras una última comprobación.
