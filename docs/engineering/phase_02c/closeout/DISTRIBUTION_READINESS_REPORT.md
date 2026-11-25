# Dictamen de distribución

**NO-GO para distribución pública.** La firma descartable y los perfiles aislados comprueban la integridad de entrega y la instalación. La versión superior del candidato, la firma Authenticode disponible para producción y la aceptación de las excepciones de Qt y escritorio requieren resolución antes de promover una distribución.

El candidato y la estable pública comparten número de versión. El actualizador interpreta esa igualdad correctamente y sólo ofrecería una versión superior. [Comprobación de actualizaciones](../distribution/UPDATE_COMPATIBILITY_REPORT.md)

## Continuación autónoma

**NO-GO para distribución pública.** La matriz completa de `eb50895` verifica portables, instaladores y salto aislado desde 2.0.0 en Windows y Linux con firma de ensayo, datos conservados y rechazo de descarga corrupta. El candidato usa 2.0.1 como versión de auditoría. El dictamen público queda sujeto a firma Windows, canal, exposición nativa y autorización expresa. [Matriz de candidatos](../validation/FINAL_VALIDATION_MATRIX.md#resultado-de-eb50895) · [Revisión nativa](../security/DEPENDENCY_CONTINUATION.md)
