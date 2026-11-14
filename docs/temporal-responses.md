# Respuesta temporal: ventana, comparación y transitorio

Estas ampliaciones corresponden a la **1.8.9 preliminar** y se integran en **Sistemas LTI → Respuesta temporal**. La herramienta conserva sus entradas locales: una transferencia H(s) o H(z) y la excitación elegida. Se pueden importar definiciones anteriores sin depender de otro cálculo abierto.

## Elegir la ventana

| Entrada | Intervalo calculado |
| --- | --- |
| Impulso o escalón discreto | N muestras, desde n=0 hasta n=N−1. |
| Impulso o escalón continuo | N puntos entre t=0 y la duración indicada, incluidos ambos extremos. |
| Entrada propia | Su origen, paso y puntos, más los ceros que se indiquen en la extensión. |

**Sugerir intervalo desde los polos** prepara los campos y deja la simulación pendiente de Calcular respuesta. Para modos estables utiliza una caída modal orientativa a 10⁻³; también tiene en cuenta escalas rápidas al proponer los puntos continuos. Los polos repetidos, los residuos y las cancelaciones pueden modificar el transitorio observado, por lo que la sugerencia no certifica una banda de establecimiento.

Con historial discreto no nulo se conservan los modos de la ecuación original, aunque se cancelen en H. Para modos crecientes se propone observar su crecimiento durante una ventana acotada; no se les atribuye un establecimiento. No se recorta silenciosamente una sugerencia que excede los recursos disponibles: los campos manuales siguen disponibles.

## Observar la cola de una entrada propia

**Extender entrada con ceros** agrega una cantidad entera de puntos, conservando origen y paso. Cero mantiene el registro cargado. La fórmula no se vuelve a evaluar fuera de ese registro, y el historial inicial sigue referido a su primer índice.

En continuo, los puntos se reconstruyen con la interpolación elegida. Lineal forma un segmento entre cada par; retención mantiene el valor hasta el punto siguiente. El tramo hacia el primer cero agregado utiliza esa misma regla. Agregar ceros no impone una desconexión instantánea entre dos puntos ni equivale a continuar la función original.

Se exportan y reutilizan los puntos de la entrada usada, con su eje y el método registrado. Cada herramienta de destino define cómo trabaja entre esos puntos; si volvés a simularlos, elegí la misma interpolación para conservar ese modelo. Cuando había un modelo o una fórmula original, también se conserva como resultado padre. La reconstrucción no recibe esa fórmula como si fuese exacta entre puntos. Los Dirac se tratan por posición y peso, separados de las muestras ordinarias.

## Comparar entrada, salida y memoria

**Comparación** utiliza un eje común para la salida y la entrada. Con historial discreto también permite superponer estado cero y entrada cero. Las casillas modifican la vista y no vuelven a simular. La retención de entrada se dibuja como escalones; la salida calculada no hereda ese estilo.

El resultado conserva cada señal por separado, con sus acciones de exportación, CAS y reutilización. La comparación usa esas mismas salidas. En gráficos discretos se leen índices enteros; el período T sólo agrega su relación con segundos y no cambia las fórmulas en n ni la frecuencia digital en rad/muestra.

## Medir un escalón

**Medidas** corresponde al escalón unitario desde reposo con un modelo causal estable. La referencia es su ganancia DC: H(0) en continuo o H(1) en discreto. La última muestra del registro se informa aparte y no se toma como valor final.

Los cruces del 10 % y 90 % determinan la subida. El sobreimpulso se mide en la dirección del valor final, lo que permite interpretar ganancias negativas. La banda de establecimiento utiliza el porcentaje indicado respecto de la magnitud de esa referencia.

El establecimiento es **observado**: se busca la entrada en banda después de la cual los puntos restantes del registro permanecen dentro de ella. Esto no demuestra qué ocurre en todos los instantes posteriores a la ventana. Una simulación corta puede no mostrar los cruces o la permanencia en banda; en ese caso no se reemplazan por el final del registro.

En discreto se informan muestras enteras. Si existe un reloj, también se muestran duraciones en segundos. En continuo los cruces y la entrada en banda se aproximan por interpolación lineal entre puntos calculados. Las respuestas complejas, modelos inestables y referencias DC nulas explican las medidas relativas que no están definidas. Un problema en esta medición auxiliar conserva la respuesta temporal ya calculada.

## Leer los aportes de una muestra discreta

**Paso a paso** prepara su inspector al abrirse. Elegí n y, en una cascada, la sección correspondiente. Aportes muestra el coeficiente, el divisor a₀, la muestra utilizada, el producto y si procede del historial o del registro calculado.

La suma se reconstruye como racionales de los valores binarios almacenados y se compara con la salida de la realización. Las diferencias muestran el efecto del redondeo; no convierten la reconstrucción en una solución simbólica exacta del problema original. Un aporte fuera del rango float64 se identifica, en lugar de reemplazarlo por cero.

El inspector conserva el último cálculo aunque cambie el formulario. Se prepara en segundo plano y no duplica sus arreglos intermedios en Resultados: las entradas y salidas originales ya están registradas. La tabla de la muestra elegida se puede exportar a CSV.

Cuando se especifica un historial global de entradas y salidas para un filtro SOS, la simulación utiliza la ecuación polinómica correspondiente. Eso no equivale a especificar sus estados internos por sección y puede perder precisión en órdenes altos. La comparación y el inspector conservan la realización efectivamente utilizada.
