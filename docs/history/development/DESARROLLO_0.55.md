# SignalLab 0.55 · Sistemas I y II

Se conserva la corrección del lector de coeficientes: pi, 2*pi, 10^(-3), 1e-3 y operaciones constantes en numerador y denominador. La unidad imaginaria ya no altera el nombre pi; los errores identifican el coeficiente.

## Diseño analógico por especificaciones

Nueva herramienta en Diseño de filtros: Butterworth, Chebyshev I, Chebyshev II y elíptico, con comparación de familias. Admite pasabajos, pasaaltos, pasabanda y rechazabanda, bordes en rad/s y tolerancias de amplitud. Incluye diagramas de ayuda, respuesta en frecuencia logarítmica y evaluación de tolerancias. Permite exportar transferencias y enviarlas a respuesta temporal o frecuencial.

Se comprueba la precisión de los coeficientes expandidos frente al diseño por polos y ceros antes de publicar el resultado. La herramienta diseña H(s); no sintetiza un circuito físico.

## Comprobación acotada

Se comprobaron las cuatro familias en los cuatro tipos de banda y se abrió el panel con cálculo comparativo, gráfica y ayuda. No se repitieron las pruebas generales del portable ni las revisiones de interfaz pendiente.

## Alcance para la primera estable

Este cambio cubre el diseño analógico por especificaciones pendiente en COBERTURA_SYS_I_II_0.54.md. Sigue pendiente su realización física. Los demás faltantes de ese documento se conservan: diagramas de realización, módulo–fase, modulación/demodulación, selección de tasas de muestreo pasabanda, ampliaciones bilaterales/ROC y efectos de aritmética de implementación. Señales Aleatorias queda para más adelante.

Esta entrega sigue siendo una versión preliminar; no certifica cobertura completa de los programas.
