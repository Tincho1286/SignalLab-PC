# SignalLab PC 0.21

- FIR e IIR reciben frecuencia angular en rad/muestra; aceptan pi/4 y expresiones numéricas. Conversión interna a la convención del motor, sin cambiar el diseño matemático. Nyquist es π.
- Polos y ceros con edición por clic, movimiento y eliminación; pares conjugados opcionales. El diseño se actualiza al terminar una edición válida. Una definición digital con más ceros que polos queda pendiente y no se presenta como un sistema válido.
- Botón directo Ver respuesta temporal con el último sistema calculado; se desactiva al editar hasta que haya un resultado nuevo.
- Biblioteca propia de ayuda por herramienta con propósito, pasos y unidades; acceso contextual desde cada pantalla.
- Se eliminan referencias visibles al texto de la calculadora. Los archivos históricos de referencia permanecen separados del contenido de ayuda de la aplicación.
- Incluye entrada directa de coeficientes para DFT inversa.

No se ejecutaron pruebas ni diagnósticos, por pedido del usuario. El empaquetado no acredita funcionamiento. Fs sigue siendo una tasa en muestras/s; las frecuencias físicas etiquetadas en Hz no son frecuencias normalizadas. La aplicación y su interfaz siguen en desarrollo.
