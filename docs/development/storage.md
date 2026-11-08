# Almacenamiento de versiones

[← Desarrollo](README.md)

El repositorio contiene código, documentación y recursos. Los ejecutables, los entornos Python y los intermedios de compilación se mantienen fuera de Git.

- `outputs/`: portables, instaladores y archivos de publicación locales.
- `work/`: compilaciones, recibos de publicación y trabajo temporal.
- `build/` y `dist/`: salidas generadas por las herramientas de empaquetado.
- `.venv/`: entorno de desarrollo.
- GitHub Releases: distribución y respaldo de versiones publicadas.

`build_portable.ps1` elimina los intermedios de una compilación exitosa. Una compilación fallida conserva sus datos para diagnóstico. La sustitución del ejecutable se realiza al terminar, sin modificar en el lugar archivos históricos que compartan almacenamiento.

`tools/optimize_storage.py` ofrece mantenimiento de archivos generados. Las versiones anteriores sólo se retiran de la copia local cuando existe un respaldo identificado e íntegro. Los archivos en uso se conservan hasta que estén disponibles.

El [archivo histórico](https://github.com/Tincho1286/SignalLab-PC/releases/tag/archivo-historico-2026-10-28) reúne las primeras entregas, su manifiesto y una guía de recuperación.
