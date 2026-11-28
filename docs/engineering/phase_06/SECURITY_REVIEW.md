# Seguridad y archivos RF

| Superficie | Decisión y control |
| --- | --- |
| Touchstone | El importador lee texto decimal en un archivo regular y limita tamaño, longitud de línea, número de puertos y entradas. Los comentarios se descartan. Los formatos, el orden, las frecuencias y las secciones deben ajustarse al contrato admitido. |
| Archivos RF de proyecto | Verificar dimensiones antes de decodificar. Cotejar codificación canónica, longitud, SHA-256 y procedencia. SLPROJ verifica el contenido completo antes de devolver el proyecto. |
| Escritura | Touchstone, proyectos y campañas conservan reemplazo atómico y cancelación cooperativa. Una campaña interrumpida conserva sólo los bloques confirmados para reanudar. |
| Presupuesto | La admisión comparte el pool del núcleo. Los tamaños declarados por el archivo se cotejan antes de reservar las matrices. Los límites operativos estiman el trabajo admitido. |
| Distribución | Se preservan el inventario nativo, SBOM, comprobación de OpenSSL por plataforma y manifiesto firmado. Los controles se vuelven a ejecutar para el candidato. |
| Dependencias | Se usan las versiones bloqueadas del proyecto. Los comparadores y documentos externos sirven de referencia matemática. |

Se mantienen las restricciones de importación MATLAB de Fase 02C, el seguimiento nativo de Qt/HDF5 y el registro de Authenticode separado de la firma del actualizador. [Riesgos acumulados](../RISK_REGISTER.md)
