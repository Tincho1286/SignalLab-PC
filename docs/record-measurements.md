# Medir un registro: intervalo y distribución temporal

En **Señales → Energía y potencia → Medir un registro**, elegí el intervalo de la señal que querés estudiar. Podés medir su energía, separar el promedio de las variaciones y buscar cruces de un nivel. El informe, las figuras y la tabla corresponden al mismo intervalo.

## Seleccionar el intervalo

Elegí señal discreta o continua y cargá una fórmula, muestras, un archivo o un resultado. Desde y Hasta vacíos utilizan todo el registro. Los límites seleccionan puntos guardados y se incluyen ambos extremos. En discreto se ingresan índices enteros; en continuo se usan las coordenadas del eje y hacen falta al menos dos puntos. Si un límite continuo cae entre nodos, el informe identifica el primer y último punto efectivamente incluidos.

La energía discreta es Σ|x[n]|² y la potencia de la ventana es esa energía dividida por su cantidad de muestras. En continuo, energía y media integran el modelo lineal entre los puntos seleccionados. Las entradas que conservan retención ZOH se integran con ese modelo: el último punto no agrega duración. No se reevalúa la fórmula cargada ni se extrapola fuera del registro. Un impulso Dirac ideal no tiene energía cuadrática finita y no se mide como una muestra ordinaria.

## Leer la acumulada y el intervalo central

El selector de resultados permite abrir la fracción de energía acumulada en los nodos. Termina en 1 cuando hay energía positiva. Para un registro nulo, la normalización, el centro y la dispersión no están definidos.

El centro energético utiliza |x|² como peso; la dispersión RMS mide la distancia cuadrática al centro en la unidad del eje. El porcentaje central deja la mitad de la energía restante en cada cola. Por ejemplo, el 90 % central utiliza los cuantiles 5 % y 95 %. No busca el intervalo más corto posible. En discreto sus extremos son muestras y se puede incluir más energía del porcentaje solicitado.

En continuo, las medidas integran |x(t)|² del modelo lineal, que es un polinomio cuadrático dentro de cada segmento. Los cuantiles resuelven su integral cúbica. La acumulada exportada conserva valores en los nodos; una recta que los una sólo guía su lectura. Para x(t)=t en [0,1], la energía es 1/3, el centro es 3/4 y la fracción acumulada es t³.

## Separar continua y alterna

La componente continua es la media compleja sobre la ventana seleccionada. La alterna es el registro menos esa media. Se publican por separado para analizar, transformar o exportar. La potencia de la ventana se separa en potencia de la media y potencia alterna, salvo el redondeo numérico. No es una clasificación de toda una señal infinita.

Los cálculos reescalan los valores antes de obtener cuadrados. Si una energía queda fuera del rango float64 se conserva como texto científico; no se reemplaza por cero o infinito. La señal alterna no se publica si sus muestras no pueden representarse numéricamente. Los índices enteros se conservan; para centros con origen discreto muy grande, el informe puede mostrar el origen más un desplazamiento local para no esconder fracciones del índice.

## Localizar cruces y contactos

Elegí parte real, parte imaginaria o módulo y un nivel de amplitud. Cruces y contactos distingue ascensos, descensos, contactos, tramos iguales al nivel y coincidencias en los extremos del registro. En discreto, un cambio de lado se ubica en la primera muestra del nuevo lado, sin inventar un índice intermedio. En continuo se resuelve el segmento complejo: el módulo puede cruzar dos veces o tocar el nivel aunque sus extremos no lo hagan.

Una retención ZOH conserva sus saltos y los tramos constantes excluyen el extremo donde cambia su valor. No se inventa un cruce lineal durante el salto. La tabla se exporta completa a CSV con las unidades y el intervalo calculados. Editar una entrada deja disponible el resultado anterior hasta recalcular. El selector de resultados determina qué señal se abre, exporta o envía a otra herramienta; todas las salidas calculadas quedan también en Resultados.
