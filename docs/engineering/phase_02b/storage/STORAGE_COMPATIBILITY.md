# Compatibilidad del almacenamiento

`save_binary_signal` y `load_binary_signal` se habilitan sólo mediante API explícita. `.slbin` contiene una sola `Signal`. La cabecera máxima es 1 MiB. El tamaño declarado debe coincidir exactamente con el del archivo y el digest SHA-256 cubre cabecera y muestras. El lector admite sólo el dtype fijo, valida metadatos y verifica RAM estimada. El archivo guarda sus datos dentro del mismo contenedor.

La escritura usa el mismo mecanismo de temporales, sincronización y reemplazo de la sesión histórica. Los archivos JSON se leen y escriben como antes. La lectura del backend experimental es íntegra. Los ensayos parciales de los formatos con acceso por desplazamiento explican una oportunidad de evolución. El benchmark mide acceso parcial al prototipo híbrido sin verificar todo el archivo en esa medición, y mide verificación completa en la columna de lectura.
