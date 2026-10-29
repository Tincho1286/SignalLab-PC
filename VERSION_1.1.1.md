# SignalLab PC 1.1.1 · ecuaciones en diferencias

La herramienta Ecuaciones lineales reúne ahora Continuo · diferencial y Discreto · diferencias. Se conserva el cálculo diferencial existente y se agrega su equivalente discreto de coeficientes constantes.

## Carga y resultados

- Convención: a₀y[n]+a₁y[n−1]+…+aₚy[n−p]=f[n]. a₀ debe ser no nulo; los coeficientes admiten fracciones, pi y 10^(-3).
- Entrada f[n] como fórmula o por tramos, con polinomios, exponenciales, senoidales, escalones e impulsos discretos.
- Primer índice n₀ y reposo opcional. Sin reposo se cargan los valores anteriores desde el más cercano: y[n₀−1], y[n₀−2], …, y[n₀−p]. No se confunden con y[n₀], que se calcula.
- Solución legible en n y separación en entrada cero y estado cero. La cantidad de muestras sólo controla la tabla y el gráfico, sin truncar la fórmula.
- Transferencia H(z) desde f[n] con condiciones iniciales nulas, guardada por separado de la solución y[n]. Ambas expresiones pueden reutilizarse en CAS y destinos compatibles; las muestras se guardan como una secuencia discreta independiente.
- Ayuda con parámetros explicados y diagrama de colores sobre los índices, historial y salida calculada. Gráficos discretos mediante tallos y figuras independientes.

## Método y alcance

Se usan la Z unilateral, la superposición y propiedades racionales. La inversión de X(z)/z con desplazamiento de un índice evita introducir deltas y tramos artificiales en exponenciales simples. Los escalones y tramos conservan sus límites; la solución sólo se aplica desde n₀, sin suponer una historia infinita anterior. La fuente f[n] mantiene su índice global cuando cambia n₀.

Para entradas que no se reducen a la familia polinómico-exponencial, se conserva una solución exacta como suma finita de convolución y se declara que no se obtuvo forma cerrada. Los parámetros sin asignar impiden producir muestras, pero no obligan a perder la expresión. Si la recurrencia numérica desborda dentro de la ventana, se conserva la fórmula y se informa por qué no se muestran esas muestras.

La resolución simbólica se ejecuta en un proceso separado y se puede cancelar. No se introducen evaluaciones de código Python del usuario. La ecuación requiere coeficientes constantes; no resuelve sistemas de recurrencias ni coeficientes variables en esta primera implementación.

## Evidencia dirigida

Se contrastaron fórmulas con la recurrencia numérica para primer y segundo orden, polos repetidos, resonancia exponencial, senoide, impulso retardado, tramos, distintos índices iniciales y coeficientes con pi y potencias negativas de diez. También se revisó la convolución finita cuando no hay forma cerrada, que cambiar N no cambie la fórmula, el desborde de muestras, el proceso simbólico, el panel real, el informe matemático y la ayuda. No se ejecutó una batería general.

La navegación mantiene 30 problemas, ahora con 83 variantes, más CAS. La ampliación de Señales Aleatorias de 1.1.0 permanece disponible.
