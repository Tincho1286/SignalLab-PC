# Dictamen de distribución

**NO-GO para distribución pública.** La firma descartable y los perfiles aislados comprueban la integridad de entrega y la instalación. La versión superior del candidato, la firma Authenticode disponible para producción y la aceptación de las excepciones de Qt y escritorio requieren resolución antes de promover una distribución.

El candidato y la estable pública comparten número de versión. El actualizador interpreta esa igualdad correctamente y sólo ofrecería una versión superior. [Comprobación de actualizaciones](../distribution/UPDATE_COMPATIBILITY_REPORT.md)

## Continuación autónoma

**NO-GO para distribución pública.** La matriz completa de `54adaa0` usa 2.0.1 y acredita el salto desde 2.0.0 en Windows y Linux con firma de ensayo, datos conservados y rechazo de descarga corrupta. El candidato vigente conserva 2.0.1 como versión de auditoría y se distingue por SHA. El dictamen público depende del estado de su matriz, la firma Windows, el canal y el alcance de exposición nativa. [Matriz de candidatos](../validation/FINAL_VALIDATION_MATRIX.md#continuación-autónoma) · [Revisión nativa](../security/DEPENDENCY_CONTINUATION.md)
