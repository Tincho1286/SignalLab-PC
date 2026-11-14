# Medir la respuesta de un sistema

Desde la **1.8.10 preliminar**, **Analizar sistema → Medidas de frecuencia** permite consultar el último resultado de H(s), H(z) o una respuesta definida como H(w). Las mediciones conservan esa definición y sus condiciones. Editar las entradas principales no cambia el sistema medido hasta volver a analizarlo.

El botón **Medir resultado** pertenece a esta pestaña. **Analizar sistema** continúa siendo la acción principal de la herramienta. El informe, la tabla y la figura describen una misma medición, que también queda registrada en Resultados.

## Leer frecuencias elegidas

Ingresá una lista de frecuencias reales separadas por comas. Se admiten expresiones como pi/4 y 10^(-2). Cada lectura evalúa la definición; no interpola los puntos dibujados. Puede consultar frecuencias fuera de la figura original si la definición y sus condiciones permiten evaluarlas.

La tabla muestra parte real, parte imaginaria, módulo, dB, ángulo principal y retardo de grupo. Un cero tiene módulo cero y −∞ dB, mientras que su fase y retardo quedan no definidos. Las condiciones excluidas y los valores fuera del rango numérico tampoco se sustituyen por cero.

## Buscar un nivel y observar sus tramos

Elegí **módulo absoluto**, expresado como amplitud positiva, o **dB relativos** al módulo en una frecuencia de referencia. Una caída de −3.0102999566 dB corresponde a 1/√2 de esa referencia, es decir, media potencia cuando corresponde interpretar |H|² como relación de potencias.

Desde/Hasta vacíos utilizan el intervalo del análisis. La búsqueda conserva puntos de ese análisis, agrega la rejilla solicitada y explora vecindades de polos de los modelos racionales. Refina cambios de signo y contactos locales con el nivel mediante nuevas evaluaciones de la definición.

El informe reúne los cruces aislados encontrados y los tramos observados por encima del nivel. Un tramo que toca el borde de la ventana tiene un ancho recortado: no se presenta como ancho de banda completo. Una tangencia, un tramo sobre el nivel o una discontinuidad requiere una interpretación diferente de un corte transversal.

La frecuencia refinada debe alcanzar el nivel dentro de la precisión de la búsqueda. Un salto entre dos valores que no lo alcanza se informa como candidato no resuelto. Cuando hay condiciones no válidas, tramos no aislados o candidatos pendientes, se conservan los cruces resueltos sin asignar anchos de banda a una partición incompleta.

## Comprobar bandas y tolerancias

Agregá una fila por intervalo exigido. **Desde/Hasta** son frecuencias angulares; **Mínimo |H| / Máximo |H|** son amplitudes lineales. Un límite vacío no impone esa restricción. Por ejemplo, una banda de paso puede tener ambos límites; una banda de rechazo puede tener sólo un máximo. Las transiciones pueden quedar fuera de las bandas comprobadas.

Los intervalos deben quedar dentro de la ventana del último análisis. Para observar otro rango, ampliá ese análisis primero. La tabla muestra los extremos de módulo refinados, sus frecuencias, los límites y el menor margen de amplitud. Un margen positivo deja holgura; uno negativo indica exceso. Los puntos no definidos y las búsquedas locales pendientes impiden declarar cumplimiento numérico.

La comprobación es numérica sobre rejilla, bordes, vecindades de polos y extremos refinados. Puede perder características entre puntos y no certifica toda la respuesta ni un orden mínimo. Permite examinar un filtro ya diseñado, importado o escrito como fórmula sin volver a diseñarlo.

## Consultar el retardo por banda

El informe muestra el menor y el mayor retardo observados, sus frecuencias, la mediana y la diferencia máximo−mínimo de los puntos válidos. Se expresa en **muestras** para H(z) y en **segundos** para H(s). No se define un retardo ordinario en ceros, polos o saltos; esos puntos se cuentan aparte.

Estas estadísticas describen el intervalo y los puntos evaluados. No prueban fase lineal para todo el sistema. Una pequeña variación puede reflejar el redondeo de la evaluación; el gráfico conserva los valores y dispone de controles de escala vertical.

## Relacionar la tabla con la figura

**Abrir gráfico**, en la cabecera de resultados, abre **Gráfico de medidas** en una ventana independiente. Azul representa la respuesta medida, ámbar los niveles o límites, verde los extremos refinados y violeta las coordenadas de la fila seleccionada. Las bandas separadas no se conectan a través de las transiciones.

El módulo puede verse en amplitud o dB sin repetir la medición. El retardo comparte el mismo eje de frecuencia. **Exportar medidas (CSV)** conserva todas las filas junto con las unidades, la definición y el criterio; el informe resume hasta veinte lecturas puntuales, pero la tabla y el archivo no recortan esa lista.
