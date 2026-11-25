# Arquitectura de almacenamiento de proyectos

| Alternativa | Fortaleza | Costo |
| --- | --- | --- |
| JSON histórico | Portabilidad e inspección, reemplazo de un archivo | Listas de muestras, memoria y tiempo de codificación |
| Manifiesto con arreglos por digest | Deducción de duplicados y lectura por arreglo | Exportación completa, recolección y recuperación de componentes |
| Contenedor autocontenido | Un archivo para copiar y respaldar | Índice, límites de extracción y compatibilidad |
| HDF5 | Formato maduro y lectura por rangos | Mayor superficie nativa, reglas para enlaces y filtros |
| NPY, NPZ o SLBIN | Representación binaria compacta | Hay que definir semántica de referencias, metadatos y recuperación |

El costo de una migración excede la evidencia del volumen previsto. El piloto conserva JSON y mide un formato binario individual. Un contenedor futuro requiere publicar el manifiesto al final, validar los digests al abrir, recuperar la generación previa y gestionar temporales huérfanos sin tocar componentes válidos.
