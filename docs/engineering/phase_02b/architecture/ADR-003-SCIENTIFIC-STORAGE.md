# ADR 003 · Almacenamiento experimental para señales

**Estado** implementado, en validación. **Contexto.** La fase piloto mostró que codificar muestras como listas JSON domina el guardado. La misma ruta de sesión se volvió a medir.

**Requisitos.** Compatibilidad con JSON histórico, archivos autocontenidos e integridad y límites verificables. Se evaluaron JSON, NPY, NPZ, HDF5, SigMF y un híbrido.

**Decisión.** Ofrecer un archivo opcional para una señal, con cabecera JSON acotada, arreglo binario complejo de 128 bits little endian y SHA-256. La medición local mostró que el híbrido reduce tamaño y costo de escritura respecto de JSON. NPY ofrece un arreglo liviano, NPZ comprime con un costo adicional y HDF5 aporta jerarquía con más dependencias y validaciones. SigMF sigue como formato de intercambio I/Q evaluado.

**Consecuencias y compatibilidad.** La API experimental mantiene Project y session en JSON y conserva en el archivo el eje, reloj y metadatos de un `Signal`. La carga verifica toda la huella. El formato queda acotado a un arreglo por archivo y exige un lector SignalLab. La huella detecta daños del archivo y no acredita el productor.

**Riesgos y revisión.** Retomar formato predeterminado, autenticación o lectura parcial verificable si cambian requisitos de volumen o intercambio. Validar cabeceras, capacidad, corrupción, portabilidad y fallos de reemplazo. [Mediciones](../storage/STORAGE_BENCHMARK_REPORT.md)
