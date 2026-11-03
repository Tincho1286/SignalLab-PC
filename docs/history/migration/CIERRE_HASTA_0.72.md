# Cierre de SignalLab 1.0 · estado vigente

Actualización: 27/10/2026, base 0.72. Este documento reemplaza el orden histórico de cierre de PENDIENTES_PRIMERA_ESTABLE.md. El objetivo sigue siendo la primera estable, no una certificación de que resuelve cualquier ejercicio o expresión matemática.

## Alcance acordado


## Evidencia reciente de cálculo y funcionalidad

| Área | Evidencia concreta | Alcance de la evidencia |
|---|---|---|
| Retardo de grupo | 0.58: retardo puro, primer orden analógico/digital, complejo, SOS, singularidades y gráfica | Corregida la dependencia errónea del desenrollado sobre una rejilla gruesa; no certifica toda la respuesta frecuencial. |
| Densidad de energía | 0.59: Parseval complejo, rejilla insuficiente, suma DFT e informe | Distingue banda finita, período completo y muestras DFT; rechaza deltas y densidades como entrada X. |
| Síntesis de series | 0.59: reconstrucciones manuales continua/discreta y entrada preservada | Corregido el fallo que impedía calcular coeficientes propios. |
| Importación | 0.57: MAT clásico/HDF5, M numérico, complejos, ejes y canales | No es un intérprete MATLAB completo; límites declarados en el diálogo. |
| Diseño analógico | 0.55: cuatro familias en cuatro tipos de banda | Transferencias y exportación; no síntesis física general. |
| Muestreo pasabanda | 0.56: intervalos, contacto, solapamiento y copia de Fs | Selección de tasas bajo soporte espectral ideal; no simulación física del conversor. |
| Hilbert, STFT y convolución por bloques | 0.54: casos numéricos y apertura de paneles | Registros finitos y convenciones documentadas; no PSD calibrada en STFT. |

## Evidencia añadida en 0.60

- Cascadas SOS: corregida pérdida de representación al copiar y conectar; verificadas contra producto frecuencial y aplicación sucesiva en tiempo. Envío del equivalente a respuesta temporal conserva secciones.
- Condiciones iniciales: caso discreto con memoria e índice negativo frente a recurrencia directa; descomposición total = estado cero + entrada cero. Primer orden continuo desde un instante no nulo frente a fórmula cerrada.
- Relojes: desplazamiento e inversión ahora ajustan el tiempo inicial sin perder Fs. Recorrido con diezmado y reconstrucción verificado.

## Trabajo que permanece abierto

- Revisar de forma dirigida convenciones y recorridos de convolución/correlación, muestreo/cambio de tasa y respuestas con condiciones iniciales. Hay implementación y pruebas históricas; comprobar los puntos de riesgo vigentes antes de afirmar su cierre.
- Dirac, 0.61: Fourier, convolución/correlación continua, transformación temporal y respuesta LTI preservan términos singulares separados. Comprobaciones dirigidas de Fourier, escala, identidad de convolución y respuesta LTI a impulso complejo desplazado. Hilbert/STFT y correlación normalizada rechazan distribuciones; no se declara soporte universal de distribuciones.
- Contrastar el alcance publicado de Laplace/Z y ROC con el motor real: resultados exactos, aproximaciones y casos no resueltos deben distinguirse en pantalla.
- Resolver las inconsistencias concretas de entradas, gráficos y reutilización que aparezcan en esas revisiones.
- Consolidar alcance y limitaciones de la ayuda con las correcciones finales, y generar una candidata 1.0 con comprobación corta de sus recorridos principales.

Los diagramas de realización, compensación módulo–fase, circuitos físicos generales y ampliaciones de aritmética de implementación de inventarios anteriores siguen identificados como posibles ampliaciones de cobertura; no se declaran implementados ni se convierten automáticamente en bloqueos de estabilidad. Las materias completas no quedan certificadas por las comprobaciones anteriores.

No marcar 1.0 únicamente por compilar, pasar un caso o aumentar el número de versión. La evidencia debe cubrir el alcance final declarado y no deben quedar errores críticos conocidos en él.

## Revisión gráfica 0.61

Ejes por significado: índices enteros, tiempo en segundos y frecuencia angular. Resultado común, Fourier, selector de señales, editor, diseño de filtros, respuesta frecuencial y espacio de estados usan esta distinción. La DFT conserva tallos sobre frecuencia; DTFT y respuestas frecuenciales siguen siendo curvas continuas. Comprobación puntual de índices con zoom y DFT en radianes. No equivale a una revisión visual exhaustiva de cada herramienta.

Revisión gráfica adicional: la densidad derivada de una DFT conserva su carácter discreto; los cortes FFT del espectrograma usan tallos. Los centros de ventana pueden tener coordenadas semienteras para ventanas pares: se conservan sin redondear.

## Ajuste de lectura discreta 0.62

Marcas por índice en ambos subgráficos, etiquetas principales espaciadas y lectura del mouse por muestra. Comprobación: 64 índices, eventos reales de movimiento en la barra, valores reales/imaginarios, índices negativos, zoom y preservación de coordenadas continuas en segundos. El gráfico ampliado utiliza los mismos ejes y conserva el comportamiento. La densidad visual de marcas se reduce sólo cuando ya no se distinguen en pantalla; no limita los datos ni los cálculos.

## Ejes conjuntos 0.63

Revisadas las rutas de trazado conjunto: Fourier, FFT/referencias, filtros, resultados compartidos, estados, aliasing y polos/ceros. Corregidos eje independiente del análisis ampliado y límites de comparaciones FFT; añadida validación de unidades. Evidencia y alcance en DESARROLLO_0.63.md.

## Interfaz y filtros ideales 0.64

Figuras de herramientas independientes, controles apilables y conversión de respuestas analógicas ideales. Alcance matemático, límites de soporte y comprobaciones en DESARROLLO_0.64.md. La respuesta digital se reutiliza como H, sin afirmar una realización racional finita.

## Reorganización 0.65

Documento único de filtros con definición por fórmula, respuesta y retardo; conversión ideal a FIR por ventana; polos/ceros binómico/polar; retiro de barrido K; Laplace y Z unificadas. Z incorpora directa por expresión e inversa racional con ROC. Se mantienen límites explícitos de convergencia, cancelaciones, avances y aproximaciones de rejilla. Evidencia y alcance en DESARROLLO_0.65.md.


## Consolidación 0.66

16 documentos públicos con operaciones internas independientes. Análisis de filtros incorpora un plano de polos y ceros de consulta, separado del diseño. Se corrigen envío a formularios ocultos, ayudas duplicadas y dimensiones de opciones inactivas. Evidencia y límites en DESARROLLO_0.66.md. No amplía el alcance académico ni certifica todas las expresiones o ejercicios.


## Interfaz por operaciones 0.67

Catálogo y explorador con ubicación única por operación; seis áreas principales; separación de análisis y diseño; carga rápida de muestras/coeficientes; cálculo común y ajuste de pantallas pequeñas. Detalles y comprobaciones en DESARROLLO_0.67.md. Los motores matemáticos se conservan.


## Un problema por herramienta 0.68

72 variantes agrupadas en 33 herramientas públicas, con dominio y método dentro de la página. Entradas compatibles compartidas entre vistas; destinos de reutilización compactados. Corregidas acciones de cálculo residuales y callbacks de series/RC que perdían sus controles. Evidencia y límites en DESARROLLO_0.68.md. La revisión de organización avanza; no cierra por sí sola los pendientes de estabilidad anteriores.


## Independencia de documentos 0.69

Cada problema público conserva su propio documento; sus variantes siguen agrupadas. Corregida la copia que podía recuperar coeficientes o archivos anteriores. Entradas de series etiquetadas como c[k], con k admitido en expresiones. Evidencia en DESARROLLO_0.69.md. Próxima revisión concreta de presentación: informes de medidas/resultados que aún exponen nombres internos o JSON en vez de una lectura matemática. Permanecen los cierres dirigidos de cálculo anteriores.


## Informes y registros 0.70

Resumen científico común, medidas con fórmulas y condiciones, lectura de resultados conservados y estado de datos modificados. La herramienta de medidas incorpora registros continuos por integración del modelo lineal, sin nuevos menús públicos. Corregidos selectores ocultos al volver de ayuda/resultados y constantes con k interpretado como eje. Evidencia en DESARROLLO_0.70.md. Se resuelve la presentación de las medidas y los resultados comunes revisados; los cierres dirigidos de cálculo y la revisión final del alcance siguen pendientes.


## Navegación y recorridos 0.71

Seis áreas y listas directas; un documento para análisis de sistema y otro para diseño FIR/IIR, con variantes internas. Filtros ideales en análisis y diseño por polos/ceros en diseño. Entrada por fórmula, muestras, archivo o resultado; fórmulas de H visibles en respuesta temporal. Revisados los tamaños 1366, 800 y 640 de los recorridos modificados, con desplazamiento vertical.

Correlación y muestreo recibieron una comprobación dirigida de los contratos documentados en DESARROLLO_0.71.md: conjugación, retardo, normalización continua/periódica, origen común grande y reloj de reconstrucción/cambio de tasa. Se corrige el uso de campos predeterminados al reutilizar una señal con Fs y tiempo inicial conocidos. Esta evidencia reduce el punto de riesgo de esos recorridos; no certifica todo el dominio numérico ni las distribuciones. Continúa pendiente contrastar Laplace/Z y ROC y consolidar la candidata final.


## Cierre dirigido de transformadas y ayuda 0.72

Revisado el contrato implementado de Laplace unilateral/inversa causal y Z por soporte/inversa racional. Se corrigieron variables de operación aceptadas como parámetros, radio de ROC rechazado por tolerancia absoluta y presentación confusa de ramas/sumas pendientes. Las operaciones conservan entradas y resultados separados y las muestras de Z son opcionales. La biblioteca adapta índice y artículo al ancho disponible. Casos, límites y evidencia en DESARROLLO_0.72.md.

La revisión dirigida respalda ese alcance declarado, no transformadas arbitrarias ni Laplace bilateral con ROC seleccionable. Falta consolidar la cobertura académica publicada frente al alcance vigente, retirar contradicciones históricas de la documentación de uso y preparar una candidata de cierre con sus limitaciones concretas. No se reemplaza la revisión general de uso por los casos puntuales anteriores.
