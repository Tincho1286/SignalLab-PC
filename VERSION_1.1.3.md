# SignalLab PC 1.1.3 · generar ventanas como señales

En Señales → Crear una señal se agrega la definición Ventana, junto a Fórmula o muestras. La ventana se genera de forma independiente; no requiere cargar h[n] ni diseñar antes un filtro.

- Rectangular, Hann, Hamming, Blackman, Bartlett y Kaiser. Se usan las variantes simétricas del diseño FIR.
- Longitud L seleccionable: cantidad total de muestras, no semilongitud ni orden M. Para un FIR con esa longitud, M=L−1 es el orden nominal.
- Índice inicial entero o centrado alrededor de cero. Con L impar el centrado es exacto en n=0; con L par se usan −L/2…L/2−1 y el centro geométrico es −1/2, sin inventar índices fraccionarios.
- β disponible al elegir Kaiser. No se añade normalización de pico, suma ni energía. L=1 produce una única muestra de valor uno.
- Resultado como señal discreta con gráfico de tallos, tabla e informe de la definición y los índices. Exportación nativa JSON/CSV con sus metadatos, y reutilización en Fourier, Z o producto de señales.
- Se corrige el envío de señales a Transformada Z: ahora abre Muestras finitas con el registro y su origen ya cargados. Esto también sirve para las otras secuencias de la aplicación.
- La ayuda incluye un diagrama de colores con L=17 sobre n=−8…8. El resultado finito vale cero fuera de su intervalo; no se supone una repetición periódica.

Los extremos que son cero por definición en Hann, Bartlett y Blackman se conservan como cero exacto, evitando términos de redondeo ficticios al estudiar la Z. No se eliminan otros valores pequeños. Kaiser usa la evaluación estándar y una forma estable con Bessel escalada si el cociente ordinario desborda para un β elevado.

Comprobaciones dirigidas de compatibilidad con las ventanas FIR existentes, longitud e índices, una muestra, formas conocidas, extremos, Kaiser, fase de DTFT, exportación JSON/CSV y recepción real en Z finita/Fourier. Se comprobó en el panel real una ventana centrada y W(z)=z+1+z⁻¹ para tres muestras unitarias sobre n=−1,0,1. No se ejecutó una batería general.

La navegación conserva 30 problemas y pasa a 84 variantes, más CAS. Referencia de la convención simétrica: [get_window de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.get_window.html). Se emplean las dependencias fijadas del proyecto.
