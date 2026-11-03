# Versión 0.32

Implementado y empaquetado:
- Importación del CSV propio conservando dominio, complejos, eje y metadatos.
- Importación CSV/TSV externo con columnas explícitas, encabezados, separador y coma decimal opcional.
- Eje generado o leído; rechazo de ejes irregulares sin remuestreo silencioso.
- Vista previa de primeras líneas y errores con número de fila.

Empaquetado completado correctamente. Portable 0.32 generado y copiado a la carpeta de entregas; se conservan las versiones anteriores. No se ejecutaron pruebas funcionales.

- Unidades explícitas: segundos, milisegundos o microsegundos en tiempo; rad/s o rad/muestra en espectros. El tiempo se convierte a segundos sin modificar amplitudes.
