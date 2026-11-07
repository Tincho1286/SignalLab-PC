# Preparar y firmar el portable

[← Desarrollo](README.md)

## Compilación verificable

El flujo [Build portables and request Windows signing](../../.github/workflows/portable.yml) utiliza Python 3.12.10 en GitHub Actions. Genera Windows y Linux por defecto; puede elegirse una sola plataforma. La solicitud Authenticode pertenece únicamente al trabajo Windows. Puede iniciarse manualmente desde `main` o una etiqueta `v…`. Conserva el commit, la versión, el checksum y el enlace de ejecución en un archivo de procedencia. Ejecuta los controles matemáticos, estáticos y de reutilización antes de empaquetar. Las ediciones instaladas añaden comprobaciones nativas de instalación y de la aplicación empaquetada.

`request_signing=false` sólo construye y sube el portable sin firma. Es el modo disponible mientras la solicitud al proveedor no esté aprobada. Ninguno de los modos reemplaza automáticamente las descargas de Releases.

## Después de la aprobación de SignPath

1. Configurá la cuenta, el proyecto y los responsables con autenticación multifactor según las condiciones del proveedor.
2. Asociá el sistema de construcción de confianza GitHub.com y el repositorio `Tincho1286/SignalLab-PC` en SignPath. Cualquier autorización de acceso a GitHub requiere revisar los permisos del proveedor.
3. Configurá el artefacto usando [packaging/signpath-artifact.xml](../../packaging/signpath-artifact.xml). Valida el nombre del producto, sus versiones y el archivo original; sólo firma el ejecutable de SignalLab dentro del artefacto ZIP.
4. Guardá `SIGNPATH_API_TOKEN` como secreto de GitHub Actions. No se incorpora a archivos, mensajes ni logs. Registrá las variables `SIGNPATH_ORGANIZATION_ID`, `SIGNPATH_PROJECT_SLUG`, `SIGNPATH_SIGNING_POLICY_SLUG` y, si corresponde, `SIGNPATH_ARTIFACT_CONFIGURATION_SLUG` con los valores entregados por el proveedor.
5. Iniciá el flujo con `request_signing=true` y aprobá manualmente la solicitud en SignPath. El flujo espera hasta una hora, valida la firma devuelta y guarda el resultado firmado por separado.

La configuración no contiene un certificado ni credenciales de demostración. No hay una alternativa que marque un archivo como firmado si falta el servicio o la validación. Tras aprobar una entrega, se publica el resultado firmado con sus propios checksums y fuente correspondiente.

## Metadatos Windows

`tools/windows_version.py` lee la versión del código sin importarlo y genera el recurso de versión usado por PyInstaller. `ProductName` es `SignalLab PC`, `ProductVersion` conserva la versión de la aplicación y `FileVersion` usa cuatro componentes numéricos. El nombre original debe coincidir con el ejecutable construido. Las versiones preliminares se identifican en los indicadores Windows.

[Code signing policy](../code-signing.md) · [Documentación oficial de SignPath](https://docs.signpath.io/trusted-build-systems/github)

## Firma local del canal de actualizaciones

El manifiesto Ed25519 se firma localmente después de verificar los instaladores construidos. No requiere SignPath ni se sube la clave privada a GitHub. La [guía de instalación y actualizaciones](../installed-updates.md#construcción-y-publicación) describe el comando y el orden de publicación. Esta firma protege las actualizaciones del programa y es independiente de Authenticode.
