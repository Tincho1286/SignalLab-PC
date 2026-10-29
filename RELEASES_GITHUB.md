# Versiones privadas en GitHub

Repositorio: https://github.com/Tincho1286/SignalLab-PC

Las versiones se publican en https://github.com/Tincho1286/SignalLab-PC/releases. Se necesita una cuenta con acceso al repositorio privado para verlas y descargarlas. Los ejecutables son adjuntos de las versiones, fuera del historial del código: clonar el repositorio no descarga todos los portables.

## Publicar la siguiente versión

1. Guardar los cambios de código y documentación en un commit y subir main.
2. Compilar con build_portable.ps1, que limpia sus temporales al terminar correctamente. No sobreescribir ejecutables históricos en el lugar.
3. Publicar desde la raíz con el Python del proyecto:

```powershell
.\.venv\Scripts\python.exe -B tools\github_release.py --tag v1.1.1 --title "SignalLab PC 1.1.1" --notes VERSION_1.1.1.md --file outputs\SignalLab-PC-1.1.1.exe --stable
```

Cambiar versión, título, notas y archivo para cada entrega. La herramienta usa la sesión de Git existente; no guarda tokens en el proyecto. Comprueba que el repositorio sea privado y que main remoto coincida con el commit local, publica primero un borrador y verifica tamaño y SHA-256 de cada adjunto antes de mostrar la versión. Por defecto publica como preliminar; --stable se usa para la línea estable; sin esa opción se publica como preliminar. Un nombre existente con contenido distinto se rechaza, no se reemplaza.

Después de publicar, sincronizar las etiquetas con git fetch --tags. Conservar localmente la versión actual, la inmediatamente anterior y el primer portable. Retirar históricos solamente cuando estén respaldados y verificados en GitHub; eliminar todas sus copias locales si comparten enlaces duros para recuperar el espacio.

## Históricos anteriores a Git

El archivo de versiones del 28 de octubre de 2026 guarda los ejecutables anteriores, sus tamaños y SHA-256. También se conservan el primer portable y su ZIP de código original como adjuntos independientes. El archivo comprimido mantiene las rutas relativas del proyecto; su manifiesto permite ubicar cada versión.

El historial Git comienza con el código 0.99.8. El archivo de ejecutables no inventa commits de código para versiones antiguas: sus fuentes sólo están disponibles cuando existía un respaldo original. Las etiquetas del archivo histórico señalan el momento del respaldo, no la implementación de todos los ejecutables incluidos.

Los programas de la materia, documentos personales, entorno Python, temporales y borradores externos permanecen locales y fuera del repositorio. El trabajo continuo con Dirac que se preparó en otra carpeta se integró, después de revisarlo sobre la base actual, en la versión 0.99.9. Los borradores históricos externos permanecen fuera de main.

## Publicaciones disponibles

- [1.1.0 estable](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.1.0): modelos AR/MA/ARMA estacionarios, estimación AR por Yule–Walker, correlación cruzada y ayudas ilustradas.

- [1.0.2 estable](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.0.2): expresiones de respuesta al impulso ideal, ventana y FIR obtenido, con ganancia y desplazamiento reales.

- [1.0.1 estable](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.0.1): aclaración de transiciones especificadas y corrección del retardo FIR.

- [1.0.0 estable](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.0.0): primera estable, corrección del estado de resultados, alcance y SHA-256.

- [0.99.11 preliminar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v0.99.11): diseño unificado, formularios despejados y exportaciones junto al resultado.

- [0.99.10 preliminar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v0.99.10): elección de Fourier, dirección conservada y búsqueda por variante.

- [0.99.9 preliminar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v0.99.9): carga continua y presentación de pesos Dirac, notas y SHA-256.

- [0.99.8 preliminar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v0.99.8): ejecutable, notas y SHA-256.
- [Archivo histórico y primera versión](https://github.com/Tincho1286/SignalLab-PC/releases/tag/archivo-historico-2026-10-28): 112 ejecutables distintos en 222 MiB, primer portable y fuentes originales de v0.1.0. El archivo contiene también la 0.99.8 como parte de la foto histórica.

Los enlaces, tamaños y huellas de los adjuntos están en docs/releases/index.json. El manifiesto histórico en esa misma carpeta enumera las versiones y las ubicaciones duplicadas que tenían antes de retirarse del disco. Para recuperar una versión, descargar el TAR.ZST y extraerlo; Windows en este equipo incluye tar con Zstandard. La guía completa está adjunta a la publicación histórica.
