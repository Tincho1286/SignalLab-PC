# Auditoría arquitectónica

La DFT es la frontera piloto compartida con Qt. Los otros servicios DSP operan sobre los mismos motores desde Python y CLI, mientras los paneles mantienen sus rutas de presentación. El contexto de ejecución concentra admisión y cancelación de los servicios. Proyecto conserva instantáneas y evidencia de publicación. Session conserva el formato de escritorio.

El análisis de importaciones directas encontró 26 módulos alcanzables desde 11 entradas del Core, sin ciclos de importaciones al nivel de módulo. Una prueba dinámica bloqueó PySide, Shiboken, PyQt y qtpy y completó la publicación de un pipeline. Las rutas antiguas tienen importaciones diferidas y contratos de GUI que no quedan caracterizados por ese grafo.

## Continuación autónoma

El grafo AST sobre `4f0f32d` contó 390 archivos de aplicación, 51 140 líneas físicas y 1 027 dependencias de nivel superior. Se conservan las fronteras DFT y DSP y la persistencia de CAS dispone de una comprobación headless específica que bloquea importación tanto de Qt como del motor de evaluación simbólica. El controlador y vistas Qt sólo proyectan el estado validado. Las dependencias diferidas siguen registradas en el análisis. El almacenamiento por corrida satisface el volumen probado sin introducir servicios externos. [Grafo y huella](../validation/evidence/headless-graph-4f0f32d.json) · [Contratos CAS](../persistence/CAS_PERSISTENCE_VALIDATION.md)

El análisis de `eb50895` contó 390 archivos y 51 166 líneas físicas. No encontró ciclos de importación de nivel superior. Cinco grupos incluyen dependencias diferidas y conservan seguimiento. El selector de resultados comparte con el proyecto el cálculo del grafo de dependencias y la incorporación de objetos, con referencias reescritas y sin recodificar las muestras. [Grafo del candidato](../validation/evidence/headless-graph-eb50895.json)
