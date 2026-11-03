# SignalLab PC 0.99.3 — transformaciones coherentes

28/10/2026. Se completa y uniforma Transformar una señal dentro del catálogo existente. Se mantienen 31 problemas y se pasa de 76 a 80 variantes, sin agregar entradas principales.

## Organización y carga

Desplazar, Invertir, Amplitud y Par e impar tienen las mismas opciones directas para registros discretos y continuos. La operación continua Transformación afín permanece para combinar A, a y t₀ en y(t)=A·x(a·(t−t₀)). Sus rutas anteriores siguen disponibles.

Todas comparten un panel con entrada independiente por fórmula/tramos, muestras, archivo o resultado; parámetros propios de la operación; resultado y original. Los parámetros se validan con el lector común de constantes: A admite reales/complejos, pi y potencias decimales; no admite una variable evaluada accidentalmente en cero. El desplazamiento discreto es entero; la escala temporal continua es real no nula.

Cada variante conserva su borrador. La copia de entrada entre operaciones del mismo dominio usa el mecanismo común y preserva la procedencia. Cambiar datos muestra que el resultado anterior necesita recalcularse. La señal original se dibuja al abrir su pestaña, evitando abrir otra figura en cada cálculo.

## Par e impar continuo

Se calculan x_e=(x+x_reflejada)/2 y x_o=(x−x_reflejada)/2, sin conjugación. La parte ordinaria se considera cero fuera del registro y se interpola linealmente sobre una rejilla simétrica que incluye cero. El paso final se basa en el de entrada y se ajusta al intervalo simétrico. Las dos componentes comparten eje y su suma recupera el registro interpolado sobre esa rejilla, salvo redondeo.

Los términos Dirac se reflejan y combinan por posición/peso, separados de la parte ordinaria. No se convierten en alturas de muestras. La descomposición es numérica de registro finito; no representa una solución simbólica universal de cualquier función infinita. Ambas salidas se registran y pueden exportarse o reutilizarse.

## Precisión y presentación

Desplazar, invertir y escalar ya no presentan la expresión original como si describiera los valores transformados. La conservan como procedencia; el informe muestra la relación aplicada. La descomposición discreta conserva el reloj con el nuevo índice inicial.

El promedio de componentes evita desbordes intermedios cuando el resultado cabe en doble precisión, sin eliminar valores subnormales representables. Las transformaciones temporales continuas conservan la regla Dirac A/|a| y describen el reloj del nuevo eje cuando está en segundos.

Las ayudas incluyen dibujos coloreados de la operación seleccionada, con la misma escala de amplitud y coordenadas entre paneles. Los informes muestran las relaciones matemáticas antes de los detalles del registro.

## Comprobación focalizada

Se comprobaron desplazamiento, inversión y amplitud discretos con reloj y expresión de procedencia; identidad de par/impar y valores finitos grandes/subnormales; simetría y reconstrucción continua sobre su rejilla; pesos Dirac; las rutas comunes, ambas salidas en biblioteca, copia de fuente, indicador de cambios, parámetros constantes y dibujo diferido del original. No se ejecutó una batería general ni una campaña de resoluciones.

La entrega conserva la estética y la escala estable previas. Sigue siendo de desarrollo y no declara concluido el objetivo de 1.0.
