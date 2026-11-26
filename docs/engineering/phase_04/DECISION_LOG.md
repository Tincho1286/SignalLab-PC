# Decisiones de Fase 04

## Retardos fraccionarios y coherencia del impulso

La primera operación conserva retardos enteros. La interpolación lineal de dos muestras implementa un FIR de primer orden. A media muestra su módulo es $|\cos(\omega/2)|$, con error de −3,01 dB en π/2 y un cero en Nyquist para un retardo ideal de módulo uno. Para señales limitadas en banda, un sinc desplazado y truncado permite ajustar el error con longitud y ventana. Requiere declarar el borde de banda, la latencia añadida y la tolerancia de módulo y fase. La entrada discreta por sí sola no determina el modelo entre muestras. Se reserva esa opción hasta definir y verificar dicho contrato. [Formulación y condiciones del retardo fraccionario](https://arxiv.org/abs/1308.0797).

Se agrupan trayectorias coherentes antes de aplicar el canal y de medir potencia. Esta decisión elimina la discrepancia entre un PDP por camino y el que se observa sobre un único tap del registro de salida. Para fading estocástico se distinguirá la potencia esperada por proceso de la potencia medida de la suma.

## Fronteras de integración

Se reutilizan las herramientas de Comunicaciones Digitales para las primeras operaciones, con ejecución Qt independiente. El enlace usará las mismas operaciones en una secuencia explícita. Los proyectos de Fase 03 y las corridas existentes serán oráculos de compatibilidad antes de extender esquemas. La distribución de los primeros candidatos usará la infraestructura de Phase 03 con manifiestos de prueba. Las claves de producción y las etiquetas se reservan para autorización separada.
