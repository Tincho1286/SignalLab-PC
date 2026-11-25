# Persistencia del CAS

Un resultado CAS publicado en Proyecto se guarda, vuelve a abrir y se puede referenciar desde otra hoja. La regresión histórica importa el valor como `r1` y verifica su derivada exacta. La exportación de fórmulas conserva hipótesis y representación cuando el contrato del resultado las incluye. La hoja activa, historial de edición y variables de una sesión CAS sin publicar se mantienen como alcance pendiente.

## Contrato de hoja CAS v1

La sesión JSON con CAS usa esquema 4. Los archivos sin hoja conservan el esquema 3 y el lector admite las versiones históricas 1–3. SLPROJ admite la hoja como dato opcional de su espacio de trabajo. Las versiones anteriores que desconozcan el esquema 4 pueden recibir la biblioteca mediante el proyecto JSON histórico. La lectura verifica nombres, variables, funciones, supuestos, historial, relaciones a registros de CAS y borrador antes de sustituir la sesión. La apertura reconstituye valores mediante el contrato estructurado y renderiza las vistas guardadas, sin volver a ejecutar las celdas. Las figuras y el cursor de edición pueden regenerarse o volver a colocarse desde la hoja abierta.

`test_math_cas_session` verifica ambos formatos, referencia inválida y lectura sin Qt o motor simbólico. `test_desktop_session` añade variables complejas, cálculo posterior, pestaña oculta, foco y recuperación después de un error de escritura. El diagnóstico congelado crea una variable compleja y guarda y reabre el proyecto. [Integridad](PERSISTENCE_INTEGRITY_REPORT.md) · [Reapertura nativa Windows](../gui/DESKTOP_CONTINUATION.md)
