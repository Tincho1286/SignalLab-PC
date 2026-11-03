# SignalLab PC 0.73 — datos primero y acciones de resultados consistentes

## Pantallas iniciales más despejadas

El visor común muestra una indicación simple antes de calcular. Las vistas de gráfico, informe, valores y exportación aparecen cuando existe un resultado. Los casos de informe sin señal, como el mapeo de frecuencias, muestran su informe sin botones de exportación de muestras inexistentes. STFT oculta los controles de consulta de ventanas hasta obtener el espectrograma.

Fourier algebraica presenta primero Expresión y condiciones. Sólo tras una expresión evaluada y sin condiciones adicionales aparecen los campos del registro numérico; el registro tiene su propia pestaña. Editar la definición indica que el resultado anterior debe recalcularse. El informe puede copiarse/exportarse y no queda limitado a una franja de 120 píxeles.

## Diseño por especificaciones

La carga de bandas usa etiquetas completas, colores de paso/rechazo y campos a todo el ancho. El esquema de bandas se despliega bajo demanda; los dibujos explicados siguen en F1. Las aclaraciones largas pasan a las ayudas emergentes de los campos, manteniendo límites y mensajes de error. Las etiquetas aprovechan su fila en lugar de quebrarse dentro de una columna estrecha.

Al cambiar entre FIR e IIR digitales por especificaciones se copian tipo, bordes y tolerancias. Cada método conserva sus parámetros propios. Un cambio a dominio analógico conserva sus frecuencias anteriores y avisa que no se convierten automáticamente rad/muestra a rad/s. No se altera el diseño matemático ni su comprobación en rejilla.

## Acciones sobre filtros calculados

FIR, biquad, RC, modelos y herramientas de diseño/ajuste comparten Analizar, Usar filtro en y Exportar filtro. Analizar ofrece polos/ceros, frecuencia y respuesta temporal. Usar filtro en contiene destinos distintos de esas consultas para no repetirlas. Las acciones usan el resultado calculado y su referencia; no vuelven a leer datos editados sin calcular.

Polos y ceros copia el filtro al análisis y calcula allí el plano, sin abrir el editor ni exigir un análisis frecuencial previo. La vista conserva el criterio causal/ROC y las advertencias de raíces numéricas. Su informe tiene acciones de copia/exportación. La respuesta en frecuencia permanece pendiente hasta calcularla; no se muestra una curva anterior como si fuese la del filtro recién copiado.

Después de diseñar se presenta el informe. La figura continúa abriéndose aparte, y las opciones de representación permanecen accesibles en Gráfico. El editor de polos/ceros conserva su vista de edición. Las pestañas largas admiten desplazamiento y muestran el nombre completo en la ayuda emergente.

## Ayuda y alcance académico

Se corrigieron las fichas de Impulse y Step: ambos tienen alias en el motor simbólico, con convenciones distintas del muestreo numérico continuo. Las ayudas de diseño y Fourier describen el recorrido actual.

Se revisaron los contenidos analíticos originales de Sistemas I (páginas 6–14) y II (ejes 1–8). COBERTURA_SYS_I_II_ACTUAL.md distingue herramientas disponibles, límites y carencias reales: realizaciones, representaciones/márgenes del análisis común, relaciones módulo–fase y aritmética de implementación. Las ampliaciones deben integrarse en problemas existentes. No se afirma cobertura total; modulación y ampliación de Aleatorias siguen excluidas. El cierre vigente reemplaza pendientes antiguos repetidos y conserva su historial.

## Comprobación dirigida

Apertura sin controles de resultado vacíos; generación y resultado; FIR por especificaciones y diseño directo; acciones/reutilización y copia al plano de polos/ceros; cálculo frecuencial posterior; informe sin muestras; STFT; Fourier algebraica y su registro numérico; cambios de entrada. Se verificó la conservación de especificaciones FIR/IIR con los bordes del pasabanda reportado, la separación de dominio y el esquema opcional. Recorridos modificados revisados a 1366, 800 y 640 píxeles; no se repitió una campaña general de cálculo o instalación.

Continúa el desarrollo hacia la 1.0. El estado académico y de cierre se documenta sin convertir la compilación o un caso aprobado en una afirmación de completitud.
