# Revisión de seguridad de Fase 03

El arranque aprovecha las dependencias ya inventariadas de 02C. Komm se usó en un directorio de auditoría para verificar referencias. El lock y el empaquetado del producto se heredan del Core. [Referencias y licencias](INTEGRATION_CATALOG.md) · [Inventarios 02C](../phase_02c/security/DEPENDENCY_CONTINUATION.md#verificación-de-e-01-en-64dc3c4)

La frontera de comunicaciones valida muestras finitas, dimensiones, tipos, reloj, energía y rangos de parámetros. Los órdenes de modulación y las configuraciones de barrido se comprueban con los presupuestos de cada etapa. Los registros de entrada tienen límites de tamaño y se validan antes de decodificar. La carga de proyectos utiliza la ruta existente y verifica la procedencia antes de incorporar resultados.

El catálogo acepta rutas previstas a archivos regulares, comprueba huellas y reserva un escritor por directorio. Se verificaron reemplazos de archivos, rutas fuera del catálogo, bloqueos entre procesos y cancelación antes de confirmar el índice. Las pruebas de empaquetado conservan el alcance aprobado de MAT para archivos confiables y el inventario completo de binarios.

El índice de PyPI del proyecto Qt ofrece 6.12.0 al 26 de noviembre de 2026. El candidato conserva las ruedas 6.12.1 fijadas por URL y SHA-256 en 02C. La matriz verifica la versión incluida en los binarios y la compilación de Pillow sin JPEG 2000. La auditoría de actualizaciones separa el manifiesto de prueba de Preview de la clave pública de distribución y del canal Stable/LTS. [Publicaciones de Qt en PyPI](https://pypi.org/project/PySide6-Essentials/#history) · [Auditoría de distribución](../DISTRIBUTION_INFRASTRUCTURE_AUDIT.md)
