# SignalLab PC 0.65 — organización de filtros y transformadas

## Un documento de filtros
La navegación pública reúne definición/análisis, diseño, conversión y respuesta temporal. Se conservan las opciones especializadas dentro del documento y sus datos independientes. Las rutas anteriores se resuelven internamente para mantener exportación y reutilización; ya no aparecen como herramientas duplicadas en el explorador. Se retira el lugar de raíces por barrido de K. Conectar sistemas conserva su herramienta propia.

Definir H por fórmula o coeficientes ahora muestra módulo, fase y retardo de grupo. Hay exportación y envío directo a respuesta temporal, conversión y polos/ceros. El análisis preserva las secciones de filtros importados y evita refactorizaciones algebraicas costosas de sus coeficientes numéricos.

Las fórmulas racionales admiten s, z y z^(-1), pi, fracciones y complejos. Se admiten potencias positivas y negativas de z. Si hay un avance temporal neto, se analiza su respuesta exacta y su retardo, pero no se publica silenciosamente como filtro causal. Una expresión racional no determina la ROC ni la estabilidad interna de una realización cancelada.

## Diseño y conversión
El plano de polos y ceros permite alternar binómica/polar sin alterar el diseño. La edición con mouse y los pares conjugados funcionan en ambas vistas. Los ángulos se muestran en radianes; las raíces reales positivas y negativas son admisibles.

La conversión de una respuesta analógica ideal produce un FIR mediante inversión numérica, truncación, ventana y desplazamiento causal. Se eligen longitud impar y ventana Hamming, Hann, Blackman, Kaiser o rectangular. Se conserva la respuesta ideal como referencia. El desplazamiento agrega (L−1)/2 muestras de retardo; la ventana/truncación modifican la respuesta. La conversión racional clásica por bilineal/invarianza sigue disponible: un IIR obtenido por bilineal no necesita una ventana FIR.

Módulo, fase y retardo aparecen en la vista predeterminada de los filtros racionales, incluidos FIR/IIR y conversiones. El retardo se calcula analíticamente a partir de H; en respuestas ideales muestreadas se identifica como aproximación por diferencias de fase y no se dibuja donde falta una fase válida.

## Laplace y Z
Laplace tiene directa/inversa por expresión en una sola herramienta (unilateral/causal, alcance informado). Z permite directa algebraica de x[n] con soporte entero finito o infinito, directa de muestras finitas e inversa racional algebraica con soporte derecho, izquierdo o ROC elegida por radio. Se publican la expresión y, cuando es posible, sus muestras por separado.

Las condiciones de convergencia mantienen |z| en el plano complejo. Se evita simplificar una condición radial como si z fuera real. La inversa usa expansión por polos y sus multiplicidades; admite términos finitos de avance/retardo. Si el motor no resuelve una suma o los polos requeridos, se informa y no se certifica una respuesta incompleta. No se promete una inversa general de toda función trascendente de z.

## Evidencia dirigida
Sintaxis; Z geométrica con ROC radial; inversas derechas/izquierdas, polo repetido y términos finitos en índices negativos; equivalencia de fórmulas en z y z^-1; FIR con ventana y retardo añadido; navegación unificada; vista polar tras calcular; envío de filtro a análisis; conversión ideal desde el panel a análisis; inversa Z y apertura de ayuda. No se repitió una campaña general del portable ni se certificaron todas las expresiones simbólicas posibles.

La aplicación sigue en preparación de 1.0; la reorganización no sustituye el cierre de exactitud y alcance documentado en CIERRE_1.0.md.
