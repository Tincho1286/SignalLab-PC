# Compilar y publicar versiones

[← Desarrollo](README.md)

Las entregas actuales ofrecen instaladores y portables para Windows x64 y Linux x86_64. Una publicación reúne los archivos construidos, su fuente correspondiente, las licencias y los checksums; el canal estable añade el manifiesto firmado de actualización. Compilar un artefacto y publicar una Release son etapas diferentes.

## Preparar la entrega

Actualizá la versión en `signallab_pc/__init__.py`, redactá `docs/releases/vVERSION.md` y revisá las descargas del README, el changelog y los índices de versiones. Las notas deben explicar el problema o capacidad que cambia, el comportamiento resultante y sus límites, agrupando las áreas relacionadas en párrafos conectados. Los objetivos pendientes pertenecen a la hoja de ruta, sin prometer una versión futura.

Guardá todo en un commit y subilo a `main` antes de construir. La versión de los archivos, los metadatos del ejecutable y el código deben coincidir. Las etiquetas de una entrega existente no se mueven para acomodar una construcción nueva.

## Construir portables e instaladores

El [flujo de distribuciones](../../.github/workflows/portable.yml) permite elegir `both`, `windows` o `linux`, con ambas plataformas como opción predeterminada. Utilizá `request_signing=false` mientras no exista un servicio Authenticode aprobado. El flujo ejecuta los controles requeridos, genera los portables, construye los instaladores por usuario y comprueba instalación, actualización y desinstalación en los sistemas nativos.

Para construir localmente un portable Windows con el entorno preparado:

```powershell
.\build_portable.ps1
```

En Linux x86_64:

```sh
bash build_portable_linux.sh
```

Los archivos quedan en `outputs/`. PyInstaller empaqueta para el sistema donde se ejecuta: un ejecutable Windows no se convierte en Linux mediante un cambio de extensión. [Preparar el entorno](README.md) · [Compatibilidad Linux](../linux.md).

Los instaladores se generan desde portables con comprobantes válidos mediante `tools/build_installers.py windows` o `tools/build_installers.py linux`. Windows necesita Inno Setup 6. Los comprobantes impiden utilizar un binario de otra versión, fuente o clave pública como si correspondiera al código actual.

## Verificar y firmar

Descargá los instaladores y portables del mismo commit. Contrastá los hashes y los metadatos de procedencia y conservá los informes de construcción para la revisión técnica. Los detalles de las pruebas no sustituyen la explicación funcional de las notas de versión.

Firmá localmente `SignalLab-updates.json` con los dos instaladores verificados y la clave privada protegida. La [guía de firma](signing.md) describe el comando. La clave privada nunca se incorpora al repositorio, a los artefactos ni a una Release; solo se publican el manifiesto firmado y los archivos identificados por él.

## Archivos de la publicación

| Archivo | Finalidad |
| --- | --- |
| `SignalLab-PC-VERSION-setup.exe` | Instalador Windows por usuario. |
| `SignalLab-PC-VERSION-linux-x86_64.run` | Instalador Linux por usuario. |
| `SignalLab-PC-VERSION.exe` | Portable Windows. |
| `SignalLab-PC-VERSION-linux-x86_64.tar.gz` | Portable Linux con documentación y avisos. |
| Archivo de fuentes y licencias | Código y avisos correspondientes a las construcciones publicadas. |
| Procedencia y comprobantes | Identificación del código, el entorno y los binarios. |
| `SignalLab-updates.json` | Metadatos firmados para el canal de actualización. |
| `SHA256SUMS-VERSION.txt` | Integridad de los adjuntos; no incluye su propio hash. |

Si las plataformas se construyeron desde commits distintos, conservá sus fuentes y procedencias diferenciadas. No atribuyas a ambas un único archivo de fuentes que no corresponda a una de ellas.

## Publicar en GitHub

La herramienta `tools/github_release.py` comprueba el checkout y la correspondencia con `origin/main`. Se le pasan las notas mediante un archivo y cada adjunto mediante `--file`. La opción `--stable` publica una estable; sin ella se publica una preliminar. `--allow-public` habilita expresamente el repositorio público configurado.

El publicador crea un borrador, sube y verifica los archivos y luego activa la publicación. Conserva el commit exacto de construcción y fecha las etiquetas nuevas con la hora de GitHub. Una etiqueta existente que apunte a otro commit provoca un error y no se reemplaza.

Después de publicar una estable, comprobá que sea la descarga principal y que `releases/latest/download/SignalLab-updates.json` entregue el manifiesto esperado con una firma válida. Las preliminares no deben reemplazar ese canal. Revisá también que todos los enlaces del README apunten a adjuntos realmente disponibles.

## Mantener las notas y el historial

El [índice de versiones](../releases/README.md), `catalog.json` y `index.json` deben reflejar las publicaciones reales, sus canales y sus formatos. Una edición de la documentación puede mejorar la descripción de una entrega sin recompilar, reemplazar sus binarios ni cambiar su etiqueta o estado.

Las notas actuales están en la documentación y en el cuerpo de cada Release. Los archivos Markdown adjuntos a una entrega son la copia incluida al publicarla y pueden conservar una redacción anterior. No se reescriben las fuentes, los manifiestos firmados o los checksums originales para hacer una corrección editorial. Si un documento adjunto necesitara reemplazarse, su integridad y el registro de publicación tendrían que actualizarse de forma explícita y coherente.

Los ejecutables se conservan en Releases, fuera del historial Git. La [guía de almacenamiento](storage.md) explica el tratamiento de salidas locales y versiones históricas.
