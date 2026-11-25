# Validación de entradas

| Familia | Control y alcance |
| --- | --- |
| JSON, proyectos, sesiones, diagramas y expresiones importadas | Lectura UTF-8 acotada en el descriptor y rechazo de claves repetidas. El esquema y la procedencia se verifican después en cada modelo. |
| CSV | El lector conserva el presupuesto del registro y el control de tamaños del encabezado. |
| MATLAB `.m` | Texto acotado y sintaxis aritmética interpretada mediante una lista de operaciones. |
| MAT | Se comprueba tamaño del archivo. En HDF5 sólo se cargan datasets numéricos con enlaces locales y dimensiones compatibles. Datos externos y datasets virtuales quedan fuera. El lector MAT clásico usa SciPy y conserva las restricciones de variables reconocidas. |
| SLBIN | Cabecera y tipos acotados, tamaño comprobado, datos binarios internos y digest. |
| Imágenes | Selección de decoder previa a la lectura Qt y control de dimensiones. |
| CAS y expresiones | Sintaxis propia y conversión simbólica controlada. El presupuesto de tiempo y memoria de expresiones largas se trata en el paquete de recursos. |
| Comprimidos | SLBIN y JSON no usan expansión comprimida. MAT admite el lector nativo existente. La extracción del inventario de portables usa artefactos producidos por CI. |

Se probaron archivos de datos sintéticos y simples. El alcance de dependencias nativas, tamaños y memoria de servicio se mantiene como control separado.
