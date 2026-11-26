# Decisiones de Fase 04

## Retardos fraccionarios y coherencia del impulso

La operación multitrayecto conserva retardos enteros. La interpolación lineal de dos muestras implementa un FIR de primer orden. A media muestra su módulo es $|\cos(\omega/2)|$, con error de −3,01 dB en π/2 y un cero en Nyquist para un retardo ideal de módulo uno. Para señales limitadas en banda, un sinc desplazado y truncado permite ajustar el error con longitud y ventana. Requiere declarar el borde de banda, la latencia añadida y la tolerancia de módulo y fase. La entrada discreta por sí sola no determina el modelo entre muestras. El deterioro temporal independiente implementa y verifica esa aproximación. El retardo fraccionario por camino queda sujeto a un contrato separado. [Formulación y condiciones del retardo fraccionario](https://arxiv.org/abs/1308.0797) · [Auditoría del deterioro temporal](MATHEMATICAL_AUDIT.md#protocolo-previo-para-errores-de-reloj-fase-e-iq).

Se agrupan trayectorias coherentes antes de aplicar el canal y de medir potencia. Esta decisión elimina la discrepancia entre un PDP por camino y el que se observa sobre un único tap del registro de salida. Para fading estocástico se distinguirá la potencia esperada por proceso de la potencia medida de la suma.

## Fronteras de integración

Las herramientas de Comunicaciones Digitales usan motores ejecutables con las importaciones de Qt bloqueadas. El enlace usa las mismas operaciones en una secuencia explícita. Los proyectos y corridas de Fase 03 son oráculos de compatibilidad. La construcción de candidatos usa la infraestructura de Fase 03 con manifiestos de prueba. Las claves de producción y las etiquetas requieren autorización separada.

## Generación de Clarke

Se evaluó una suma directa de rotadores con ángulos uniformes, un filtrado coloreado sobre una grilla FFT fija y cuadratura espectral de Gaussianas complejas. Con pocos rotadores de amplitud fija, la distribución de la envolvente solo se aproxima a Rayleigh. La grilla FFT fija puede representar mal un Doppler que ocupa una fracción de bin. La cuadratura usa masa integrada y frecuencias dependientes del Doppler solicitado. Mantiene marginales gaussianas y controla el coste mediante Zoom FFT, con una reserva antes de construir la transformada. Conserva una aproximación finita de la PSD continua, documentada en el contrato. La cancelación se observa entre llamadas nativas y durante la aplicación por bloques.

El desplazamiento de portadora es una operación separada que conserva el módulo de cada muestra. Su misma implementación sirve para Doppler determinista, CFO y fase constante. [Clarke](https://web.stanford.edu/~dntse/papers/main.pdf) · [Transformada](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ZoomFFT.html).

## Reloj alterado sobre un registro de duración finita

Para SFO se requiere el mismo número de muestras de observación, conservando el primer instante, con acceso directo a instantes fraccionarios. El conversor polifásico L/M existente cambia el número de muestras y necesita una rejilla intermedia que puede ser muy grande para errores pequeños en ppm. El núcleo Lanczos local calcula el valor únicamente en los instantes solicitados. El coste queda separado del denominador racional del reloj. La aproximación y los bordes se acreditan con un oráculo analítico y con una prueba de atenuación de una componente que se plegaría al reducir la tasa.
