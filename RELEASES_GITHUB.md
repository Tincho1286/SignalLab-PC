# Versiones privadas en GitHub

Repositorio: https://github.com/Tincho1286/SignalLab-PC

Las versiones se publican en https://github.com/Tincho1286/SignalLab-PC/releases. Se necesita una cuenta con acceso al repositorio privado para verlas y descargarlas. Los ejecutables son adjuntos de las versiones, fuera del historial del código: clonar el repositorio no descarga todos los portables.

## Publicar la siguiente versión

1. Guardar los cambios de código y documentación en un commit y subir main.
2. Compilar con build_portable.ps1, que limpia sus temporales al terminar correctamente. No sobreescribir ejecutables históricos en el lugar.
3. Publicar desde la raíz con el Python del proyecto:

```powershell
.\.venv\Scripts\python.exe -B tools\github_release.py --tag v0.99.8 --title "SignalLab PC 0.99.8" --notes DESARROLLO_0.99.8.md --file outputs\SignalLab-PC-0.99.8-preview.exe
```

Cambiar versión, título, notas y archivo para cada entrega. La herramienta usa la sesión de Git existente; no guarda tokens en el proyecto. Comprueba que el repositorio sea privado y que main remoto coincida con el commit local, publica primero un borrador y verifica tamaño y SHA-256 de cada adjunto antes de mostrar la versión. Por defecto publica como preliminar; --stable queda reservado para una versión estable real. Un nombre existente con contenido distinto se rechaza, no se reemplaza.

Después de publicar, sincronizar las etiquetas con git fetch --tags. Conservar localmente la versión actual, la inmediatamente anterior y el primer portable. Retirar históricos solamente cuando estén respaldados y verificados en GitHub; eliminar todas sus copias locales si comparten enlaces duros para recuperar el espacio.

## Históricos anteriores a Git

El archivo de versiones del 28 de octubre de 2026 guarda los ejecutables anteriores, sus tamaños y SHA-256. También se conservan el primer portable y su ZIP de código original como adjuntos independientes. El archivo comprimido mantiene las rutas relativas del proyecto; su manifiesto permite ubicar cada versión.

El historial Git comienza con el código 0.99.8. El archivo de ejecutables no inventa commits de código para versiones antiguas: sus fuentes sólo están disponibles cuando existía un respaldo original. Las etiquetas del archivo histórico señalan el momento del respaldo, no la implementación de todos los ejecutables incluidos.

Los programas de la materia, documentos personales, entorno Python, temporales y borradores externos permanecen locales y fuera del repositorio. La ampliación continua con Dirac preparada en otra carpeta de trabajo sigue pendiente y no se mezcla con main.
