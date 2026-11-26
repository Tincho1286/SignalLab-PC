# Compilar y publicar versiones

[← Desarrollo](README.md)

Las entregas ofrecen instaladores y portables para Windows x64 y Linux x86_64. Stable/LTS mantiene la familia 2.0.x. Preview reúne los avances acumulativos de SignalLab Engineering desde 2.1.0. Ambos canales requieren manifiesto firmado y archivos identificados por sus checksums. [Política de publicación y mantenimiento](../engineering/RELEASE_POLICY.md)

## Preparar la entrega

Actualizá la versión en `signallab_pc/__init__.py`, redactá `docs/releases/vVERSION.md` y revisá las descargas del README, el changelog y los índices de versiones. Las notas deben explicar el problema o capacidad que cambia, el comportamiento resultante y sus límites, agrupando las áreas relacionadas en párrafos conectados. Los objetivos pendientes pertenecen a la hoja de ruta, sin prometer una versión futura.

Para Preview, prepará el commit limpio en `develop` y verificá el mismo SHA en Windows y Linux. Para mantenimiento LTS, trabajá desde la última etiqueta estable en un checkout desacoplado. El commit de mantenimiento puede incorporar las adaptaciones de infraestructura necesarias para repetir los controles. La versión de los archivos, los metadatos y el código deben coincidir. El propietario autoriza la publicación y la creación de su etiqueta después de revisar el candidato.

## Construir portables e instaladores

El [flujo de distribuciones](../../.github/workflows/portable.yml) recibe el canal, el SHA completo y las plataformas. Preview se ejecuta sobre `develop` y comprueba que el SHA elegido esté en su historial. Así podés identificar el candidato aunque haya commits posteriores de documentación. Stable/LTS admite el SHA exacto de `main` cuando contiene código de esa familia o de una etiqueta LTS coincidente con el código. Un candidato LTS desacoplado que todavía no tiene etiqueta se compila y valida desde ese mismo commit en cada sistema. Usá `request_signing=false` mientras no haya un servicio Authenticode aprobado.

El Quality Gate de Fase 03 produce directamente los adjuntos del candidato para ambos sistemas. Guardá los comprobantes `candidate-windows.json` y `candidate-linux.json` con sus paquetes y el informe de la misma ejecución. Así se puede preparar la entrega a partir de lo que se probó. Los artefactos de Actions tienen retención temporal.

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

Las entregas nuevas requieren un único SHA validado en las dos plataformas. La fuente y los comprobantes deben identificar el mismo SHA.

## Publicar en GitHub

Con la autorización del propietario, usá `tools/github_release.py` con `--candidate SHA_COMPLETO`, `--quality-gate INFORME.json`, el archivo de notas y un `--file` por adjunto. `--allow-public` habilita el repositorio público configurado. Preview comprueba que el SHA pertenezca a `develop`. Para Stable/LTS usá `--stable --lts-base v2.0.X` desde el checkout desacoplado que contiene el candidato.

El informe acredita los controles de la entrega y lleva `commit`, `automated_passed` y `platforms`. Los nodos `windows-2022` y `ubuntu-22.04` deben incluir cada uno su objeto `candidate_bundle` emitido en la construcción correspondiente. El publicador coteja esos objetos con los dos comprobantes adjuntos. Para una corrección LTS, usá la evidencia del mantenimiento y de sus regresiones sobre el SHA desacoplado. Los controles científicos de una fase de Engineering corresponden a su propio candidato.

Las entregas con instaladores necesitan un manifiesto firmado entre sus adjuntos. El publicador comprueba el canal, la coincidencia entre versión y etiqueta y los tamaños y hashes de todos los instaladores declarados antes de crear la publicación. Para preliminares compatibles se utilizan etiquetas numéricas y `--channel preview` al firmar, como explica la [guía de firma](signing.md).

El publicador crea un borrador, sube y verifica los archivos y luego activa la publicación. Conserva el commit exacto de construcción y rechaza una etiqueta que apunte a otro commit. También conserva las entregas que ya están públicas.

Después de publicar una estable, comprobá que sea la descarga principal y que `releases/latest/download/SignalLab-updates.json` entregue el manifiesto esperado con una firma válida. Las preliminares no deben reemplazar ese canal. Revisá también que todos los enlaces del README apunten a adjuntos realmente disponibles.

## Mantener las notas y el historial

El [índice de versiones](../releases/README.md), `catalog.json` y `index.json` deben reflejar las publicaciones reales, sus canales y sus formatos. Una edición de la documentación puede mejorar la descripción de una entrega sin recompilar, reemplazar sus binarios ni cambiar su etiqueta o estado.

Las notas actuales están en la documentación y en el cuerpo de cada Release. Los archivos Markdown adjuntos a una entrega son la copia incluida al publicarla y pueden conservar una redacción anterior. No se reescriben las fuentes, los manifiestos firmados o los checksums originales para hacer una corrección editorial. Si un documento adjunto necesitara reemplazarse, su integridad y el registro de publicación tendrían que actualizarse de forma explícita y coherente.

Los ejecutables se conservan en Releases, fuera del historial Git. La [guía de almacenamiento](storage.md) explica el tratamiento de salidas locales y versiones históricas.
