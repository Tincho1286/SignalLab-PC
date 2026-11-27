# Ramas, entregas y mantenimiento LTS

Las ramas oficiales son `main` y `develop`. `main` contiene el último estado integrado y aprobado por el propietario. `develop` reúne el trabajo de ingeniería de las fases autorizadas. Para revisar una versión histórica o preparar el mantenimiento LTS, usar su etiqueta, SHA o un worktree con HEAD desacoplado. La política se aplica también a correcciones y publicaciones. [Estado del proyecto](PROJECT_STATE.md)

## De una fase autorizada a su cierre

| Gate | Responsable | Controles y decisión |
| --- | --- | --- |
| A · Calificación técnica | Codex | Auditar y planificar el alcance autorizado, modernizar herramientas relacionadas e implementar. Validar con oráculos independientes, probar lo nuevo y las regresiones, corregir defectos y aprobar el Quality Gate. Ejecutar la matriz Windows/Linux sobre el mismo SHA limpio. Verificar los paquetes y publicar la Preview. |
| B · Aceptación funcional | Propietario | Probar la Preview en sus equipos y decidir si satisface el uso esperado. Los hallazgos se corrigen en nuevas Preview, con sus pruebas aplicables, Quality Gate y SHA propio. |
| C · Integración y cierre | Propietario y Codex | El propietario autoriza expresamente la integración. Codex integra `develop` en `main`, verifica el resultado y registra el cierre. El inicio de la fase siguiente requiere autorización independiente. |

La autorización de inicio habilita el trabajo de esa fase. Si el alcance cambia sustancialmente, el propietario decide antes de implementar. La aceptación funcional de una Preview se registra por separado del permiso para integrarla en `main`. [Quality Gate permanente](VALIDATION_MATRIX.md#criterios-vigentes) · [Roadmap](ROADMAP.md)

## Publicar Preview

Codex tiene autorización permanente para publicar las Preview de fases autorizadas una vez aprobada la calificación técnica. Esa autorización cubre la publicación y su **nueva etiqueta numérica** en el SHA calificado. Cada corrección se publica bajo un número nuevo dentro de la familia y revalida el candidato. Las Preview son acumulativas.

Antes de publicar, reunir el informe aprobado y comprobantes del mismo SHA, portables e instaladores Windows x64 y Linux x86_64, fuentes, avisos de licencia, notas, sumas SHA-256, procedencia e inventarios. Verificar firma Ed25519 del manifiesto, versión, canal, metadatos y hashes de los instaladores. Tras publicar, verificar artefactos, enlace al SHA y elección del canal desde el actualizador. [Guía de publicación](../development/releases.md) · [Firma de manifiestos](../development/signing.md)

Si firmar o publicar requiere una acción del propietario, pedir únicamente esa intervención y usar los controles existentes. La rotación o modificación de claves de producción, las etiquetas históricas, las excepciones de riesgo y cualquier cambio de criterios de calidad requieren aprobación específica. La autorización permanente se limita al canal Preview de fases autorizadas.

Las pruebas funcionales automatizadas de interfaz permanecen en ambas plataformas. DPI, escalados y escritorio manual se usan como diagnóstico y seguimiento. Un defecto funcional conocido o una regresión automatizada se trata según su severidad y los criterios del Quality Gate. [Reglas de validación](VALIDATION_MATRIX.md#criterios-vigentes)

## Stable/LTS y Preview

| Canal | Versiones | Fuente | Actualizador |
| --- | --- | --- | --- |
| Stable/LTS | Familia `2.0.x` | Última etiqueta LTS y mantenimiento en checkout desacoplado | Predeterminado, con manifiesto firmado `stable`. |
| Preview | Familias desde `2.1.x` | SHA limpio alcanzable desde `develop` con calificación aprobada | Activación explícita y manifiesto firmado `preview`. |

`v2.0.0` es la base LTS y la entrega estable vigente. Mantener inmutables sus etiquetas, código fuente y artefactos, y los de cada actualización. La integración en `main` cambia el código aprobado de esa rama. El canal LTS se rige por sus propias etiquetas, publicaciones y manifiesto.

Cada corrección LTS se prepara sobre la última etiqueta de mantenimiento en un checkout desacoplado y usa una versión nueva. Requiere autorización específica del propietario para etiqueta, firma y publicación. Propagar a `main` y `develop` las correcciones aplicables con su origen identificado, pruebas de regresión y las aprobaciones de integración correspondientes. Los laboratorios nuevos se entregan en Preview durante las fases de expansión. La distribución definitiva de Fase 11, su nombre y su versión requieren autorización propia.

Los manifiestos conservan el esquema que entiende 2.0.0. Ed25519 autentica canal, versión e instaladores. Authenticode continúa en el seguimiento E-04, separado del mecanismo firmado del actualizador y de la autorización de distribución. [Auditoría de distribución](DISTRIBUTION_INFRASTRUCTURE_AUDIT.md) · [Guía de firma](../development/signing.md)
