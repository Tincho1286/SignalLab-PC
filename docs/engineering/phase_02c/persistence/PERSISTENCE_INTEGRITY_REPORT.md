# Integridad de persistencia

## Contratos binarios v1

Todos los enteros del encabezado tienen orden little-endian. Los formatos transportan vectores unidimensionales no vacíos, con un par IEEE 754 binary64 real e imaginario por muestra, en ese orden. El tamaño exacto se valida antes de reservar muestras. Los lectores rechazan cabeceras inconsistentes y claves repetidas. Una carga sólo se entrega después de comprobar el digest y validar el modelo.

| Offset o tramo | SLBIN | SLPROJ |
| --- | --- | --- |
| 0–7 | `SLPCBIN\x01` | `SLPROJ\x00\x01` |
| 8–11 | Longitud u32 de JSON, 1 B a 1 MiB | Longitud u32 de JSON, 1 B a 16 MiB |
| Desde 12 | Objeto con `count`, `origin`, `step`, `units`, `name`, `domain`, `expression` y `metadata` | Objeto con `project`, `workspace` y `counts`. Los registros de `project` usan el esquema JSON de proyecto. Los de señal omiten `data.values`. |
| Después de JSON | `count × 16` bytes de muestras | Un vector por señal en el orden de `records`. `counts[i]` vale 0 para un registro sin muestras. Máximo 10 000 registros. |
| Últimos 32 bytes | SHA-256 de encabezado, JSON y muestras | SHA-256 de encabezado, JSON y muestras |

La procedencia se conserva en los registros del proyecto y en sus hashes científicos. SLBIN conserva los metadatos declarados de una señal y no transporta su grafo de registros. SHA-256 detecta daños y desajustes respecto del contenido serializado. Un tercero con capacidad de reescritura también puede recalcular el digest.

Los escritores crean el temporal en el directorio del destino, ejecutan `fsync` sobre el archivo y lo sustituyen con `os.replace`. La cancelación y los fallos anteriores a la sustitución conservan el último archivo válido y limpian el temporal. El reemplazo evita que los lectores vean media escritura. La durabilidad después de una pérdida de alimentación depende del sistema de archivos y de sus garantías de persistencia de directorios y caché.

El escritorio sigue ofreciendo JSON como formato de guardado explícito predeterminado. SLPROJ es opcional para el usuario. La recuperación automática escribe por separado en SLPROJ en segundo plano y ofrece la recuperación de un punto JSON histórico cuando está disponible. Las sesiones con hoja CAS usan JSON esquema 4. Las que carecen de hoja conservan esquema 3. El contrato de hoja CAS v1 conserva valores codificados por el motor, historial, borrador, opciones y referencias a resultados publicados. La reapertura valida las referencias antes de restaurar la interfaz y muestra los resultados guardados. La evaluación simbólica se ejecuta cuando el usuario la solicita.

Las regresiones ejercitan truncado, longitud, digest, claves JSON duplicadas, cancelación antes de reemplazar y fallo de `os.replace`. El caso SLBIN verifica los bytes con `struct` y `hashlib`, independientemente del cargador. Cada publicación del Core verifica la instantánea efectiva y los padres. La reapertura comprueba el registro verificado, incluso tras exportar e importar un subconjunto.

El reemplazo atómico distribuye siempre una versión completa mediante el mismo sistema de archivos. La aplicación no garantiza durabilidad frente a pérdida eléctrica del directorio en todas las plataformas.
