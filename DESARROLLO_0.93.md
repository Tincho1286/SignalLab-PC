# SignalLab PC 0.93 — DTFT inversa

28/10/2026. Se incorpora la operación que faltaba dentro de Transformada de Fourier → Discreta → DTFT inversa. Incluye las variantes Numérico y Algebraico, sin agregar otra familia al explorador: 31 problemas y 74 variantes.

## Cálculo numérico

Entrada independiente mediante fórmula/tramos, muestras, archivo o espectro de Resultados. Se usa x[n]=(1/2π)∫ X(ω)exp(iωn)dω en un período de 2π, con frecuencias en rad/muestra e índices de salida enteros, positivos o negativos.

Para una fórmula se eligen inicio del período y cantidad de frecuencias; el paso se ajusta automáticamente para incluir ambos extremos. En listas y archivos se acepta un período con ambos extremos o sin repetir el final. Una banda parcial, unidades rad/s/Hz o una rejilla incompatible se rechazan con explicación.

La suma periódica se evalúa mediante FFT inversa, con normalización de la integral y el factor de fase correspondiente al inicio real del período. Cuando ambos extremos están incluidos, comparten peso 1/2. Se conservan valores complejos y ruido de redondeo, sin recortar muestras pequeñas a cero. La ayuda distingue esta aproximación a la integral de la DFT inversa de un bloque.

La salida pedida es un tramo de x[n]. La cantidad de frecuencias independientes determina una separación de aliasing temporal, con posible factor de fase según el origen de frecuencia. Pedir más índices no aporta información espectral adicional. El informe explicita esta limitación; no se declara una inversión exacta universal a partir de muestras finitas.

## Cálculo algebraico

Para expresiones racionales en exp(iω), se construye X(z) y se aplica la inversa Z con la ROC que contiene |z|=1. Esto permite obtener términos derechos, izquierdos o bilaterales sin imponer causalidad. Se conservan las propiedades de desplazamiento, polos repetidos y notación legible de secuencias del motor existente.

Para otros casos se integra simbólicamente de −π a π. Una banda ideal por tramos produce la expresión de sinc con su valor especial en n=0. Si el motor deja una integral sin evaluar, se informa como pendiente; los parámetros necesitan valores antes de generar muestras. No se implementa aquí un tratamiento general de polos en el círculo unidad mediante distribuciones o valor principal.

La expresión y sus muestras se registran por separado en Resultados. El gráfico de salida es discreto, con tallos e índices enteros. Las vistas numérica/algebraica pueden copiar una fórmula compatible al abrirse por primera vez y conservan sus borradores al regresar.

## Uso y ayuda

Las expresiones de DTFT de la biblioteca ofrecen las dos inversas; los espectros en rad/muestra permiten abrir la variante numérica. La ayuda contiene un esquema coloreado del período de X(ω) y de los índices de salida. Buscar una operación específica abre la variante encontrada dentro de su familia. El informe usa la pestaña existente, sin añadir otra pestaña duplicada.

Se ajusta la escritura de condiciones booleanas por tramos a operadores matemáticos compatibles con el lector de expresiones, permitiendo evaluar el caso n=0 de la banda ideal. Las vistas previas de listas extensas del registro común se limitan explícitamente a ocho entradas; los datos completos se conservan y exportan.

## Comprobación focalizada

Se comprobaron una ida/vuelta numérica con secuencia compleja de origen negativo y los dos tipos de período; una inversa racional causal y otra izquierda; y una banda ideal con su muestra central. Un recorrido breve comprobó las dos variantes, el paso automático, muestras enteras, registro en biblioteca y ayuda ilustrada. No se ejecutó la batería general ni una campaña por todas las resoluciones, según el pedido del usuario.

Esta capacidad no cierra por sí sola los pendientes generales de la primera estable. La revisión de uso queda a cargo del usuario.
