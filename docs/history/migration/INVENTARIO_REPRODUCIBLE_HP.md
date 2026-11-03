# Inventario reproducible HP y rutas PC

Fuente SHA-256: `9EC7E69183AC50303A4EF0FDFAFD4B585F33D75D2164AE725E95574A75033DCB`.

157 llamadas SSMenu; 110 títulos literales; 5 listas de opciones calculadas; 751 expresiones de opción explícitas, de las cuales 7 se construyen dinámicamente.

Estos conteos no son porcentajes de migración. El tablero principal y los comportamientos dentro de cada rama necesitan auditoría adicional. Los vínculos relacionan familias; no prueban equivalencia de subopciones.

## SSUseBuffer · Interpretar datos

Línea 126 · `hp.menu.ssusebuffer.interpretar-datos.1`

- 1. Conservar origen y paso
- 2. Solo valores; indice desde cero
- 3. Cancelar

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSExportData · Destino de exportacion

Línea 194 · `hp.menu.ssexportdata.destino-de-exportacion.1`

- 1. Banco SignalLab (menos memoria)
- 2. Listas Home L0 y L1
- 3. Tabla Home M0
- 4. Banco + L0 + L1 + M0
- 5. Guardar en historial
- 6. Cancelar

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSReadList · Fuente de datos

Línea 226 · `hp.menu.ssreadlist.fuente-de-datos.1`

- 1. Ingresar una lista
- 2. Usar banco SignalLab
- 3. Usar lista L0 de Home

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSReadList · Fuente de datos

Línea 234 · `hp.menu.ssreadlist.fuente-de-datos.2`

- 1. Ingresar una lista
- 2. Usar lista L0 de Home

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSUseHomeList · Lista L0 de Home

Línea 272 · `hp.menu.ssusehomelist.lista-l0-de-home.1`

- 1. Usar valores e indice desde cero
- 2. Asociar eje uniforme de L1
- 3. Cancelar

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSShow · Título calculado

Línea 1719 · `hp.menu.ssshow.dynamic.1`

- 1. Tabla de valores
- 2. Grafico de la senal
- 3. Formula / representacion
- 4. Datos y eje del resultado
- 5. Exportar resultado
- 6. Volver

Rutas relacionadas: `tool.signal_editor.0`
Estado: pendiente de auditoría por opción.

## SSHistoryMenu · Recientes / banco

Línea 2331 · `hp.menu.sshistorymenu.recientes-banco.1`

Lista construida en ejecución: requiere revisar su construcción.


Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSHistoryMenu · Calculo guardado

Línea 2375 · `hp.menu.sshistorymenu.calculo-guardado.1`

- 1. Reabrir resultado / editar
- 2. Consultar datos guardados
- 3. Volver a Recientes

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSHistoryMenu · Título calculado

Línea 2411 · `hp.menu.sshistorymenu.dynamic.1`

Lista construida en ejecución: requiere revisar su construcción.


Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSHistoryMenu · Título calculado

Línea 2423 · `hp.menu.sshistorymenu.dynamic.2`

- 1. Tabla de valores
- 2. Grafico de parte real
- 3. Exportar / usar como banco
- 4. Volver al registro

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSHistoryMenu · Senal guardada

Línea 2442 · `hp.menu.sshistorymenu.senal-guardada.1`

- 1. Ver datos y eje
- 2. Ver tabla
- 3. Reutilizar como banco
- 4. Volver

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSCursorDetail · Lecturas del grafico

Línea 2481 · `hp.menu.sscursordetail.lecturas-del-grafico.1`

- 1. Valor del punto actual B
- 2. Fijar este punto como A
- 3. Medir de A a B
- 4. Borrar referencia A
- 5. Contexto del grafico
- 6. Volver

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSMathTextView · Formula y condiciones

Línea 2556 · `hp.menu.ssmathtextview.formula-y-condiciones.1`

- 1. Formula Textbook
- 2. Limites y condiciones
- 3. Expresion lineal completa
- 4. Continuar al integrando
- 5. Volver

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSMenu · Antes de salir

Línea 3510 · `hp.menu.ssmenu.antes-de-salir.1`

- 1. Guardar en Recientes y salir
- 2. Salir sin guardar
- 3. Seguir en el resultado

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSPlotDiscrete · Acciones del grafico

Línea 3763 · `hp.menu.ssplotdiscrete.acciones-del-grafico.1`

- 1. Tabla completa
- 2. Lectura del cursor
- 3. Activar/desactivar cursor
- 4. Original / limpia
- 5. Autoescala
- 6. Volver al grafico

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSPlotXY · Acciones del grafico

Línea 4113 · `hp.menu.ssplotxy.acciones-del-grafico.1`

- 1. Tabla completa
- 2. Lectura del cursor
- 3. Activar/desactivar cursor
- 4. Original / limpia
- 5. Autoescala
- 6. Volver al grafico

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSPlotDual · Acciones de comparacion

Línea 4362 · `hp.menu.ssplotdual.acciones-de-comparacion.1`

- 1. Tablas
- 2. Mostrar/ocultar contraria
- 3. Original / limpia
- 4. Autoescala
- 5. Volver al grafico

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSPlotDual · Acciones de comparacion

Línea 4365 · `hp.menu.ssplotdual.acciones-de-comparacion.2`

- 1. Tablas
- 2. Original / limpia
- 3. Autoescala
- 4. Volver al grafico

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSPlotDual · Datos de la comparacion

Línea 4373 · `hp.menu.ssplotdual.datos-de-la-comparacion.1`

- 1. DTFT: tabla compleja
- 2. DFT: tabla compleja
- 3. Volver al grafico

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSPlotDual · Acciones de comparacion

Línea 4482 · `hp.menu.ssplotdual.acciones-de-comparacion.3`

- 1. Tablas
- 2. Mostrar/ocultar contraria
- 3. Original / limpia
- 4. Autoescala
- 5. Volver al grafico

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSPlotDual · Acciones de comparacion

Línea 4485 · `hp.menu.ssplotdual.acciones-de-comparacion.4`

- 1. Tablas
- 2. Original / limpia
- 3. Autoescala
- 4. Volver al grafico

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSPlotPZ · Cambios del filtro

Línea 4624 · `hp.menu.ssplotpz.cambios-del-filtro.1`

- 1. Guardar en Recientes y volver
- 2. Descartar cambios
- 3. Seguir editando

Rutas relacionadas: `tool.systems.6`
Estado: pendiente de auditoría por opción.

## SSPlotPZ · Posicionar polos y ceros

Línea 4651 · `hp.menu.ssplotpz.posicionar-polos-y-ceros.1`

- 1. Agregar cero en cursor
- 2. Agregar polo en cursor
- 3. Cero y su conjugado
- 4. Polo y su conjugado
- 5. Mover un cero al cursor
- 6. Mover un polo al cursor
- 7. Eliminar un cero
- 8. Eliminar un polo
- 9. Coordenadas exactas del cursor
- 10. Cambiar paso de las flechas
- 11. Guardar y volver
- 12. Volver al plano
- 13. Autoescala
- 14. Agregar por coordenadas
- 15. Ver H(z) del diseno

Rutas relacionadas: `tool.systems.6`
Estado: pendiente de auditoría por opción.

## SSPlotPZ · Agregar por coordenadas

Línea 4708 · `hp.menu.ssplotpz.agregar-por-coordenadas.1`

- 1. Polo
- 2. Cero
- 3. Volver

Rutas relacionadas: `tool.systems.6`
Estado: pendiente de auditoría por opción.

## SSResultBrowse · Título calculado

Línea 4859 · `hp.menu.ssresultbrowse.dynamic.1`

Lista construida en ejecución: requiere revisar su construcción.


Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSResultBrowse · Título calculado

Línea 4869 · `hp.menu.ssresultbrowse.dynamic.2`

- 1. Volver al resultado
- 2. Texto lineal completo
- 3. Contexto y condiciones
- 4. Ver Textbook otra vez

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSResultBrowse · Título calculado

Línea 4880 · `hp.menu.ssresultbrowse.dynamic.3`

- 1. Resultado Textbook
- 2. Ver entrada utilizada
- 3. Interpretacion y condiciones
- 4. Expresion lineal completa
- 5. Volver

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSCASRunTransform · Título calculado

Línea 5341 · `hp.menu.sscasruntransform.dynamic.1`

- 1. Ver transformada calculada
- 2. Aplicar propiedad
- 3. Volver

Rutas relacionadas: `tool.system_analysis.0`, `tool.symbolic.0`, `tool.symbolic.1`
Estado: pendiente de auditoría por opción.

## SSCASRunTransform · Título calculado

Línea 5348 · `hp.menu.sscasruntransform.dynamic.2`

- 1. [Texto calculado] izquierda
- 2. [Texto calculado] derecha
- 3. Multiplicar por X^k
- 4. Modular: exp / cos / sin
- 5. Convolucion con otra senal
- 6. Producto con otra senal
- 7. Volver

Rutas relacionadas: `tool.system_analysis.0`, `tool.symbolic.0`, `tool.symbolic.1`
Estado: pendiente de auditoría por opción.

## SSCASRunTransform · Modulacion

Línea 5417 · `hp.menu.sscasruntransform.modulacion.1`

- 1. exp(i*(w0*X+phi))
- 2. cos(w0*X+phi)
- 3. sin(w0*X+phi)
- 4. Volver

Rutas relacionadas: `tool.system_analysis.0`, `tool.symbolic.0`, `tool.symbolic.1`
Estado: pendiente de auditoría por opción.

## SSSampleResults · Título calculado

Línea 5642 · `hp.menu.sssampleresults.dynamic.1`

- 1. Tabla n, t y x[n]
- 2. Grafico con eje temporal
- 3. Formula utilizada
- 4. Exportar muestras
- 5. Metodo, unidades y limites
- 6. Editar parametros
- 7. Vista por indice n
- 8. Volver

Rutas relacionadas: `tool.sampling.0`
Estado: pendiente de auditoría por opción.

## SSSampleResults · Indice n desde 0

Línea 5645 · `hp.menu.sssampleresults.indice-n-desde-0.1`

- 1. Tabla por indice
- 2. Grafico por indice
- 3. Exportar con indice n
- 4. Volver

Rutas relacionadas: `tool.sampling.0`
Estado: pendiente de auditoría por opción.

## SSRateResults · Título calculado

Línea 5790 · `hp.menu.ssrateresults.dynamic.1`

- 1. Tabla de entrada
- 2. Tabla de salida y[n]
- 3. Grafico discreto y[n]
- 4. Exportar salida
- 5. Parametros usados
- 6. Editar factor y fase
- 7. Filtro opcional antialias/recup.
- 8. Comparar con y sin filtro
- 9. [Texto calculado] etiquetaFiltrada
- 10. [Texto calculado] consultaFiltro
- 11. Curva SINC (extra)
- 12. Espectros por etapa
- 13. Tiempo fisico / exportar
- 14. Volver

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## SSRateResults · Salida: eje t en segundos

Línea 5804 · `hp.menu.ssrateresults.salida-eje-t-en-segundos.1`

- 1. Tabla con tiempo
- 2. Grafico con tiempo
- 3. Exportar con tiempo
- 4. Volver

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## SSRateResults · Título calculado

Línea 5865 · `hp.menu.ssrateresults.dynamic.2`

- 1. Sin filtro
- 2. FIR Hamming centrado
- 3. IIR causal por coeficientes b/a
- 4. Pasa bajos ideal: amplitud y corte
- 5. Volver

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## SSRateResults · Unidad de frecuencia de corte

Línea 5893 · `hp.menu.ssrateresults.unidad-de-frecuencia-de-corte.1`

- 1. fc en ciclos/muestra
- 2. wc en radianes/muestra
- 3. Cancelar

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## SSRateResults · IIR: confirmar advertencia

Línea 5953 · `hp.menu.ssrateresults.iir-confirmar-advertencia.1`

- 1. Cancelar cambio
- 2. Aplicar para analisis teorico

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## SSRateResults · Comparar filtro ideal

Línea 6078 · `hp.menu.ssrateresults.comparar-filtro-ideal.1`

- 1. Muestras sin/con filtro
- 2. Curva SINC de la salida
- 3. Volver

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## SSRateResults · Consultar filtro IIR

Línea 6092 · `hp.menu.ssrateresults.consultar-filtro-iir.1`

- 1. Funcion H(z)
- 2. Numerador b[k]
- 3. Denominador a[k]
- 4. Estado y convenciones
- 5. Volver

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## SSRateResults · Consultar filtro ideal

Línea 6099 · `hp.menu.ssrateresults.consultar-filtro-ideal.1`

- 1. Respuesta H y contexto
- 2. Formula de h[k]
- 3. Nucleo h[k] para k >= 0
- 4. Volver

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## SSRateResults · Espectros por etapa

Línea 6111 · `hp.menu.ssrateresults.espectros-por-etapa.1`

- 1. Original x[n]
- 2. Salida sin filtro opcional
- 3. [Texto calculado] etiquetaFiltrada
- 4. Salida final y[n]
- 5. Volver

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## SSRateResults · Título calculado

Línea 6149 · `hp.menu.ssrateresults.dynamic.3`

- 1. Magnitud |X(w)|
- 2. Fase en radianes
- 3. Tabla compleja X(w)
- 4. Exportar espectro
- 5. Convenciones y registro
- 6. Volver

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## SSDFTResults · Título calculado

Línea 6254 · `hp.menu.ssdftresults.dynamic.1`

Lista construida en ejecución: requiere revisar su construcción.


Rutas relacionadas: `tool.basic.dft`, `tool.basic.idft`
Estado: pendiente de auditoría por opción.

## SSDFTResults · Vistas del resultado

Línea 6261 · `hp.menu.ssdftresults.vistas-del-resultado.1`

- 1. Magnitud
- 2. Fase (rad)
- 3. Parte real
- 4. Parte imaginaria
- 5. Volver

Rutas relacionadas: `tool.basic.dft`, `tool.basic.idft`
Estado: pendiente de auditoría por opción.

## SSDFTResults · Formula y eje

Línea 6339 · `hp.menu.ssdftresults.formula-y-eje.1`

- 1. Formula del registro Textbook
- 2. Unidades y convenciones
- 3. Volver

Rutas relacionadas: `tool.basic.dft`, `tool.basic.idft`
Estado: pendiente de auditoría por opción.

## SSDFTResults · Eje y unidades

Línea 6362 · `hp.menu.ssdftresults.eje-y-unidades.1`

- 1. Indice n / frecuencia original
- 2. Bins k centrados (DFT/serie)
- 3. Hz / segundos: indicar Ts
- 4. Volver

Rutas relacionadas: `tool.basic.dft`, `tool.basic.idft`
Estado: pendiente de auditoría por opción.

## SSDFTResults · Analisis de fase

Línea 6378 · `hp.menu.ssdftresults.analisis-de-fase.1`

- 1. Fase desenrollada
- 2. Retardo de grupo (muestras)
- 3. Volver

Rutas relacionadas: `tool.basic.dft`, `tool.basic.idft`
Estado: pendiente de auditoría por opción.

## SSSequenceExprResults · Título calculado

Línea 6403 · `hp.menu.sssequenceexprresults.dynamic.1`

- 1. Tabla numerica x[n]
- 2. Grafico discreto x[n]
- 3. Expresion e intervalo
- 4. Exportar secuencia
- 5. Metodo y contexto
- 6. Editar parametros
- 7. Volver

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSQuantResults · Título calculado

Línea 6514 · `hp.menu.ssquantresults.dynamic.1`

- 1. Tabla x, xq y error
- 2. Grafico comparativo
- 3. Grafico del error xq-x
- 4. Parametros y formula
- 5. Intervalo para SNR
- 6. Editar cuantizador
- 7. Vistas y exportacion con eje original
- 8. Volver

Rutas relacionadas: `tool.sampling.4`
Estado: pendiente de auditoría por opción.

## SSQuantResults · Metodo / offset

Línea 6526 · `hp.menu.ssquantresults.metodo-offset.1`

- 1. Redondeo sin offset
- 2. Truncamiento sin offset
- 3. Redondeo: nivel cero
- 4. Truncamiento: nivel cero
- 5. Cancelar

Rutas relacionadas: `tool.sampling.4`
Estado: pendiente de auditoría por opción.

## SSQuantResults · Título calculado

Línea 6542 · `hp.menu.ssquantresults.dynamic.2`

- 1. Tabla salida xq
- 2. Comparar x y xq
- 3. Error xq-x
- 4. Exportar xq con eje
- 5. Volver

Rutas relacionadas: `tool.sampling.4`
Estado: pendiente de auditoría por opción.

## SSQuantResults · Intervalo para SNR

Línea 6555 · `hp.menu.ssquantresults.intervalo-para-snr.1`

- 1. Registro completo
- 2. Por indices n (desde 0)
- 3. Por eje original (t o n)
- 4. Volver

Rutas relacionadas: `tool.sampling.4`
Estado: pendiente de auditoría por opción.

## SSQuantResults · Título calculado

Línea 6577 · `hp.menu.ssquantresults.dynamic.3`

- 1. INCLUIR muestra del final
- 2. EXCLUIR muestra del final
- 3. Cancelar

Rutas relacionadas: `tool.sampling.4`
Estado: pendiente de auditoría por opción.

## SSQuantResults · Aplicar intervalo SNR

Línea 6599 · `hp.menu.ssquantresults.aplicar-intervalo-snr.1`

- 1. [Texto calculado] "Aplicar: "+STRING(lastNew-firstNew+1)+" muestras"
- 2. Cancelar; conservar anterior

Rutas relacionadas: `tool.sampling.4`
Estado: pendiente de auditoría por opción.

## SSConvDiscreteResults · Título calculado

Línea 6614 · `hp.menu.ssconvdiscreteresults.dynamic.1`

- 1. Tabla salida y[n]
- 2. Tabla entrada x[n]
- 3. Tabla impulso h[n]
- 4. Grafico de y[n]
- 5. Resultado matematico
- 6. Volver

Rutas relacionadas: `tool.basic.convolve`
Estado: pendiente de auditoría por opción.

## SSConvContinuousResults · Título calculado

Línea 6630 · `hp.menu.ssconvcontinuousresults.dynamic.1`

- 1. Datos de salida y(t)
- 2. Datos de entrada x(t)
- 3. Datos del impulso h(t)
- 4. Grafico de salida y(t)
- 5. Graficos de x(t) y h(t)
- 6. Resultado matematico
- 7. Desarrollo y metodo
- 8. Volver

Rutas relacionadas: `tool.basic.continuous_convolve`, `tool.convolution_algebra.0`
Estado: pendiente de auditoría por opción.

## SSConvDFTResults · Título calculado

Línea 6652 · `hp.menu.ssconvdftresults.dynamic.1`

- 1. Tabla del resultado
- 2. Grafico y[n]: parte real
- 3. Resultado matematico
- 4. Metodo y teorema
- 5. Grafico y[n]: parte imaginaria
- 6. Volver

Rutas relacionadas: `tool.basic.circular`
Estado: pendiente de auditoría por opción.

## UIGenerator · Generador discreto

Línea 6704 · `hp.menu.uigenerator.generador-discreto.1`

- 1. Impulso
- 2. Escalon
- 3. Rampa
- 4. Exponencial
- 5. Seno
- 6. Pulso rectangular
- 7. Expresion matematica x[n]

Rutas relacionadas: `tool.basic.generate`
Estado: pendiente de auditoría por opción.

## UISampleExpr · Expresion o tramos

Línea 6757 · `hp.menu.uisampleexpr.expresion-o-tramos.1`

- 1. Muestrear expresion x(t)
- 2. Tramos continuos x(t)
- 3. Tramos discretos x[n]
- 4. Volver

Rutas relacionadas: `tool.signal_editor.0`, `tool.basic.generate`, `tool.sampling.0`
Estado: pendiente de auditoría por opción.

## UISampleExpr · Editar senal sin recargar

Línea 6837 · `hp.menu.uisampleexpr.editar-senal-sin-recargar.1`

- 1. Expresion o un tramo
- 2. Origen de la ventana
- 3. Paso Ts (continuo)
- 4. Cantidad de puntos N
- 5. Valor exterior (tramos)
- 6. Volver al resultado

Rutas relacionadas: `tool.signal_editor.0`, `tool.basic.generate`, `tool.sampling.0`
Estado: pendiente de auditoría por opción.

## UITransformSignal · Operacion con secuencias

Línea 6908 · `hp.menu.uitransformsignal.operacion-con-secuencias.1`

- 1. Desplazar x[n-k]
- 2. Invertir x[-n]
- 3. Escalar amplitud
- 4. Sumar otra senal
- 5. Partes par e impar

Rutas relacionadas: `tool.basic.shift`, `tool.basic.reverse`, `tool.basic.scale`, `tool.basic.parity`, `tool.basic.sum`
Estado: pendiente de auditoría por opción.

## UITransformSignal · Título calculado

Línea 6928 · `hp.menu.uitransformsignal.dynamic.1`

- 1. Parte par
- 2. Parte impar
- 3. Entrada original
- 4. Volver

Rutas relacionadas: `tool.basic.shift`, `tool.basic.reverse`, `tool.basic.scale`, `tool.basic.parity`, `tool.basic.sum`
Estado: pendiente de auditoría por opción.

## SSMeasureResults · Título calculado

Línea 7036 · `hp.menu.ssmeasureresults.dynamic.1`

- 1. Calcular E y P global
- 2. Entrada y alcance
- 3. Volver

Rutas relacionadas: `tool.basic.measures`
Estado: pendiente de auditoría por opción.

## SSMeasureResults · Título calculado

Línea 7040 · `hp.menu.ssmeasureresults.dynamic.2`

- 1. Energia y potencia global
- 2. Tabla de la senal
- 3. Tabla de |x|^2
- 4. Grafico de la senal
- 5. Grafico de |x|^2
- 6. Expresion y planteos
- 7. Medidas de ventana
- 8. Metodo y limites
- 9. Volver

Rutas relacionadas: `tool.basic.measures`
Estado: pendiente de auditoría por opción.

## UISignalMeasuresTheory · Dominio de energia teorica

Línea 7334 · `hp.menu.uisignalmeasurestheory.dominio-de-energia-teorica.1`

- 1. Discreta: x[n]
- 2. Continua: x(t)
- 3. Volver

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## UISignalMeasures · Energia y potencia

Línea 7345 · `hp.menu.uisignalmeasures.energia-y-potencia.1`

- 1. Lista discreta finita
- 2. Expresion discreta por indices
- 3. Expresion continua por intervalo
- 4. Analisis teorico en todo el eje
- 5. Formulas y clasificacion
- 6. Densidad espectral de energia
- 7. Volver

Rutas relacionadas: `tool.basic.measures`
Estado: pendiente de auditoría por opción.

## UI_SIGNALS · Senales continuas y discretas

Línea 7365 · `hp.menu.ui-signals.senales-continuas-y-discretas.1`

- 1. Crear secuencia x[n]
- 2. Crear expresion o senal por tramos
- 3. Transformar o sumar secuencias
- 4. Calcular energia y potencia
- 5. Conceptos y clasificacion
- 6. Volver al inicio

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## UICorrelation · Correlacion y autocorrelacion

Línea 7463 · `hp.menu.uicorrelation.correlacion-y-autocorrelacion.1`

- 1. Autocorrelacion discreta
- 2. Correlacion cruzada discreta
- 3. Autocorrelacion continua
- 4. Correlacion cruzada continua
- 5. Auto periodica discreta
- 6. Auto periodica continua
- 7. Volver

Rutas relacionadas: `tool.correlation_algebra.0`, `tool.correlation.0`, `tool.correlation.1`
Estado: pendiente de auditoría por opción.

## UICorrelation · Modelo de correlacion discreta

Línea 7474 · `hp.menu.uicorrelation.modelo-de-correlacion-discreta.1`

- 1. Lineal: registro finito
- 2. Circular: un periodo
- 3. Volver

Rutas relacionadas: `tool.correlation_algebra.0`, `tool.correlation.0`, `tool.correlation.1`
Estado: pendiente de auditoría por opción.

## UICorrelation · Título calculado

Línea 7515 · `hp.menu.uicorrelation.dynamic.1`

- 1. Lista o datos exportados
- 2. Expresion matematica
- 3. Cancelar

Rutas relacionadas: `tool.correlation_algebra.0`, `tool.correlation.0`, `tool.correlation.1`
Estado: pendiente de auditoría por opción.

## UICorrelation · Título calculado

Línea 7630 · `hp.menu.uicorrelation.dynamic.2`

- 1. Tabla de correlacion
- 2. Grafico de parte real
- 3. Grafico de parte imaginaria
- 4. Grafico de modulo |r|
- 5. Resumen y valor en cero
- 6. Definicion y formula
- 7. Consultar entradas
- 8. Exportar correlacion
- 9. Metodo y convenciones
- 10. Normalizacion / escala
- 11. Volver

Rutas relacionadas: `tool.correlation_algebra.0`, `tool.correlation.0`, `tool.correlation.1`
Estado: pendiente de auditoría por opción.

## UICorrelation · Formula de correlacion

Línea 7651 · `hp.menu.uicorrelation.formula-de-correlacion.1`

- 1. Definicion y escala
- 2. CAS sin normalizar: todo el eje
- 3. Volver

Rutas relacionadas: `tool.correlation_algebra.0`, `tool.correlation.0`, `tool.correlation.1`
Estado: pendiente de auditoría por opción.

## UICorrelation · Entradas utilizadas

Línea 7706 · `hp.menu.uicorrelation.entradas-utilizadas.1`

- 1. Primera entrada x
- 2. Segunda entrada h
- 3. Volver

Rutas relacionadas: `tool.correlation_algebra.0`, `tool.correlation.0`, `tool.correlation.1`
Estado: pendiente de auditoría por opción.

## UICorrelation · Escala de correlacion

Línea 7712 · `hp.menu.uicorrelation.escala-de-correlacion.1`

- 1. Integral de un periodo
- 2. Normalizada: R(tau)/R(0)
- 3. Promedio de periodo: r/T
- 4. Volver

Rutas relacionadas: `tool.correlation_algebra.0`, `tool.correlation.0`, `tool.correlation.1`
Estado: pendiente de auditoría por opción.

## UICorrelation · Escala de correlacion

Línea 7714 · `hp.menu.uicorrelation.escala-de-correlacion.2`

- 1. Sin normalizar: suma
- 2. Coeficiente r/sqrt(Ex*Eh)
- 3. Promedio de periodo: r/L
- 4. Volver

Rutas relacionadas: `tool.correlation_algebra.0`, `tool.correlation.0`, `tool.correlation.1`
Estado: pendiente de auditoría por opción.

## UICorrelation · Escala de correlacion

Línea 7715 · `hp.menu.uicorrelation.escala-de-correlacion.3`

- 1. Sin normalizar: suma/integral
- 2. Coeficiente r/sqrt(Ex*Eh)
- 3. Volver

Rutas relacionadas: `tool.correlation_algebra.0`, `tool.correlation.0`, `tool.correlation.1`
Estado: pendiente de auditoría por opción.

## UIResponses · Entrada del sistema

Línea 7752 · `hp.menu.uiresponses.entrada-del-sistema.1`

- 1. Impulso
- 2. Escalon

Rutas relacionadas: `tool.systems.5`, `tool.systems.9`
Estado: pendiente de auditoría por opción.

## UIPolesZeros · Polos, ceros y filtros

Línea 7793 · `hp.menu.uipoleszeros.polos-ceros-y-filtros.1`

- 1. Analizar / editar coeficientes
- 2. Disenar ubicando polos y ceros
- 3. Volver

Rutas relacionadas: `tool.system_analysis.0`, `tool.systems.3`, `tool.systems.6`
Estado: pendiente de auditoría por opción.

## UIPolesZeros · Dominio de estabilidad

Línea 7796 · `hp.menu.uipoleszeros.dominio-de-estabilidad.1`

- 1. Continuo: plano s
- 2. Discreto: plano z

Rutas relacionadas: `tool.system_analysis.0`, `tool.systems.3`, `tool.systems.6`
Estado: pendiente de auditoría por opción.

## UIPolesZeros · Título calculado

Línea 7836 · `hp.menu.uipoleszeros.dynamic.1`

- 1. Diagrama polos y ceros
- 2. Valores y estabilidad
- 3. [Texto calculado] "Formula H("+variable+")"
- 4. Editar coeficientes de H
- 5. Posicionar polos y ceros
- 6. Editar ganancia K
- 7. Magnitud y fase
- 8. Aplicar a una senal
- 9. Coeficientes y exportacion
- 10. Volver

Rutas relacionadas: `tool.system_analysis.0`, `tool.systems.3`, `tool.systems.6`
Estado: pendiente de auditoría por opción.

## UIPolesZeros · Respuesta del diseno

Línea 7896 · `hp.menu.uipoleszeros.respuesta-del-diseno.1`

- 1. Magnitud |H(e^jw)|
- 2. Fase en radianes
- 3. Magnitud en dB
- 4. Volver

Rutas relacionadas: `tool.system_analysis.0`, `tool.systems.3`, `tool.systems.6`
Estado: pendiente de auditoría por opción.

## UIPolesZeros · Coeficientes del filtro

Línea 7923 · `hp.menu.uipoleszeros.coeficientes-del-filtro.1`

- 1. Tabla numerador b[k]
- 2. Tabla denominador a[k]
- 3. Exportar b[k]
- 4. Exportar a[k]
- 5. Volver

Rutas relacionadas: `tool.system_analysis.0`, `tool.systems.3`, `tool.systems.6`
Estado: pendiente de auditoría por opción.

## UIPolesZeros · Aplicar el diseno actual

Línea 7930 · `hp.menu.uipoleszeros.aplicar-el-diseno-actual.1`

- 1. Continuar con esta H(z)
- 2. Cancelar

Rutas relacionadas: `tool.system_analysis.0`, `tool.systems.3`, `tool.systems.6`
Estado: pendiente de auditoría por opción.

## UIPolesZeros · Título calculado

Línea 7941 · `hp.menu.uipoleszeros.dynamic.2`

- 1. Tabla y[n]
- 2. Grafico y[n]
- 3. Exportar y[n]
- 4. Volver al diseno

Rutas relacionadas: `tool.system_analysis.0`, `tool.systems.3`, `tool.systems.6`
Estado: pendiente de auditoría por opción.

## UI_LTI · Sistemas LTI

Línea 8000 · `hp.menu.ui-lti.sistemas-lti.1`

- 1. Convolucion discreta x[n]*h[n]
- 2. Convolucion continua numerica
- 3. Correlacion y autocorrelacion
- 4. Resolver ecuacion en diferencias
- 5. Respuesta a impulso o escalon
- 6. Polos, ceros y estabilidad
- 7. Conceptos y propiedades LTI
- 8. Volver al inicio

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## UIZTransform · Transformada Z

Línea 8085 · `hp.menu.uiztransform.transformada-z.1`

- 1. Secuencia finita con indices
- 2. Expresion CAS y graficos
- 3. Simbolica: tablas y CAS
- 4. Volver

Rutas relacionadas: `tool.symbolic.2`, `tool.symbolic.3`
Estado: pendiente de auditoría por opción.

## UIZTransform · Título calculado

Línea 8123 · `hp.menu.uiztransform.dynamic.1`

- 1. Formula X(z) Textbook
- 2. Magnitud sobre z=r*exp(i*w)
- 3. Fase sobre z=r*exp(i*w)
- 4. Tabla compleja de X(z)
- 5. Exportar valores del contorno
- 6. Cambiar radio r
- 7. Entrada y region de convergencia
- 8. Volver

Rutas relacionadas: `tool.symbolic.2`, `tool.symbolic.3`
Estado: pendiente de auditoría por opción.

## UIBilinear · Bilineal sin resultado

Línea 8257 · `hp.menu.uibilinear.bilineal-sin-resultado.1`

- 1. Editar H(s)
- 2. Editar T
- 3. Volver

Rutas relacionadas: `tool.systems.7`
Estado: pendiente de auditoría por opción.

## UIBilinear · Título calculado

Línea 8261 · `hp.menu.uibilinear.dynamic.1`

- 1. H(z) Textbook
- 2. Sustitucion y unidades
- 3. Editar H(s)
- 4. Editar T
- 5. Volver

Rutas relacionadas: `tool.systems.7`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Modo de Fourier continua

Línea 8351 · `hp.menu.uifouriercontinuous.modo-de-fourier-continua.1`

- 1. Numerico: graficos y tablas
- 2. Simbolico: tablas y CAS
- 3. Volver

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Entrada serie continua

Línea 8362 · `hp.menu.uifouriercontinuous.entrada-serie-continua.1`

- 1. Expresion x(t)
- 2. Tren de pulsos rectangulares
- 3. Tren de impulsos Dirac
- 4. Volver

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Título calculado

Línea 8447 · `hp.menu.uifouriercontinuous.dynamic.1`

- 1. Tabla de coeficientes c[k]
- 2. Magnitud por armonico
- 3. Fase en radianes
- 4. Formula Textbook y c[0]
- 5. Ver tren de entrada
- 6. Suma parcial de Fourier
- 7. Exportar coeficientes
- 8. Parametros e interpretacion
- 9. Editar parametros
- 10. Volver

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Entrada B + tren Dirac

Línea 8461 · `hp.menu.uifouriercontinuous.entrada-b-tren-dirac.1`

- 1. Nivel continuo B
- 2. Impulsos: posiciones y areas
- 3. Volver

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Editar tren periodico

Línea 8475 · `hp.menu.uifouriercontinuous.editar-tren-periodico.1`

- 1. Periodo T
- 2. Altura o area A
- 3. Offset vertical B
- 4. Ancho (solo pulsos)
- 5. Centro temporal
- 6. Armonicos K
- 7. Volver al resultado

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Fourier cancelada

Línea 8548 · `hp.menu.uifouriercontinuous.fourier-cancelada.1`

- 1. Reintentar: misma entrada
- 2. Volver sin calcular

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Inversa cancelada

Línea 8567 · `hp.menu.uifouriercontinuous.inversa-cancelada.1`

- 1. Reintentar: mismo espectro
- 2. Volver sin calcular

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Título calculado

Línea 8590 · `hp.menu.uifouriercontinuous.dynamic.2`

- 1. Resultado matematico
- 2. Grafico de magnitud de salida
- 3. Grafico de fase de salida
- 4. Entrada utilizada
- 5. Tabla compleja de salida
- 6. Exportar salida
- 7. Metodo, ventana y condiciones
- 8. Volver

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Formula de Fourier

Línea 8593 · `hp.menu.uifouriercontinuous.formula-de-fourier.1`

- 1. Completa: tablas y CAS
- 2. Integral de la ventana (CAS)
- 3. Formula numerica de los graficos
- 4. Volver

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Título calculado

Línea 8731 · `hp.menu.uifouriercontinuous.dynamic.3`

- 1. Tabla de coeficientes c[k]
- 2. Magnitud por armonico
- 3. Fase en radianes
- 4. Formulas Textbook y c[0]
- 5. Ver expresion de entrada
- 6. Suma parcial de Fourier
- 7. Exportar coeficientes
- 8. Parametros e interpretacion
- 9. Editar parametros
- 10. Volver

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Formulas de la serie

Línea 8737 · `hp.menu.uifouriercontinuous.formulas-de-la-serie.1`

- 1. Suma parcial explicita xK(t)
- 2. Coeficiente general c[k] (CAS)
- 3. Valor medio c[0] numerico
- 4. Volver

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UIFourierContinuous · Editar serie por expresion

Línea 8837 · `hp.menu.uifouriercontinuous.editar-serie-por-expresion.1`

- 1. Expresion x(t) con X
- 2. Periodo T
- 3. Armonicos K
- 4. Precision N
- 5. Volver al resultado

Rutas relacionadas: `tool.fourier_symbolic.0`, `tool.fourier_symbolic.1`, `tool.fourier.1`, `tool.fourier.3`, `tool.fourier.4`
Estado: pendiente de auditoría por opción.

## UI_TRANSFORMS · Transformadas Laplace y Z

Línea 8868 · `hp.menu.ui-transforms.transformadas-laplace-y-z.1`

- 1. Laplace directa: x(t) a X(s)
- 2. Laplace inversa: X(s) a x(t)
- 3. Transformada Z de secuencia
- 4. Z inversa: X(z) a x[n]
- 5. Resolver una EDO simbolica
- 6. Bilineal: H(s) a H(z)
- 7. Teoria, convergencia y ROC
- 8. Volver al inicio

Rutas relacionadas: `tool.symbolic.0`, `tool.symbolic.1`
Estado: pendiente de auditoría por opción.

## UIDFT · Fourier discreta

Línea 8913 · `hp.menu.uidft.fourier-discreta.1`

- 1. DFT directa
- 2. DFT inversa
- 3. DTFT de expresion o lista finita
- 4. DTFT simbolica: senal completa
- 5. Volver

Rutas relacionadas: `tool.dtft_symbolic.0`, `tool.basic.dft`, `tool.basic.idft`, `tool.fourier.0`
Estado: pendiente de auditoría por opción.

## UIDFT · Entrada Fourier discreta

Línea 8922 · `hp.menu.uidft.entrada-fourier-discreta.1`

- 1. Lista o banco de datos
- 2. Expresion matematica x[n]
- 3. Volver

Rutas relacionadas: `tool.dtft_symbolic.0`, `tool.basic.dft`, `tool.basic.idft`, `tool.fourier.0`
Estado: pendiente de auditoría por opción.

## UIDFT · DTFT cancelada

Línea 8957 · `hp.menu.uidft.dtft-cancelada.1`

- 1. Reintentar: mismos datos
- 2. Volver sin calcular

Rutas relacionadas: `tool.dtft_symbolic.0`, `tool.basic.dft`, `tool.basic.idft`, `tool.fourier.0`
Estado: pendiente de auditoría por opción.

## UIDFT · Título calculado

Línea 8971 · `hp.menu.uidft.dynamic.1`

Lista construida en ejecución: requiere revisar su construcción.


Rutas relacionadas: `tool.dtft_symbolic.0`, `tool.basic.dft`, `tool.basic.idft`, `tool.fourier.0`
Estado: pendiente de auditoría por opción.

## UIDFT · Unidades del espectro

Línea 8974 · `hp.menu.uidft.unidades-del-espectro.1`

- 1. w rad/muestra
- 2. Hz: indicar Ts en segundos
- 3. Volver

Rutas relacionadas: `tool.dtft_symbolic.0`, `tool.basic.dft`, `tool.basic.idft`, `tool.fourier.0`
Estado: pendiente de auditoría por opción.

## UIDFT · Analisis de fase

Línea 8984 · `hp.menu.uidft.analisis-de-fase.1`

- 1. Fase desenrollada
- 2. Retardo de grupo (muestras)
- 3. Volver

Rutas relacionadas: `tool.dtft_symbolic.0`, `tool.basic.dft`, `tool.basic.idft`, `tool.fourier.0`
Estado: pendiente de auditoría por opción.

## UIDFT · Calculo cancelado

Línea 9051 · `hp.menu.uidft.calculo-cancelado.1`

- 1. Reintentar: mismos datos
- 2. Volver sin calcular

Rutas relacionadas: `tool.dtft_symbolic.0`, `tool.basic.dft`, `tool.basic.idft`, `tool.fourier.0`
Estado: pendiente de auditoría por opción.

## UIDiscreteFourierSeries · Entrada serie discreta

Línea 9070 · `hp.menu.uidiscretefourierseries.entrada-serie-discreta.1`

- 1. Lista o banco: un periodo
- 2. Expresion x[n]: un periodo
- 3. Volver

Rutas relacionadas: `tool.fourier.5`
Estado: pendiente de auditoría por opción.

## UISpectrum · Densidades espectrales

Línea 9147 · `hp.menu.uispectrum.densidades-espectrales.1`

- 1. Energia: secuencia discreta
- 2. Energia: expresion continua
- 3. Periodograma con ventana (PSD)
- 4. Volver

Rutas relacionadas: `tool.fourier.6`, `tool.fourier.7`
Estado: pendiente de auditoría por opción.

## UISpectrum · Entrada de energia espectral

Línea 9171 · `hp.menu.uispectrum.entrada-de-energia-espectral.1`

- 1. Lista o datos exportados
- 2. Expresion discreta
- 3. Volver

Rutas relacionadas: `tool.fourier.6`, `tool.fourier.7`
Estado: pendiente de auditoría por opción.

## UISpectrum · Título calculado

Línea 9229 · `hp.menu.uispectrum.dynamic.1`

- 1. Grafico de Psi(w)
- 2. Tabla de Psi(w)
- 3. Formula del registro o modelo
- 4. Energia y comparacion Parseval
- 5. Consultar entrada
- 6. Tabla compleja X(w)
- 7. Exportar Psi(w)
- 8. Metodo, unidades y limites
- 9. Volver

Rutas relacionadas: `tool.fourier.6`, `tool.fourier.7`
Estado: pendiente de auditoría por opción.

## UISpectrum · Metodo espectral

Línea 9270 · `hp.menu.uispectrum.metodo-espectral.1`

- 1. Periodograma anterior: |DFT|^2/N
- 2. PSD calibrada: un segmento
- 3. PSD Welch: promedio de segmentos
- 4. Volver

Rutas relacionadas: `tool.fourier.6`, `tool.fourier.7`
Estado: pendiente de auditoría por opción.

## UISpectrum · Continua en la PSD

Línea 9288 · `hp.menu.uispectrum.continua-en-la-psd.1`

- 1. Conservar media (incluye DC)
- 2. Restar media de cada segmento
- 3. Cancelar

Rutas relacionadas: `tool.fourier.6`, `tool.fourier.7`
Estado: pendiente de auditoría por opción.

## UISpectrum · Ventana espectral

Línea 9291 · `hp.menu.uispectrum.ventana-espectral.1`

- 1. Rectangular
- 2. Hann
- 3. Hamming
- 4. Blackman
- 5. Kaiser

Rutas relacionadas: `tool.fourier.6`, `tool.fourier.7`
Estado: pendiente de auditoría por opción.

## UISpectrum · Título calculado

Línea 9326 · `hp.menu.uispectrum.dynamic.2`

- 1. Grafico PSD
- 2. Tabla PSD
- 3. Exportar PSD
- 4. Metodo y potencia
- 5. Volver

Rutas relacionadas: `tool.fourier.6`, `tool.fourier.7`
Estado: pendiente de auditoría por opción.

## UISpectrum · Título calculado

Línea 9345 · `hp.menu.uispectrum.dynamic.3`

- 1. Magnitud DFT
- 2. Periodograma
- 3. Tabla compleja DFT
- 4. Tabla periodograma
- 5. Exportar periodograma
- 6. Escala e interpretacion
- 7. Volver

Rutas relacionadas: `tool.fourier.6`, `tool.fourier.7`
Estado: pendiente de auditoría por opción.

## UIConvDFT · Tipo de convolucion DFT

Línea 9376 · `hp.menu.uiconvdft.tipo-de-convolucion-dft.1`

- 1. Lineal por DFT
- 2. Circular

Rutas relacionadas: `tool.basic.circular`
Estado: pendiente de auditoría por opción.

## UIFreqResponse · Título calculado

Línea 9402 · `hp.menu.uifreqresponse.dynamic.1`

- 1. Magnitud lineal
- 2. Fase en radianes
- 3. Magnitud en dB
- 4. Funcion H(z) Textbook
- 5. Tabla compleja H(e^jw)
- 6. Editar H(z)
- 7. Fase desenrollada
- 8. Retardo de grupo
- 9. Volver

Rutas relacionadas: `tool.systems.4`
Estado: pendiente de auditoría por opción.

## UI_FOURIER · Fourier: series y transformadas

Línea 9421 · `hp.menu.ui-fourier.fourier-series-y-transformadas.1`

- 1. Serie de Fourier continua
- 2. Serie de Fourier discreta
- 3. Transformada continua directa
- 4. Transformada continua inversa
- 5. Fourier discreta: DFT y DTFT
- 6. Densidad de energia y PSD
- 7. Convolucion y correlacion
- 8. Teoria y propiedades de Fourier
- 9. Volver al inicio

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## UI_FOURIER · Operaciones de Fourier

Línea 9429 · `hp.menu.ui-fourier.operaciones-de-fourier.1`

- 1. Convolucion lineal o circular
- 2. Correlacion y autocorrelacion
- 3. Volver

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## UINyquist · Nyquist y aliasing

Línea 9479 · `hp.menu.uinyquist.nyquist-y-aliasing.1`

- 1. Criterio de banda y alias
- 2. Laboratorio visual de un tono
- 3. Volver

Rutas relacionadas: `tool.sampling.1`
Estado: pendiente de auditoría por opción.

## UINyquist · Título calculado

Línea 9493 · `hp.menu.uinyquist.dynamic.1`

- 1. Criterio de banda
- 2. Alias del tono
- 3. Valores y formulas
- 4. Supuestos
- 5. Volver

Rutas relacionadas: `tool.sampling.1`
Estado: pendiente de auditoría por opción.

## UINyquist · Título calculado

Línea 9558 · `hp.menu.uinyquist.dynamic.2`

- 1. Resumen y diagnostico
- 2. Graficos individuales
- 3. Muestras y exportacion
- 4. Comparar senales
- 5. Editar tono y muestreo
- 6. Filtro antialias RC
- 7. Volver

Rutas relacionadas: `tool.sampling.1`
Estado: pendiente de auditoría por opción.

## UINyquist · Graficos de aliasing

Línea 9563 · `hp.menu.uinyquist.graficos-de-aliasing.1`

- 1. Tono original
- 2. Tono alias
- 3. Entrada al muestreador
- 4. Reconstruccion SINC
- 5. Error SINC - original
- 6. Espectros de lineas
- 7. Volver

Rutas relacionadas: `tool.sampling.1`
Estado: pendiente de auditoría por opción.

## UINyquist · Diagnostico de aliasing

Línea 9578 · `hp.menu.uinyquist.diagnostico-de-aliasing.1`

- 1. Resumen del muestreo
- 2. Datos del tono
- 3. Filtro y senal muestreada
- 4. Interpretar el alias
- 5. SINC y error
- 6. Interpretar los espectros
- 7. Volver

Rutas relacionadas: `tool.sampling.1`
Estado: pendiente de auditoría por opción.

## UINyquist · Comparaciones del laboratorio

Línea 9604 · `hp.menu.uinyquist.comparaciones-del-laboratorio.1`

- 1. Original y alias
- 2. Original y SINC
- 3. Original y filtrada analogica
- 4. Muestras sin y con filtro
- 5. Filtrada analogica y SINC
- 6. Volver

Rutas relacionadas: `tool.sampling.1`
Estado: pendiente de auditoría por opción.

## UINyquist · Editar un parametro

Línea 9615 · `hp.menu.uinyquist.editar-un-parametro.1`

- 1. Frecuencia f (Hz)
- 2. Amplitud A
- 3. Fase phi (rad)
- 4. Cantidad de muestras N
- 5. Periodo Ts (s)
- 6. Volver al resultado

Rutas relacionadas: `tool.sampling.1`
Estado: pendiente de auditoría por opción.

## UINyquist · Filtro antes de muestrear

Línea 9621 · `hp.menu.uinyquist.filtro-antes-de-muestrear.1`

- 1. Sin filtro
- 2. Cascada analogica RC
- 3. Volver

Rutas relacionadas: `tool.sampling.1`
Estado: pendiente de auditoría por opción.

## UIRateChange · Cambio de tasa

Línea 9668 · `hp.menu.uiratechange.cambio-de-tasa.1`

- 1. Diezmar
- 2. Expandir con ceros
- 3. Interpolacion lineal
- 4. Interpolacion SINC
- 5. Retenedor orden cero

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## UIRateChange · Entrada x[n]

Línea 9670 · `hp.menu.uiratechange.entrada-x-n.1`

- 1. Secuencia finita
- 2. Expresion matematica x[n]

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## UIRateChange · SINC cancelada

Línea 9713 · `hp.menu.uiratechange.sinc-cancelada.1`

- 1. Reintentar: misma entrada
- 2. Volver sin calcular

Rutas relacionadas: `tool.rational_resampling.0`, `tool.sampling.2`
Estado: pendiente de auditoría por opción.

## UIReconstruction · Metodo D/A

Línea 9740 · `hp.menu.uireconstruction.metodo-d-a.1`

- 1. Retenedor de orden cero
- 2. Interpolacion lineal
- 3. Interpolacion SINC

Rutas relacionadas: `tool.sampling.3`
Estado: pendiente de auditoría por opción.

## UIReconstruction · SINC cancelada

Línea 9749 · `hp.menu.uireconstruction.sinc-cancelada.1`

- 1. Reintentar: misma entrada
- 2. Volver sin calcular

Rutas relacionadas: `tool.sampling.3`
Estado: pendiente de auditoría por opción.

## UIReconstruction · Título calculado

Línea 9755 · `hp.menu.uireconstruction.dynamic.1`

- 1. Grafico de entrada
- 2. Grafico reconstruido
- 3. Tabla de salida
- 4. Exportar salida
- 5. Metodo y resolucion
- 6. Volver

Rutas relacionadas: `tool.sampling.3`
Estado: pendiente de auditoría por opción.

## UIQuantization · Niveles de cuantizacion

Línea 9801 · `hp.menu.uiquantization.niveles-de-cuantizacion.1`

- 1. Sin offset: rango original
- 2. Con offset: nivel en 0

Rutas relacionadas: `tool.sampling.4`
Estado: pendiente de auditoría por opción.

## UIQuantization · Metodo de cuantizacion

Línea 9803 · `hp.menu.uiquantization.metodo-de-cuantizacion.1`

- 1. Redondeo
- 2. Truncamiento

Rutas relacionadas: `tool.sampling.4`
Estado: pendiente de auditoría por opción.

## UIFixedPoint · Metodo de punto fijo

Línea 9829 · `hp.menu.uifixedpoint.metodo-de-punto-fijo.1`

- 1. Redondeo
- 2. Truncamiento

Rutas relacionadas: `tool.sampling.5`
Estado: pendiente de auditoría por opción.

## UI_SAMPLING · Muestreo, conversion A/D y D/A

Línea 9841 · `hp.menu.ui-sampling.muestreo-conversion-a-d-y-d-a.1`

- 1. Muestrear: x(t) a x[n]
- 2. Analizar Nyquist y aliasing
- 3. Diezmar, expandir o interpolar
- 4. Reconstruir: x[n] a x(t)
- 5. Cuantizar y calcular SNR
- 6. Representar en punto fijo
- 7. Conceptos de conversion A/D y D/A
- 8. Volver al inicio

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## SSDigitalFilterResults · Título calculado

Línea 9903 · `hp.menu.ssdigitalfilterresults.dynamic.1`

- 1. Funcion matematica H(z)
- 2. Caracteristicas
- 3. Implementacion digital
- 4. Coeficientes b y a
- 5. Respuesta al impulso
- 6. Modulo lineal
- 7. Fase
- 8. Magnitud en dB
- 9. Polos y ceros
- 10. Editar H(z)
- 11. Fase desenrollada
- 12. Retardo de grupo
- 13. Volver

Rutas relacionadas: `tool.systems.0`, `tool.systems.1`
Estado: pendiente de auditoría por opción.

## SSDigitalFilterResults · Coeficientes del filtro

Línea 9925 · `hp.menu.ssdigitalfilterresults.coeficientes-del-filtro.1`

- 1. Numerador b[k]
- 2. Denominador a[k]
- 3. Exportar b[k]
- 4. Exportar a[k]
- 5. Volver

Rutas relacionadas: `tool.systems.0`, `tool.systems.1`
Estado: pendiente de auditoría por opción.

## UIFIRDesign · FIR ideal

Línea 9952 · `hp.menu.uifirdesign.fir-ideal.1`

- 1. Pasa bajos
- 2. Pasa altos
- 3. Pasa banda
- 4. Rechaza banda

Rutas relacionadas: `tool.systems.0`
Estado: pendiente de auditoría por opción.

## UIFIRDesign · Ventana FIR

Línea 9969 · `hp.menu.uifirdesign.ventana-fir.1`

- 1. Rectangular
- 2. Hann
- 3. Hamming
- 4. Blackman
- 5. Kaiser

Rutas relacionadas: `tool.systems.0`
Estado: pendiente de auditoría por opción.

## UIBiquadDesign · IIR biquad

Línea 9993 · `hp.menu.uibiquaddesign.iir-biquad.1`

- 1. Pasa bajos
- 2. Pasa altos
- 3. Pasa banda
- 4. Notch / rechaza

Rutas relacionadas: `tool.systems.1`
Estado: pendiente de auditoría por opción.

## SSAnalogFilterResults · Título calculado

Línea 10038 · `hp.menu.ssanalogfilterresults.dynamic.1`

- 1. Funcion matematica H(s)
- 2. Caracteristicas
- 3. Componentes y topologia
- 4. Modulo lineal
- 5. Fase lineal
- 6. Bode magnitud
- 7. Polos y ceros
- 8. Volver

Rutas relacionadas: `tool.systems.2`
Estado: pendiente de auditoría por opción.

## UIAnalogRCDesign · Diseno analogico RC

Línea 10073 · `hp.menu.uianalogrcdesign.diseno-analogico-rc.1`

- 1. Pasa bajos RC
- 2. Pasa altos RC
- 3. Volver

Rutas relacionadas: `tool.systems.2`
Estado: pendiente de auditoría por opción.

## UIAnalogRCDesign · Componente conocido

Línea 10074 · `hp.menu.uianalogrcdesign.componente-conocido.1`

- 1. Fijar resistencia R
- 2. Fijar capacitor C
- 3. Volver

Rutas relacionadas: `tool.systems.2`
Estado: pendiente de auditoría por opción.

## UI_FILTERS · Filtros analogicos y digitales

Línea 10109 · `hp.menu.ui-filters.filtros-analogicos-y-digitales.1`

- 1. Disenar FIR por ventanas
- 2. Disenar IIR biquad
- 3. Disenar filtro analogico RC
- 4. Filtrar una senal con b/a
- 5. Respuesta digital H(e^jw)
- 6. Polos/ceros: analizar o disenar
- 7. Transformacion bilineal H(s)-H(z)
- 8. Teoria y estructuras de filtros
- 9. Volver

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## UISecondOrder · Título calculado

Línea 10164 · `hp.menu.uisecondorder.dynamic.1`

- 1. Parametros y polos
- 2. Respuesta al escalon
- 3. Funcion H(s)
- 4. Volver

Rutas relacionadas: `tool.systems.8`, `tool.systems.9`
Estado: pendiente de auditoría por opción.

## UIBodeContinuous · Título calculado

Línea 10191 · `hp.menu.uibodecontinuous.dynamic.1`

- 1. Magnitud en dB
- 2. Fase en radianes
- 3. Funcion H(s) Textbook
- 4. Tabla compleja H(jw)
- 5. Editar H(s)
- 6. Cambiar intervalo
- 7. Fase desenrollada
- 8. Retardo de grupo (s)
- 9. Volver

Rutas relacionadas: `tool.systems.4`
Estado: pendiente de auditoría por opción.

## UIFreqResponseContinuousLinear · Título calculado

Línea 10241 · `hp.menu.uifreqresponsecontinuouslinear.dynamic.1`

- 1. Magnitud lineal
- 2. Fase en radianes
- 3. Funcion y coeficientes
- 4. Tabla compleja H(jw)
- 5. Editar H(s)
- 6. Cambiar rango y resolucion
- 7. Fase desenrollada
- 8. Retardo de grupo (s)
- 9. Volver

Rutas relacionadas: `tool.systems.4`
Estado: pendiente de auditoría por opción.

## UIFeedback · Título calculado

Línea 10284 · `hp.menu.uifeedback.dynamic.1`

- 1. Valores y estabilidad
- 2. Diagrama polos / ceros
- 3. Funcion de lazo cerrado
- 4. Cambiar K
- 5. Volver

Rutas relacionadas: `tool.systems.10`
Estado: pendiente de auditoría por opción.

## UIRootLocus · Título calculado

Línea 10309 · `hp.menu.uirootlocus.dynamic.1`

- 1. Ver lugar de raices
- 2. Transferencia de la planta
- 3. Rango de K y resolucion
- 4. Volver

Rutas relacionadas: `tool.systems.11`
Estado: pendiente de auditoría por opción.

## UI_CONTROL · Sistemas y control

Línea 10322 · `hp.menu.ui-control.sistemas-y-control.1`

- 1. Respuesta de segundo orden
- 2. Respuesta lineal H(jw)
- 3. Diagramas de Bode H(jw)
- 4. Respuesta discreta H(e^jw)
- 5. Realimentacion unitaria
- 6. Lugar de raices
- 7. Polos, ceros y estabilidad
- 8. Teoria de sistemas y control
- 9. Volver

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## UITheory · Teoria por programa

Línea 10343 · `hp.menu.uitheory.teoria-por-programa.1`

- 1. Sistemas I: ejes 1-4
- 2. Sistemas I: Fourier
- 3. Sistemas I: muestreo/control
- 4. Sistemas II: procesamiento
- 5. Sistemas II: espectro
- 6. Sistemas II: filtros
- 7. Formulas clave
- 8. Instrucciones de uso
- 9. Volver

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.

## UIAbout · SignalLab 5.0

Línea 10363 · `hp.menu.uiabout.signallab-5-0.1`

- 1. Novedades y limites
- 2. Ultima operacion registrada
- 3. Limpiar contexto temporal
- 4. Volver

Sin ruta relacionada en el catálogo actual.
Estado: pendiente de auditoría por opción.
