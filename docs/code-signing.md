# Code signing policy

[← Documentación](README.md)

## Estado de la firma

La distribución estable 1.2.1 disponible en Releases permanece **sin firma Authenticode**. La solicitud de incorporación al programa gratuito de SignPath Foundation fue presentada el **2 de noviembre de 2026** y la página confirmó su recepción. Está pendiente la evaluación del proveedor; no existe todavía un certificado aprobado ni una firma de producción publicada. Ningún sello de esta página sustituye el estado real del archivo.

Se solicita el servicio gratuito de SignPath Foundation para código abierto. La atribución aplicable a futuras versiones firmadas mediante ese programa será: “Free code signing provided by SignPath.io, certificate by SignPath Foundation”. Esta atribución describe el servicio solicitado y no anuncia una aprobación obtenida.

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
