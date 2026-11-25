# Auditoría arquitectónica

La DFT es la frontera piloto compartida con Qt. Los otros servicios DSP operan sobre los mismos motores desde Python y CLI, mientras los paneles mantienen sus rutas de presentación. El contexto de ejecución concentra admisión y cancelación de los servicios. Proyecto conserva instantáneas y evidencia de publicación. Session conserva el formato de escritorio.

El análisis de importaciones directas encontró 26 módulos alcanzables desde 11 entradas del Core, sin ciclos de importaciones al nivel de módulo. Una prueba dinámica bloqueó PySide, Shiboken, PyQt y qtpy y completó la publicación de un pipeline. Las rutas antiguas tienen importaciones diferidas y contratos de GUI que no quedan caracterizados por ese grafo.
