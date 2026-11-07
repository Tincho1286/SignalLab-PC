# Instalación y actualizaciones

[← Documentación](README.md)

SignalLab PC puede distribuirse como portable y como aplicación instalada. Ambas ediciones incluyen Python y las dependencias necesarias; no requieren una instalación separada de Python. La disponibilidad de cada formato se comprueba en los adjuntos de [GitHub Releases](https://github.com/Tincho1286/SignalLab-PC/releases).

## Windows x64

El archivo `SignalLab-PC-VERSION-setup.exe` instala el programa para el usuario actual, por defecto en `%LOCALAPPDATA%\Programs\SignalLab PC`. Crea accesos en el menú Inicio y un registro de desinstalación. El acceso del escritorio es opcional.

Las entregas siguientes conservan la identidad de instalación y reemplazan los archivos del programa en la misma carpeta. No es necesario desinstalar antes. La configuración de SignalLab y los documentos del usuario permanecen fuera de los archivos administrados por el instalador.

El instalador no obtiene automáticamente una firma Authenticode reconocida por Windows. El Control inteligente de aplicaciones puede bloquear una instalación inicial sin suficiente confianza. La firma propia del actualizador descrita más abajo protege las descargas de actualización, pero no sustituye la firma del publicador ante Windows. [Firma y reputación](windows-downloads.md).

## Linux x86_64

El archivo `SignalLab-PC-VERSION-linux-x86_64.run` abre un instalador para el usuario actual. Se puede iniciar desde una terminal:

```sh
sh ./SignalLab-PC-VERSION-linux-x86_64.run
```

Reemplazá `VERSION` por el número del archivo descargado. No requiere `sudo`. Conserva los mismos requisitos de bibliotecas gráficas y compatibilidad del [portable Linux](linux.md).

La instalación predeterminada utiliza:

- `~/.local/share/SignalLab-PC/`: archivos y versiones del programa.
- `~/.local/bin/signallab-pc`: acceso al ejecutable activo.
- `~/.local/share/applications/org.signallab.PC.desktop`: entrada del menú de aplicaciones.

Se respetan los directorios XDG configurados para los datos y el menú. El programa conserva la versión activa y una anterior; las versiones administradas más antiguas se eliminan después de una actualización correcta. Una instalación nueva se prepara por completo antes de cambiar el enlace activo. Si falla esa activación, se conserva la versión anterior.

La acción **Desinstalar SignalLab PC** del acceso del menú, o el siguiente comando para la instalación predeterminada, abre el desinstalador:

```sh
~/.local/bin/signallab-pc --install-linux --uninstall
```

La desinstalación quita los archivos administrados y los accesos del programa. Conserva los temas, la configuración y los documentos. Los archivos desconocidos que el usuario haya agregado en la raíz de instalación se conservan.

## Buscar e instalar una actualización

En las ediciones que incorporan el actualizador, abrí **Ayuda → Buscar actualizaciones**. La edición instalada también puede comprobar novedades al iniciar; esa opción se puede desactivar en el mismo diálogo. La comprobación en segundo plano no descarga ni instala por sí sola.

Cuando hay una versión estable compatible:

1. **Descargar actualización** obtiene el instalador y comprueba su autenticidad e integridad.
2. La descarga queda preparada mientras continuás trabajando.
3. **Instalar y reiniciar** pide confirmación, espera que terminen los cálculos y cierra SignalLab para actualizarlo.

Antes de confirmar, guardá o exportá los resultados que quieras conservar. La configuración persiste entre versiones, pero una sesión con resultados sin guardar no se recupera automáticamente al reiniciar.

La edición portable conserva su funcionamiento independiente. Puede consultar las novedades y abrir la descarga oficial, pero no se convierte ni se instala automáticamente.

## Cómo se verifica una actualización

Cada entrega instalada utiliza un manifiesto `SignalLab-updates.json` con firmas Ed25519. La aplicación conserva la clave pública necesaria para verificarlo. El manifiesto identifica la versión, los dos instaladores, sus tamaños y sus checksums SHA-256. También contiene una fecha de expiración.

El actualizador acepta únicamente instaladores de la versión indicada en el repositorio oficial y rechaza firmas ajenas, descargas incompletas, contenidos modificados, plataformas incompatibles y retrocesos de versión. La integridad vuelve a comprobarse antes de iniciar el instalador.

El programa consulta metadatos públicos de GitHub. No envía señales, fórmulas, documentos ni resultados. GitHub recibe la solicitud de red correspondiente; la comprobación inicial se puede desactivar. [Privacidad](privacy.md).

## Construcción y publicación

El flujo existente de portables construye además los instaladores y verifica su instalación en Windows y Linux nativos. Sus artefactos conservan los informes de construcción e integridad. La creación de un artefacto de GitHub Actions no publica una nueva versión descargable.

La firma de actualizaciones se realiza **localmente**. La clave privada permanece fuera del repositorio y no se sube a GitHub. Se debe conservar una copia de seguridad protegida; las instalaciones existentes dependen de esa identidad. No se genera otra clave para cada versión.

Después de descargar los instaladores y sus comprobantes `installer-windows.json` e `installer-linux.json` del mismo commit, se crea el manifiesto:

```powershell
.\.venv\Scripts\python.exe -B tools\update_signing.py sign `
  --version VERSION `
  --private-key RUTA_PROTEGIDA\private.pem `
  --installer RUTA_WINDOWS\SignalLab-PC-VERSION-setup.exe `
  --installer RUTA_LINUX\SignalLab-PC-VERSION-linux-x86_64.run `
  --notes docs\releases\vVERSION.md `
  --output outputs\SignalLab-updates.json
```

El firmador comprueba la correspondencia entre versión, código, clave pública e instaladores. El manifiesto se publica junto con ambos instaladores, los portables, las fuentes, las licencias y sus checksums. Se utiliza una versión y una etiqueta correspondientes al commit de construcción; no se reemplazan silenciosamente los archivos de una entrega anterior.

La descarga del canal estable usa `releases/latest/download/SignalLab-updates.json`. Las preliminares no reemplazan ese canal. El manifiesto vence a los 90 días por defecto: si se necesita renovar su vigencia, hay que verificar los instaladores y volver a firmarlo localmente. No se acepta un manifiesto vencido como una actualización válida.

[Compilar y publicar](development/releases.md) · [Política de firma](code-signing.md)
