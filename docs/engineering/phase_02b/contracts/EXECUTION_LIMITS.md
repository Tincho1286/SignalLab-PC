# Límites de ejecución

Los recursos son estimaciones en bytes y una admisión basada en RAM libre. Cada motor conserva sus propias guardas. Siguen separados el tamaño de los archivos, la carga de entrada, temporales científicos y el guardado JSON. La escritura binaria recorre bloques de 1 MiB. NumPy y SciPy retoman el control cooperativo al terminar sus bloques nativos. Los procesos simbólicos siguen sujetos a sus permisos de aplicación y a la política de Fase 01.

La concurrencia se limita con un pool compartido. La carga de archivos del escritor de escritorio y los resultados conservados fuera de una reserva no se descuentan automáticamente de ese pool. Una sesión tiene un solo escritor por archivo.
