# Integridad de persistencia

Las regresiones ejercitan truncado, longitud, digest, claves JSON duplicadas, cancelación antes de reemplazar y fallo de `os.replace`. El caso SLBIN verifica los bytes con `struct` y `hashlib`, independientemente del cargador. Cada publicación del Core verifica la instantánea efectiva y los padres. La reapertura comprueba el registro verificado, incluso tras exportar e importar un subconjunto.

El reemplazo atómico distribuye siempre una versión completa mediante el mismo sistema de archivos. La aplicación no garantiza durabilidad frente a pérdida eléctrica del directorio en todas las plataformas.
