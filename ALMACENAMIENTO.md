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
