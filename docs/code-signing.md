# Code signing policy

[← Documentación](README.md)

## Estado de la firma

La distribución estable 1.8.0 disponible en Releases permanece **sin firma Authenticode**. No hay un servicio de firma de producción habilitado. La solicitud al programa gratuito de SignPath Foundation no fue aprobada; la integración técnica opcional no constituye una aprobación ni una firma publicada.

Las ediciones con actualizador utilizan una **firma Ed25519 propia para autenticar las actualizaciones**. La clave pública se distribuye con la aplicación y la clave privada permanece fuera del repositorio. Esta firma no es un certificado de identidad reconocido por Windows y no elimina por sí sola un bloqueo del Control inteligente de aplicaciones. [Instalación y actualizaciones](installed-updates.md).

## Responsabilidades

- Mantenimiento, revisión de cambios y compilaciones: [Tincho1286](https://github.com/Tincho1286).
- Aprobación humana de solicitudes de firma: [Tincho1286](https://github.com/Tincho1286), una vez que el proveedor habilite ese rol.
- Las contribuciones externas se revisan antes de incorporarse a las ramas utilizadas para firmar.

Las cuentas que participan en el proceso deben utilizar autenticación multifactor en GitHub y SignPath. El flujo no habilita ni modifica esta configuración de las cuentas.

## Qué se podrá firmar

Sólo ejecutables de SignalLab PC producidos a partir del código público de este repositorio mediante el [flujo de compilación](../.github/workflows/portable.yml). Las bibliotecas de terceros conservan sus licencias y no se firman individualmente usando la identidad de SignalLab.

El flujo se inicia manualmente desde `main` o una etiqueta `v…`, en un agente Windows alojado por GitHub. Se fija el commit de origen, se instalan las versiones declaradas y se sube el ejecutable como un artefacto de GitHub antes de solicitar su firma. Los metadatos Windows identifican producto, versión y nombre original. Las acciones externas se fijan por commit.

La firma exige una cuenta y política aprobadas por SignPath y la aprobación humana de cada solicitud. La construcción por sí sola no firma ni publica un release. El resultado firmado debe superar la validación Authenticode antes de ofrecerse como tal. Los archivos temporales de GitHub expiran después de siete días; las entregas aprobadas se conservan en Releases.

## Alcance de la firma

Una firma identifica al publicador, vincula el archivo a su origen y permite detectar modificaciones posteriores. No certifica la exactitud de los cálculos ni garantiza eliminar inmediatamente todos los avisos de Windows. Consultá [firma y reputación](windows-downloads.md).

## Privacidad

La aplicación trabaja con datos locales. Su política está en [Privacidad](privacy.md). La gestión de la solicitud, las cuentas y la firma utiliza los servicios de GitHub y SignPath, sujetos a las políticas de esos proveedores.

[Condiciones de SignPath Foundation](https://signpath.org/terms.html) · [Integración oficial con GitHub](https://docs.signpath.io/trusted-build-systems/github)
