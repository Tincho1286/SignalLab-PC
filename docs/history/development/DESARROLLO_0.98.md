# SignalLab PC 0.98 — suma y producto coherentes

28/10/2026. Se reúnen Suma y Producto en Señales → Sumar o multiplicar señales. Cada operación conserva sus rutas y nombres de búsqueda; la elección se hace dentro del documento. El catálogo pasa de 32 a 31 problemas, con las mismas 76 variantes públicas.

## Carga de las señales

Las dos operaciones admiten señales discretas o continuas. Se muestran dos pestañas de entrada en lugar de apilar dos formularios largos. Cada fuente conserva fórmula/tramos, muestras, archivo o resultado anterior, y su propio eje. Una señal recibida se muestra en su pestaña correspondiente.

Cada operación conserva su borrador y resultado al regresar. Al abrir una operación por primera vez puede copiar ambas entradas y el dominio desde la otra; si ya había un borrador, Copiar entrada permite reemplazarlo explícitamente. La procedencia de una fórmula recibida de Resultados se conserva al copiarla. La suma continua también se ofrece desde señales y expresiones de la biblioteca.

## Suma

La suma discreta alinea por n entero y cubre la unión de ambos registros, incluidos sus huecos con cero. Se validan las tasas y los orígenes físicos registrados; el reloj conocido se propaga al nuevo inicio. No se cambian las tasas automáticamente.

La suma continua cubre ambos intervalos. Las partes ordinarias se interpolan linealmente con extensión por cero fuera de sus datos. Se construye una rejilla uniforme con resolución basada en el menor paso de entrada, ajustando el paso para incluir ambos extremos. Ese paso final queda en el resultado. El orden de las entradas no cambia la rejilla o el resultado, salvo redondeo numérico. Entre muestras sigue siendo una aproximación; no se recupera información ausente en los datos.

Los impulsos Dirac se suman mediante sus posiciones y pesos, separados de las muestras ordinarias. Se combinan los términos coincidentes y se mantienen términos pequeños; no se convierten impulsos ideales en alturas finitas. Un ajuste acotado a errores submuestra de redondeo evita perder el extremo de un registro durante la interpolación.

## Producto

Conserva el comportamiento anterior: producto punto a punto sobre el intervalo de la primera señal, con cero fuera de la segunda. En continuo se interpola la segunda sobre los instantes de la primera. No se conjuga, convoluciona ni normaliza el resultado. Los productos generales de Dirac siguen requiriendo otro tratamiento. La elección independiente de L para un FIR permanece en Diseñar filtro → FIR → h[n] propia.

## Presentación y ayuda

La diferencia entre el intervalo de la suma y el del producto aparece junto a las entradas y en los informes. La ayuda de suma incluye un esquema coloreado con la misma escala de amplitud en los tres paneles. Las salidas se guardan en Resultados y pueden exportarse o enviarse a otras herramientas.

## Comprobación focalizada

Se comprobó suma discreta compleja con registros separados, reloj conservado y rechazo de tasas incompatibles; suma continua con diferentes intervalos/pasos, conmutatividad y extremo de una rejilla no coincidente; y pesos Dirac. Un recorrido breve comprobó el documento común, la copia de ambas fuentes al cambiar de dominio/operación, el producto anterior, el retorno al borrador de suma y su registro en biblioteca. No se ejecutó una batería general ni una campaña de resoluciones.

Esta compilación de desarrollo no declara terminado el objetivo de 1.0.
