# Requisitos de almacenamiento científico

**Criterios previos de WP-02B.04.** Medir tamaños desde 1.024 hasta 1.048.576 de datos reales y complejos. Repetir también la sesión de 65.536 del piloto. El ensayo usa un tope por caso de 512 MiB y un factor de admisión conservador de 256 bytes por muestra. Si un tamaño excede el presupuesto, se registra la exclusión. Medir lectura, escritura con sincronización, acceso parcial, tamaño, pico residente y concordancia exacta del arreglo. Conservar mediana, dispersión y plataforma.

El backend experimental debe cargar un archivo sin referencias externas ni objetos deserializables. Requiere metadatos acotados, longitud exacta, huella de integridad y destino reemplazado de forma atómica. El proyecto y las sesiones conservan JSON.
