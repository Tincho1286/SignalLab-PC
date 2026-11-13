# Instalación y actualizaciones

[← Documentación](README.md) · [Elegir un formato](installation.md)

Desde la versión 1.8.0, SignalLab PC ofrece ediciones instalables para Windows x64 y Linux x86_64, además de los portables. La edición instalada registra accesos y permite incorporar nuevas versiones desde la aplicación. Ambas utilizan los mismos motores de cálculo y contienen Python y sus dependencias.

## Ubicación de la instalación

En Windows, el instalador trabaja para el usuario actual y utiliza por defecto `%LOCALAPPDATA%\Programs\SignalLab PC`. Las siguientes entregas conservan la identidad de instalación y reemplazan los archivos del programa en esa carpeta. Los accesos y el registro de desinstalación se mantienen entre versiones.

En Linux, la ubicación predeterminada es `~/.local/share/SignalLab-PC/`, con un lanzador en `~/.local/bin/signallab-pc` y una entrada del menú en `~/.local/share/applications/org.signallab.PC.desktop`. Se respetan los directorios XDG configurados para datos y menú. La instalación no requiere `sudo`; sus requisitos gráficos y de glibc son los del [portable Linux](linux.md).

## Buscar una versión nueva

Abrí **Ayuda → Buscar actualizaciones**. En **Versiones que querés recibir** elegí **Sólo versiones estables** o **Estables y preliminares (Pre-releases)**. La elección se conserva para las consultas siguientes; la opción predeterminada sigue siendo estable. En una instalación también podés dejar activada la comprobación al iniciar; esa consulta solo avisa cuando hay una nueva versión. No descarga ni instala automáticamente y se puede desactivar desde el mismo diálogo.

La edición portable permite consultar las versiones y abrir las descargas oficiales. Su archivo no se reemplaza mediante la instalación automática; si elegís otro portable, seguís utilizando el formato independiente.

Las preliminares permiten probar cambios antes de su entrega estable. Se ofrecen únicamente si son posteriores a la versión instalada, tienen instalador compatible y un manifiesto firmado válido del canal preliminar. El diálogo identifica ese canal y mantiene también las estables como candidatas. Las preliminares históricas sin ese manifiesto se pueden consultar en GitHub, pero no se instalan desde el actualizador.

Volver a **Sólo versiones estables** no instala una versión anterior: si tu preliminar es más nueva, se esperará a una estable posterior. Cambiar el canal descarta la selección de descarga anterior y realiza una consulta nueva. Si no puede completarse la consulta de preliminares, el diálogo lo informa y conserva únicamente las versiones que logró verificar.

## Descargar, instalar y reiniciar

1. Elegí **Descargar actualización** cuando aparezca una versión posterior compatible del canal elegido.
2. Continuá trabajando mientras se obtiene el instalador completo y se verifica su integridad.
3. Guardá o exportá los resultados de la sesión que quieras conservar.
4. Elegí **Instalar y reiniciar** cuando hayan terminado los cálculos y confirmá el cierre de la aplicación.

La nueva versión se instala sobre la existente y vuelve a abrir SignalLab. Los temas y la configuración persisten; los resultados sin guardar no se recuperan automáticamente como una sesión completa. Un fallo de conexión o de verificación deja disponible la instalación anterior y se informa en el diálogo.

En Linux, los archivos nuevos se preparan antes de cambiar la versión activa. Se conserva la activa y una anterior, y se eliminan las versiones administradas más antiguas después de una actualización correcta. Si falla la activación, se restaura la versión previa.

## Qué verifica el actualizador

La aplicación incorpora una clave pública Ed25519 para verificar `SignalLab-updates.json`. Ese manifiesto firmado identifica la versión, las direcciones oficiales de los instaladores, sus tamaños, sus hashes SHA-256 y una fecha de expiración. La clave privada se utiliza localmente al preparar la entrega y permanece fuera del repositorio.

El actualizador rechaza firmas ajenas, manifiestos vencidos, archivos alterados o incompletos y paquetes incompatibles. Comprueba de nuevo la integridad antes de ejecutar el instalador y evita reemplazar una instalación por una versión anterior, incluso si quedó abierta una ventana de una versión antigua.

Esta verificación es distinta de Authenticode. **Los ejecutables Windows siguen sin una firma de publicador reconocida por el sistema** y pueden ser bloqueados en la primera instalación. El formato instalable y la firma Ed25519 del canal no eliminan ese bloqueo. [Firma y alertas de Windows](windows-downloads.md).

## Red y privacidad

Las consultas y descargas utilizan GitHub. Se envía la solicitud de red correspondiente, con la versión de la aplicación; no se transmiten señales, fórmulas, documentos ni resultados. La [política de privacidad](privacy.md) detalla el funcionamiento local y los servicios externos utilizados.

## Desinstalar

En Windows, usá la opción de desinstalación del sistema. En Linux, elegí **Desinstalar SignalLab PC** desde el acceso del menú. Para la ruta predeterminada también podés ejecutar:

```sh
~/.local/bin/signallab-pc --install-linux --uninstall
```

La desinstalación retira los archivos y accesos administrados por SignalLab. Conserva la configuración y los documentos del usuario; también conserva archivos desconocidos agregados en la raíz de instalación.

## Construcción y publicación

Las instrucciones para crear los instaladores y firmar el manifiesto están en [Compilar y publicar](development/releases.md) y [Verificación y firma de las distribuciones](development/signing.md). Los artefactos temporales de una construcción no se convierten en una release hasta completar su publicación.
