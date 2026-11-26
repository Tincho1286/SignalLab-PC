# Decisiones de Fase 03

## ADR 002 · Cadenas de comunicaciones sobre el Core

**Estado.** Aprobado para implementación tras la matriz de consolidación. Los contratos se acreditan mediante las pruebas de sus paquetes. [SHA de referencia](PHASE_03_BASELINE.md)

El laboratorio necesita operaciones independientes y un demostrador con reloj, ruido reproducible y entrega atómica. El flujo DSP vigente acredita la reserva común, el cálculo sin Qt, las huellas por contenido y la entrega en proyecto. Se extiende ese enfoque manteniendo tipos distintos para bits, etiquetas de constelación y muestras I/Q.

Las operaciones comparten servicios entre Python, CLI y Workbench. Para persistir, se reutilizan `Project`, los formatos de señales y el patrón de catálogo de SLPROJ probado con 48 corridas. Los experimentos validan el archivo de una corrida antes de publicarla en el índice. La extensión de formatos depende de una necesidad medida. El editor de bloques, motores distribuidos, SDR y canales de propagación pertenecen a alcances posteriores.

Para reproducir, se registran algoritmo de generación, versión, semilla y subflujo por etapa, configuración y huellas. La comparación de referencias externas queda separada del producto. El criterio de entrada para WP-01 es la matriz limpia de los dos sistemas. [Arquitectura](ARCHITECTURE.md) · [Auditoría de referencias](INTEGRATION_CATALOG.md) · [Criterios](QUALITY_GATE_CRITERIA.md)

## Recuperación de campañas

Cada combinación usa una semilla derivada de la semilla base y su posición en el plan, o una semilla común declarada. La recuperación compara un resumen canónico de los parámetros y del entorno numérico y vuelve a verificar las corridas. Una reposición conserva los mismos parámetros, subflujos y métricas del archivo original para el mismo entorno. Una actualización del entorno puede exigir conservar el ejecutor de origen para continuar el barrido. Los SLPROJ y CSV ya generados quedan disponibles como evidencia.

## Distribución del primer candidato

La versión numérica elegida para el candidato es 2.1.0 Preview. Así conserva tres campos para los clientes instalados y deja la familia 2.0.x disponible para mantenimiento. La firma usa el mismo esquema de manifiesto con el campo de canal. La matriz prepara una sola pareja de portables y una pareja de instaladores con procedencia verificable. La etiqueta y la firma pública requieren la autorización ya prevista para cada entrega. [Política](../RELEASE_POLICY.md)
