# Comparación e inspección interactiva de resultados

[← Desarrollo](development/README.md)

Estas funciones corresponden a la versión **1.8.1**. Se integran en las herramientas existentes y utilizan sus resultados y acciones de exportación. La entrega 1.8.0 conserva sus archivos originales y no incluye estas incorporaciones.

## Comparación de diseños FIR

En el diseño por bandas y tolerancias, **Cálculo** permite elegir entre un diseño individual y dos comparaciones. **Mismas tolerancias** busca para cada ventana su primera longitud que supera la comprobación numérica. **Igual longitud** aplica a todas el mismo número de coeficientes L y muestra cuáles cumplen las restricciones.

Las ventanas disponibles son Kaiser, Hann, Hamming, Blackman, Bartlett y rectangular. Kaiser obtiene β de las tolerancias solicitadas. En un FIR simétrico, una longitud par corresponde a tipo II y tiene un cero en π; por eso se requiere longitud impar cuando las especificaciones piden paso no nulo en esa frecuencia.

La pestaña **Comparación** presenta longitud L, orden nominal M=L−1, tipo I/II, retardo, desvío máximo del paso, máximo en rechazo, cumplimiento y tiempo de cálculo. El informe detalla los mínimos y máximos de cada banda y sus frecuencias. Los desvíos están en amplitud lineal y el retardo en muestras.

Seleccioná una fila o utilizá el selector de resultados para elegir el filtro que analizarás, exportarás o reutilizarás. La figura puede superponer los filtros sobre las mismas frecuencias; la exportación del sistema toma el elegido. El CSV de comparación conserva las medidas y los intentos sin diseño, con su motivo. Seleccionar una fila fallida no habilita las acciones de un filtro anterior.

La comprobación utiliza rejillas, bordes y refinamiento numérico de extremos. Una búsqueda satisfactoria no demuestra un orden mínimo analítico ni certifica todos los puntos entre frecuencias evaluadas. Las bandas de transición no forman parte de las tolerancias de paso y rechazo.

## Selección visual de la región de convergencia

En Z o Laplace inversa, **Explorar ROC…** abre una ventana con los polos y las regiones abiertas. Podés seleccionar una región mediante un clic o desde la lista. **Aplicar ROC** actualiza los campos sin recalcular; **Aplicar y calcular inversa** utiliza esa elección para obtener la respuesta.

En Z, la elección distingue radios menores que los polos, anillos intermedios y la región exterior. La inclusión de cero o infinito depende del soporte y se consulta en el informe de la inversa. Si no hay polos finitos, el selector no inventa regiones adicionales.

En Laplace, la elección distingue semiplanos y franjas por las partes reales de los polos. Aplicar una región utiliza interpretación bilateral; un mismo X(s) puede representar señales con soportes distintos. El selector admite expresiones racionales numéricas y un retardo global `exp(-d*s)`.

Los polos se obtienen después de cancelaciones exactas. Las fronteras no pertenecen a las regiones abiertas y no se fusionan por proximidad numérica. Si dos bordes no se distinguen en la escala del gráfico pero sí en la precisión del cálculo, se utiliza la lista. La selección se rechaza si se editó la expresión después de abrir la ventana. Los campos habituales permanecen disponibles para definiciones que el selector no puede representar.

## Inspector de ecuaciones en diferencias

Después de resolver una ecuación con muestras numéricas, abrí **Paso a paso**. El índice n permite consultar cualquier muestra del intervalo calculado y los botones avanzan o retroceden una posición.

El inspector utiliza la ecuación normalizada:

```text
y[n] = f[n]/a₀ − Σ(aₖ/a₀) · y[n−k]
```

La tabla muestra cada coeficiente, la muestra anterior y su contribución. Distingue las condiciones iniciales de los valores calculados desde n₀. También muestra la suma de aportes, la salida almacenada y su diferencia numérica.

La navegación no vuelve a evaluar la entrada ni resuelve otra vez la ecuación: utiliza el historial, los coeficientes y las muestras del último cálculo. Por eso, si cambiás la fórmula del formulario, el inspector sigue describiendo el resultado anterior hasta recalcular. Las ecuaciones sin memoria muestran solo el término de entrada y las definiciones con parámetros pendientes conservan la fórmula aunque todavía no tengan un inspector numérico.

La diferencia entre los aportes y la muestra almacenada permite consultar el redondeo de esa iteración. No sustituye la comprobación simbólica de la solución ni certifica una identidad para todos los índices.

## Productos de la convolución discreta

En **Convolución lineal**, calculá las dos entradas y abrí **Paso a paso**. El campo n permite elegir una muestra del intervalo de salida; los botones avanzan o retroceden una posición. **Explicación** muestra la suma completa y la salida almacenada, y **Productos** detalla k, n−k, x[k], h[n−k] y su producto.

La tabla muestra hasta cien productos por página. Los botones de productos cambian la página sin cambiar n. **Alineación**, disponible desde **Abrir gráfico** en la cabecera de resultados, muestra esa misma página mediante tallos: arriba se comparan x[k] y h[n−k], y abajo se muestran los productos. El selector dentro de la figura permite consultar parte real, parte imaginaria o módulo.

La convolución multiplica sin conjugar h y usa cero fuera de ambos soportes. La suma incluye todos los productos, incluso si la tabla muestra sólo una página. El inspector conserva copias de las entradas y la salida del último cálculo, para que editar las fuentes no cambie la explicación. Una diferencia de redondeo entre la suma directa y la salida calculada por FFT no modifica el resultado original.

## Medidas espectrales de las ventanas

**Generar ventanas** conserva sus muestras simétricas y agrega las propiedades espectrales al informe. La ganancia coherente es Σw/L; el ancho equivalente de ruido en bins es L·Σ|w|²/|Σw|². Para expresarlo en rad/muestra se multiplica ese ancho en bins por 2π/L. Los bins se refieren a una DFT de L puntos: agregar ceros a una FFT no cambia esta medida.

El ancho completo de media potencia se obtiene entre −ω₃dB y +ω₃dB, donde |W(ω₃dB)|/|W(0)|=1/√2. Su referencia en amplitud es −3.0103 dB. No es el ancho entre los primeros ceros ni una estimación de la transición de un filtro.

En **Abrir gráfico**, elegí **Espectro de la ventana**. La figura utiliza ω en rad/muestra y permite alternar módulo relativo lineal o dB desde su propia barra. Las muestras de la ventana no se normalizan por cambiar esa vista, y se pueden seguir enviando a Fourier, Z o producto de señales. Una ventana nula no tiene ancho equivalente definido; si no se encuentra un cruce de media potencia entre 0 y π, el informe lo indica.
