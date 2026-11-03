# Versión 0.37

Implementado y empaquetado:
- Guardar sesión devuelve un resultado explícito: éxito, cancelación o error.
- Cerrar con muestras editadas exige guardado exitoso o descarte explícito. Cancelar el selector de archivo ya no autoriza el cierre aunque no haya registros nuevos en el proyecto.
- Los cálculos activos se atienden antes de preguntar por el guardado, evitando un diálogo de guardado seguido de rechazo del cierre.
- Se explica el alcance real de la sesión: resultados, entradas registradas y edición de muestras; los formularios sin calcular y disposición de ventanas aún no se restauran.

Hallazgo por inspección de código. Empaquetado completado correctamente y portable 0.37 copiado a la carpeta de entregas. Versiones anteriores conservadas. No se ejecutaron pruebas funcionales.
