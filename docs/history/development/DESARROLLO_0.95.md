# SignalLab PC 0.95 — multiplicación de señales y FIR desde h[n]

28/10/2026. Se agregan las dos capacidades de enventanado solicitadas. Se conserva la organización por problema: 32 familias y 76 variantes públicas.

## Multiplicar señales

Señales → Multiplicar señales. Las dos entradas son independientes y admiten fórmula/tramos, muestras, archivo o un resultado anterior. El dominio discreto/continuo se elige dentro de la herramienta.

La salida y[n]=x[n]·w[n] conserva los índices y el intervalo de la primera señal. La segunda se alinea por n y vale cero fuera de su registro. No es convolución, no se conjugan valores ni se normaliza el producto. Si ambas entradas registran una tasa de muestreo y tiempo físico, se exige compatibilidad de sus relojes.

Para registros continuos, el producto se evalúa en los instantes de la primera entrada; la segunda se interpola linealmente, con cero fuera del intervalo. El resultado es una aproximación entre muestras. No se ignoran términos Dirac ideales: esos productos requieren otro tratamiento.

La salida se guarda en la biblioteca, puede exportarse y enviarse a otras herramientas. Las expresiones de n/t de la biblioteca también ofrecen este destino.

## FIR desde h[n] propia

Diseño de filtros → Diseñar filtro → FIR → Digital → Definir por → h[n] propia. La opción Cortes y longitud se mantiene para las formas predefinidas.

La entrada h[n] admite fórmula/tramos, muestras, archivo o un resultado. Se aplica una ventana estándar simétrica (Hamming, Hann, Blackman, Kaiser con β, Bartlett o rectangular), de longitud igual al registro cargado, o una señal w[n] propia alineada por índices. Admite h compleja y registros cortos. El resultado no normaliza automáticamente la ganancia; puede enviarse al ajuste de ganancia existente.

Si el registro empieza antes de cero, la casilla Retardar si empieza antes de n=0 agrega D=−n₀ muestras y lleva el inicio a cero. Considera el inicio del registro, incluidos ceros iniciales; no busca el menor retardo posible. Desactivarla conserva los índices negativos y permite obtener una transferencia con avances. Un origen ya positivo se conserva. Se mantienen los datos de reloj al desplazar una señal muestreada. El informe muestra n₀, longitud, D y las relaciones h_w[n]=h[n]·w[n] y h_F[n]=h_w[n−D]. El retardo cambia la fase y el retardo de grupo, pero no el módulo.

El documento ofrece módulo, fase y retardo de grupo; h[n], w[n] y el producto; e informe matemático. Las figuras siguen el mecanismo de ventanas externas. Los resultados intermedios y la transferencia quedan en la biblioteca para analizar o reutilizar. Un rango de frecuencia inválido no impide generar el FIR: se muestra el problema y puede corregirse el rango posteriormente.

La biblioteca de ayuda incorpora explicaciones y un esquema coloreado de multiplicación índice por índice. Se corrige una inicialización del selector de ilustraciones que podía impedir generar algunas ayudas generales. La limpieza de una respuesta pendiente ya no vuelve a interpretar un rango inválido.

## Comprobación acotada

Se comprobó el producto discreto con orígenes diferentes y extensión por cero, el producto continuo con interpolación, y una Hann aplicada a h de origen negativo. La transferencia se contrastó con la suma directa de sus muestras tanto conservando índices negativos como agregando retardo. Un recorrido breve confirmó las dos rutas, ventana estándar y propia, respuesta en frecuencia y registro de salidas en biblioteca. No se ejecutó una batería general ni una campaña de resoluciones; la evaluación general de uso queda pendiente.

La versión es de desarrollo y no declara finalizados los pendientes de la primera estable.
