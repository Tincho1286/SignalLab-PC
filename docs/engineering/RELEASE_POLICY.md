# Ramas, entregas y mantenimiento LTS

El repositorio mantiene dos ramas. `main` representa el último estado aprobado por el propietario. `develop` reúne el trabajo de ingeniería autorizado. Las versiones históricas se identifican con una etiqueta, un SHA o un checkout desacoplado.

## Entregas de las fases 03 a 09

1. Implementar la fase autorizada en `develop` y completar sus controles científicos, de seguridad, recursos y compatibilidad.
2. Identificar un mismo SHA limpio y verificado en Windows y Linux. Preparar portables, instaladores, fuentes, checksums, notas y procedencia para ese SHA.
3. Entregar el expediente al propietario para autorizar la prerelease y su etiqueta. Las prereleases de Engineering acumulan los avances de las fases anteriores.
4. Recibir la validación funcional del propietario, corregir hallazgos y revalidar cualquier candidato cuyo código cambie.
5. Integrar en `main` solamente después de la aprobación expresa y verificar el resultado. Empezar la fase siguiente cuando se autorice.

La preparación de artefactos y el dictamen técnico de distribución son independientes de la aprobación para publicar o integrar. [Guía de publicación](../development/releases.md) · [Auditoría de infraestructura](DISTRIBUTION_INFRASTRUCTURE_AUDIT.md)

## Stable/LTS y Preview

| Canal | Versiones nuevas | Fuente de construcción | Actualizador |
| --- | --- | --- | --- |
| Stable/LTS | Familia `2.0.x` | Última entrega LTS y mantenimiento sobre un checkout desacoplado | Consulta estable predeterminada y manifiesto firmado `stable`. |
| Preview | Versiones numéricas a partir de `2.1.0` | SHA alcanzable desde `develop` y aprobado en su Quality Gate | Opción explícita para consultar preliminares y manifiesto firmado `preview`. |

`v2.0.0` es la versión LTS vigente y la base de su familia. La etiqueta, los archivos y su procedencia histórica se conservan. La línea Preview de Engineering empieza en `v2.1.0`. Sus correcciones avanzan en nuevas versiones Preview como `v2.1.1`. Integrar una fase en `main` cambia el código aprobado en esa rama. La disponibilidad LTS depende de su etiqueta, publicación, versión y manifiesto propios.

Cada corrección LTS parte del SHA señalado por la última etiqueta LTS publicada. Se trabaja en un checkout o un worktree desacoplado, se conservan los commits de mantenimiento y se validan los paquetes antes de autorizar una nueva etiqueta. Las correcciones aplicables se incorporan a `main` y `develop` con sus pruebas y un registro de origen. El mantenimiento de la familia LTS se limita al alcance aprobado de esa familia.

Los manifiestos continúan con el formato firmado que entiende 2.0.0. La firma Ed25519 autentica canal, versión e instaladores. Los comprobantes de construcción vinculan cada archivo al SHA y a la huella de las fuentes. La firma Authenticode se mantiene en el seguimiento E-04. [Firma y verificación](../development/signing.md)
