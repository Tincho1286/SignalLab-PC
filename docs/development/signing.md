# Verificación y firma de las distribuciones

[← Desarrollo](README.md)

El proceso actual construye instaladores y portables en Windows y Linux, y firma localmente el manifiesto de actualización. Esa firma es independiente de Authenticode; el [estado de las firmas](../code-signing.md) se documenta por separado para no confundir una integración disponible con un servicio habilitado.

## Construcción identificada

El [flujo de distribuciones](../../.github/workflows/portable.yml) se inicia manualmente sobre `main` o una etiqueta `v…`. Construye ambas plataformas por defecto, utiliza el commit seleccionado y las dependencias fijadas, y ejecuta los controles matemáticos, estáticos y de reutilización. Después genera y comprueba los instaladores nativos.

Cada salida conserva versión, hash y procedencia. Los comprobantes de instalador incluyen el commit y una huella del código relevante normalizada para que la misma fuente tenga la misma identidad en ambos sistemas. No se acepta un portable antiguo sin actualizador como base de un nuevo instalador.

## Firma local Ed25519

La clave privada debe permanecer fuera del repositorio y de los artefactos de GitHub. Conservá una copia de seguridad protegida: las instalaciones existentes verifican contra la clave pública distribuida y dependen de esa identidad. No generes una clave nueva para cada entrega.

Descargá ambos instaladores y sus comprobantes `installer-windows.json` e `installer-linux.json` desde la misma construcción. Con el checkout limpio del commit correspondiente, ejecutá:

```powershell
.\.venv\Scripts\python.exe -B tools\update_signing.py sign `
  --version VERSION `
  --private-key RUTA_PROTEGIDA\private.pem `
  --installer RUTA_WINDOWS\SignalLab-PC-VERSION-setup.exe `
  --installer RUTA_LINUX\SignalLab-PC-VERSION-linux-x86_64.run `
  --notes NOTAS_DE_ACTUALIZACION.txt `
  --output outputs\SignalLab-updates.json
```

Reemplazá `VERSION` y las rutas por los archivos reales. Las notas del diálogo pueden ser texto breve y legible; las notas completas de la Release desarrollan los cambios. El firmador comprueba versión, origen, tamaños, hashes y correspondencia entre las claves antes de producir el manifiesto, y verifica su propia salida.

La vigencia predeterminada es de 90 días. Para renovarla hay que volver a verificar los instaladores originales y firmar desde el código correspondiente, manteniendo su identidad. El cliente rechaza un manifiesto vencido. La publicación debe conservar consistentes el manifiesto y sus checksums.

## Firmar una preliminar compatible con el actualizador

La versión de la aplicación y la etiqueta conservan tres componentes numéricos: por ejemplo, `1.8.4` y `v1.8.4`. Para una entrega preliminar agregá `--channel preview` al comando de firma y publicala en GitHub con `prerelease=true`. Para una estable usá `--channel stable` (predeterminado) y `prerelease=false`. El canal forma parte de los datos firmados; cambiarlo requiere generar un manifiesto nuevo a partir de los mismos instaladores verificados. No basta con editar el JSON o el estado de la Release.

El cliente estable no acepta manifiestos del canal preliminar. El cliente que incluye preliminares verifica además que la versión firmada coincida con la etiqueta consultada. Las etiquetas históricas con sufijos como `-preview` siguen disponibles en GitHub, pero no se incorporan a este protocolo de actualización.

## Metadatos Windows y Authenticode opcional

`tools/windows_version.py` genera los recursos de versión para PyInstaller: `ProductName` es `SignalLab PC`, `ProductVersion` coincide con la aplicación y `FileVersion` utiliza cuatro componentes numéricos. El nombre original debe corresponder al archivo construido.

`request_signing=false` es el modo utilizado actualmente. La rama opcional `request_signing=true` requiere una cuenta y política de SignPath aprobadas, credenciales, configuración de artefacto y aprobación humana; sin ellas la construcción solicitada falla. Esa rama espera una respuesta y exige validar Authenticode antes de ofrecerla como firmada. La clave Ed25519 no interviene en ese servicio.

Los artefactos de Actions expiran; no son una publicación definitiva. El orden de subida, las fuentes, los checksums y la activación del canal estable se explican en [Compilar y publicar](releases.md).
