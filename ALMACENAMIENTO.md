# Almacenamiento del proyecto

El código, las referencias de la materia, el entorno Python, los respaldos y todas las versiones entregadas se conservan. La primera versión continúa en releases/v0.1.0.

## Compilar sin acumular temporales

Usar build_portable.ps1 para las próximas entregas. Después de generar y guardar el ejecutable, elimina solamente la carpeta intermedia de esa compilación dentro de work/pyinstaller. Con -KeepBuildFiles se conserva para diagnóstico. Una compilación fallida también conserva sus intermedios.

El ejecutable se genera primero en work/portable-output y luego reemplaza atómicamente su entrada en outputs. Así, recompilar con el mismo nombre no modifica copias históricas que compartan almacenamiento. Conservar esta forma de publicación al crear otros asistentes de compilación; no volver a acumular un directorio intermedio por cada versión.

## Mantenimiento de históricos

tools/optimize_storage.py informa por defecto; --apply efectúa la limpieza. Ejecutarlo con la aplicación y las compilaciones cerradas. Admite --deliveries con la carpeta de entregas para comparar sus ejecutables con los de outputs, releases y dist.

Sólo elimina directorios SignalLab-PC generados dentro de work/pyinstaller o build que contengan Analysis-00.toc. Verifica antes sus rutas y rechaza enlaces de carpetas. No borra .venv, fuentes, referencias, trabajo pendiente ni respaldos before.

Los ejecutables con igual tamaño y SHA-256 pueden compartir los mismos datos mediante enlaces duros en el mismo disco. Se conservan todos los nombres y rutas y siguen siendo ejecutables completos. Copiar uno a otro disco o pendrive produce un archivo portable normal. Borrar una de las rutas no borra las demás. No editar un histórico en el lugar: para sustituirlo, reemplazar su entrada con un archivo nuevo, como hace build_portable.ps1.

El Explorador puede sumar varias veces el tamaño lógico de estos archivos aunque ocupen una sola vez el espacio físico. La recuperación real se mide por el espacio libre del disco. work/storage-maintenance.json registra las carpetas limpiadas, los archivos enlazados y sus hashes.

## Almacenamiento remoto

Los históricos verificados pasan a releases del repositorio privado Tincho1286/SignalLab-PC. Localmente se retienen el portable actual, el anterior y el primero. El código y las referencias de trabajo siguen disponibles sin descargar todos los ejecutables; .gitignore excluye los portables y los temporales. Ver RELEASES_GITHUB.md.

Migración realizada el 28 de octubre de 2026: 112 ejecutables distintos comprimidos y verificados en un archivo de unos 222 MiB, publicado en GitHub privado. Se retiraron 212 rutas locales históricas después de verificar los adjuntos remotos. Se recuperaron otros 11,88 GiB y el disco quedó con aproximadamente 36,12 GiB libres. Los recibos de publicación y limpieza quedan en work/remote-release y work/github-storage-prune.json, fuera de Git.

Entrega 0.99.9: publicada y verificada en GitHub; copias locales actuales 0.99.9 y 0.99.8, más v0.1.0. La 0.99.7 se retiró después de comprobar su correspondencia con el respaldo histórico remoto. El compilador eliminó sus intermedios al terminar.

Entrega 0.99.10: publicación por la herramienta de releases del proyecto y verificación de adjuntos. Se conservan 0.99.10, 0.99.9 y el primer portable; 0.99.8 se retiró tras verificar su release individual. Sin intermedios de compilación acumulados.

Entrega 0.99.11: publicación por la herramienta de releases del proyecto y verificación de adjuntos. Se conservan 0.99.11, 0.99.10 y el primer portable; 0.99.9 se retiró tras verificar su release individual. Sin intermedios de compilación acumulados.

Entrega estable 1.0.0: publicada como última estable en GitHub privado y verificados sus cinco adjuntos. Retención local 1.0.0, 0.99.11 y v0.1.0; 0.99.10 se retiró tras comprobar su release. Los intermedios de la compilación estable se limpiaron automáticamente.

Entrega estable 1.0.1: publicada como última estable en GitHub privado, con sus cinco adjuntos verificados. Se conservan localmente 1.0.1, 1.0.0 y v0.1.0. La copia de 0.99.11 en la carpeta de entrega quedó pendiente de limpieza porque Windows impidió eliminarla mientras la versión anterior seguía en ejecución; no se interrumpió la aplicación. Su hash y ubicación se registran en work/remote-release/1.0.1/pending-cleanup.json. Los intermedios de compilación se limpiaron automáticamente.

Entrega estable 1.0.2: cinco adjuntos verificados en GitHub privado; portable compartido mediante enlace físico con la carpeta de entrega. Se conservan 1.0.2, 1.0.1 y la primera versión. La versión 1.0.0 se retiró localmente tras verificar sus adjuntos remotos, salvo cualquier ruta bloqueada por Windows. Las copias pendientes, incluida la anterior 0.99.11 en uso, están registradas en work/remote-release/1.0.2/pending-cleanup.json. No se interrumpieron aplicaciones abiertas. Intermedios de compilación limpiados.

Entrega estable 1.1.0: seis adjuntos verificados en GitHub privado; portable compartido mediante enlace físico con la carpeta de entrega. Se conservan 1.1.0, 1.0.2 y la primera versión. La versión 1.0.1 se retiró localmente tras verificar sus adjuntos remotos, salvo cualquier ruta bloqueada por Windows. Las copias pendientes, incluida la anterior 0.99.11 en uso, están registradas en work/remote-release/1.1.0/pending-cleanup.json. No se interrumpieron aplicaciones abiertas. Intermedios de compilación limpiados.

Entrega estable 1.1.1: seis adjuntos verificados en GitHub privado; portable compartido mediante enlace físico con la carpeta de entrega. Se conservan 1.1.1, 1.1.0 y la primera versión. La versión 1.0.2 se retiró localmente tras verificar sus adjuntos remotos, salvo cualquier ruta bloqueada por Windows. Las copias pendientes, incluida la anterior 0.99.11 en uso, están registradas en work/remote-release/1.1.1/pending-cleanup.json. No se interrumpieron aplicaciones abiertas. Intermedios de compilación limpiados.
