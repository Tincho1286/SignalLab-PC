# SignalLab PC 0.99.7 · conversión, cortes y plano s

La herramienta Convertir analógico/digital incorpora un informe matemático con la definición de entrada, el período T, la relación entre s y z, las frecuencias de referencia mapeadas y la transferencia resultante. No se amplía el catálogo ni se crea otra herramienta para cada método.

## Corte mapeado y corte medido

El campo opcional Ωc de referencia acepta uno o varios valores positivos en rad/s, con pi y notación decimal. No modifica ni predeforma el filtro. Para transferencias racionales, dejarlo vacío busca cruces analógicos de media potencia respecto de una ganancia de referencia. Esta toma el máximo de una rejilla adaptativa e incluye el límite analógico conocido en infinito cuando es mayor. No es una prueba del máximo global ni de todos los cruces.

Bilineal muestra s=(2/T)(z−1)/(z+1), z=(1+sT/2)/(1−sT/2), ω=2 atan(ΩT/2) y su relación inversa. Invarianza muestra h[n]=T·ha(nT) y z=exp(sT), aclarando que el exponencial mapea polos y no sustituye toda H. Las referencias se presentan en rad/muestra, con ΩT sin plegar y el representante principal cuando hay aliasing.

Cada transferencia resultante muestra también los cruces de |H|=referencia/√2, equivalentes a −3.0103 dB respecto de esa referencia, la referencia usada y el intervalo evaluado. Este criterio no se confunde con un borde arbitrario de una especificación de diseño. En invarianza, el corte medido puede diferir del mapeado por las réplicas espectrales. Los cruces se refinan numéricamente; una rejilla finita puede omitir detalles estrechos.

El informe incluye H(s) y H(z) calculadas. Para expresiones largas utiliza la representación finita y los coeficientes completos. La conversión de respuestas ideales mantiene el informe del FIR aproximado y su ventana, y permite indicar referencias Ωc; no se presenta ese FIR como un ideal exacto. Los métodos inversos conservan sus ecuaciones, fórmulas de candidatos y alcance de ramas.

## Módulo lineal o dB

Conversión usa un selector de módulo independiente de la vista: módulo/fase/retardo, sólo módulo o retardo. Se agrega el mismo control lineal/dB a la barra de la ventana del gráfico. Los controles están sincronizados y se conserva el intervalo ampliado al cambiar la escala. Los filtros calculados no se rediseñan por esa presentación.

## Plano de polos y ceros

El análisis binómico fija límites con margen en ambas direcciones y conserva igual escala física. Incluir el origen y el círculo unidad cuando corresponde evita que todas las raíces reales o imaginarias produzcan una franja casi sin área. Se aplica a la consulta de raíces y a la vista de sistemas existente. No se mueven raíces ni se modifican multiplicidades.

## Evidencia puntual

Para H(s)=1/(s+1), T=1, se comprobaron el corte bilineal 2 atan(1/2) y el corte de invarianza relativo a DC 2 asin(sinh(1/2)). El informe distingue ΩcT=1 del segundo resultado. Se recorrieron informe y fórmulas, control lineal/dB de la figura con zoom conservado y plano s de un polo real, verificando una región cuadrada utilizable. Se revisó visualmente el encuadre y la ayuda de mapeo. No se ejecutó una batería general ni una campaña del portable.

La entrega sigue en desarrollo hacia 1.0. La ampliación de carga continua por pesos Dirac, preparada en otra carpeta de trabajo, no está incluida en este ejecutable.
