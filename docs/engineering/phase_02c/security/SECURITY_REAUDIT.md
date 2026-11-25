# Revisión de seguridad

El lector de fondos identifica PNG, JPEG, WebP o BMP antes de crear el lector Qt. Se mantiene el límite de píxeles y el decoder explícito. La interfaz usa sus iconos SVG instalados. Se revisaron importaciones de Qt y no se encontró uso directo de `QCborValue` para datos de usuario. La versión del componente sigue afectada por el aviso de CBOR aun con la ruta ajena al importador. Se verificó lectura válida PNG y rechazo de un SVG ordinario como fondo.

Qt 6.12.1 está publicado por Qt desde el 24 de noviembre de 2026. Las consultas a PyPI para Essentials y shiboken6 devolvieron 404. Sigue abierta la excepción de componente para distribución. Para levantarla hay que verificar las ruedas compatibles y repetir los portables. [Publicación de Qt](https://www.qt.io/blog/qt-6.12.1-released) · [Aviso de CBOR](https://www.qt.io/blog/security-advisory-cve-2026-105924) · [Aviso SVG corregido a partir de 6.12.0](https://www.qt.io/blog/security-advisory-cve-2026-8168)
