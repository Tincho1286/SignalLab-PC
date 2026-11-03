# SignalLab PC 0.96 — longitud de ventana y ejes de estados

28/10/2026. Se corrige la limitación de enventanado de referencia y se integra la mejora de entradas de espacio de estados que estaba en preparación. Se conservan 32 problemas y 76 variantes; no se agregan menús principales.

## Ventana con longitud independiente

Diseñar filtro → FIR → h[n] propia permite elegir la longitud L de una ventana estándar y su ubicación, independientemente del tamaño del registro de h[n]. L es la cantidad total de muestras; M=L−1 se muestra como orden nominal. El orden efectivo puede diferir por extremos nulos o desplazamientos.

Centrada coloca la ventana sobre n=0 para una fórmula, o sobre el centro del registro para muestras/archivo/resultado. Cuando no existe un centro entero compatible con la longitud elegida, se toma el primer índice inferior: para una fórmula y L par el centro queda en −1/2. Desde un índice elegido permite indicar n_w directamente. La ayuda explica los dos casos y el informe muestra el intervalo exacto n_w…n_w+L−1.

Si h[n] es una fórmula o tramos, se evalúa directamente en los índices de la ventana. Sus antiguos campos de inicio/cantidad se ocultan para evitar dos controles del mismo intervalo. Si h es un registro finito, se toman sus muestras en el soporte de la ventana y se usa cero donde no hay datos. Una ventana propia define su longitud y origen mediante sus datos. La salida contiene L muestras, no el registro completo de h rellenado con ceros. Las fórmulas no se desplazan automáticamente para imponer otra simetría.

Se conserva el retardo opcional para llevar a cero un origen negativo, con actualización del reloj si existe. No se normaliza automáticamente la ganancia. Intermedios y transferencia quedan en Resultados; se conserva el acceso a módulo, fase y retardo de grupo.

## Simulación de estados

Se reemplazan la expresión separada por punto y coma y los botones de copiar/restablecer por una entrada local para cada canal. Una sola queda visible a la vez; el selector aparece cuando el modelo tiene más de una entrada. Cada canal admite fórmula/tramos, muestras, archivo o resultado. Los borradores se conservan al cambiar canal o dominio durante la sesión.

Se corrige la evaluación de las fórmulas discretas: ahora usan índices enteros n, en lugar de nT. Salidas y estados conservan el primer índice de las entradas; las figuras usan tallos y el cursor/marcas de muestra. Los canales requieren igual cantidad y origen, y en continuo también igual paso en segundos. Los relojes registrados deben ser compatibles con el período del modelo discreto. No se recortan ni remuestrean canales automáticamente.

El estado inicial corresponde al comienzo del registro, incluso con un origen negativo o distinto de cero. Se usa el lector común de constantes, que admite pi, potencias, notación científica, fracciones y complejos. En continuo se mantiene la propagación por exponencial matricial con entrada ZOH. Entradas, estados, salidas y datos del cálculo se guardan en la biblioteca; las señales pueden enviarse directamente a esta herramienta desde otras.

Se agrega el indicador de datos modificados a las variantes de espacio de estados. Los resultados anteriores permanecen disponibles hasta recalcular.

## Frecuencia de estados

La respuesta continua usa Ω en rad/s; la discreta usa ω en rad/muestra, como H(z). La interfaz convierte ω/T al llamar al motor existente, cuya respuesta digital evalúa exp(iΩT). Gráficos, registros y exportaciones usan las mismas unidades. Los rangos de ambos dominios conservan sus borradores al alternar.

## Comprobación puntual

Se contrastó una ventana más corta que h y una más larga con extensión por cero, incluyendo la transferencia frente a la suma directa. Un recorrido breve confirmó que una fórmula usa L=7 y que un registro de 101 muestras produce 11 con L=11. En estados se comprobó una recurrencia MIMO con origen negativo, una entrada n, otra constante con potencia decimal, estado inicial pi, rechazo de reloj incompatible, un integrador continuo ZOH y la frecuencia digital frente a su expresión analítica. No se ejecutó la batería general ni recorridos por todas las resoluciones. La revisión general de uso permanece abierta.

Esta compilación no declara terminado el objetivo de la primera estable.
