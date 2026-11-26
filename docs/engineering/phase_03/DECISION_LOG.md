# Decisiones de Fase 03

## ADR 002 · Cadenas de comunicaciones sobre el Core

**Estado.** Diseño de WP-00, sujeto a la matriz de consolidación y a la validación de los primeros contratos.

El laboratorio necesita operaciones independientes y un demostrador con reloj, ruido reproducible y entrega atómica. El flujo DSP vigente acredita la reserva común, el cálculo sin Qt, las huellas por contenido y la entrega en proyecto. Se extiende ese enfoque manteniendo tipos distintos para bits, etiquetas de constelación y muestras I/Q.

Las operaciones comparten servicios entre Python, CLI y Workbench. Para persistir, se reutilizan `Project`, los formatos de señales y el patrón de catálogo de SLPROJ probado con 48 corridas. Los experimentos validan el archivo de una corrida antes de publicarla en el índice. La extensión de formatos depende de una necesidad medida. El editor de bloques, motores distribuidos, SDR y canales de propagación pertenecen a alcances posteriores.

Para reproducir, se registran algoritmo de generación, versión, semilla y subflujo por etapa, configuración y huellas. La comparación de referencias externas queda separada del producto. El criterio de entrada para WP-01 es la matriz limpia de los dos sistemas. [Arquitectura](ARCHITECTURE.md) · [Auditoría de referencias](INTEGRATION_CATALOG.md) · [Criterios](QUALITY_GATE_CRITERIA.md)
