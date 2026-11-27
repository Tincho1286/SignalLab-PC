# Arquitectura de Fase 05

El laboratorio conserva el monolito modular. `probability.py` normaliza distribuciones univariadas y evalúa escalares con estados numéricos explícitos. `multivariate_probability.py` implementa gaussianas conjuntas reales o complejas y la multinomial. Ambos producen los registros `Signal` que ya conocen las herramientas de filtrado, correlación, espectros y comunicaciones. Sus importaciones carecen de Qt.

El Workbench amplía la ruta existente `random/generate`. Las tres primeras opciones y sus campos preservan el formato de restauración. Las familias posteriores muestran solo sus parámetros. Un único selector alterna realización y consulta teórica. La configuración avanzada presenta semilla, réplicas, índice y reloj. La pestaña de realizaciones permite seleccionar registros y componentes con los mismos controles de gráfico y reutilización del Workbench.

La CLI `python -m signallab_pc probability` adapta entradas JSON y archivos de salida. El generador, las consultas, la normalización y el manejo de estados son compartidos con Python y, cuando aplica, Workbench. La simulación histórica de las tres variantes originales sigue disponible por su ruta y mantiene la secuencia anterior. Los nuevos subflujos usan una identidad derivada de semilla y réplica y conservan versiones de NumPy y SciPy.

Una realización registra su huella al generarse. La entrega guarda la distribución y todas sus realizaciones con una transacción `Project.stage_records`. Una inconsistencia de origen, contenido o cancelación antes de entregar revoca el lote. CLI persiste esa misma transacción mediante sesión JSON o SLPROJ y conserva el archivo anterior si falla el guardado. [Contratos](SCIENTIFIC_CONTRACTS.md) · [Línea base](PHASE_05_BASELINE.md)

La futura estimación, identificación, PSD y campañas tomarán estos contratos como punto de partida, y seguirán usando las primitivas acreditadas de Engineering Core y canales. [Plan](PHASE_05_PLAN.md)
