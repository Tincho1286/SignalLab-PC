# Matriz de migración HP → Python → prueba → estado

Referencia fija: SignalLab 5.0 en `C:/Users/lesca/Documents/Software_Apps/SignalLab Hp Prime`, revisión 21/10/2026, SHA-256 `9EC7E69183AC50303A4EF0FDFAFD4B585F33D75D2164AE725E95574A75033DCB`. El proyecto PC conserva una copia de referencia congelada en `references/SignalLab_App_5.0.hppl`. Las opciones se cotejaron con el código completo y la guía HP. El catálogo de 109 menús estáticos y opciones está en `INVENTARIO_HP.md`; los puntos de entrada UI en `PUNTOS_ENTRADA_HP.txt`.

**Actualización 0.10:** ver `AVANCE_0_10.md` y `OBJETIVO_LABORATORIO_PC.md`. La suite actual tiene 97 pruebas aprobadas; ese resultado no demuestra paridad de las filas pendientes. Los estados históricos se actualizan sólo donde existe evidencia nueva.

**Estado**: Implementado = el alcance completo de esa fila funciona en PC; Parcial = sólo algunas de las funciones listadas están portadas; Pendiente = sólo inventariado. Una fila parcial o pendiente nunca anuncia paridad completa.

| Módulo / opción HP Prime 5.0 | Código Python PC | Prueba o caso independiente | Estado |
|---|---|---|---|
| Señales · crear secuencia x[n] (impulso, escalón, rampa, exponencial, seno, pulso, expresión) | `engine; plantillas UI` | Validación 0.2 pendiente | Parcial: Plantillas de generadores agregadas; estados especiales y validación pendientes |
| Señales · expresión o señal por tramos, muestreo y edición | `engine.evaluate_expression; sampling.sample_expression` | Validación 0.2 pendiente | Parcial: Tramos y muestreo agregados; estados especiales y validación pendientes |
| Señales · desplazar, invertir, escalar, sumar, par/impar | `operations.shift`, `reverse`, `scale_amplitude`, `add_sequences`, `even_odd_parts`; UI | `tests/test_migrated_operations.py` | Implementado: registros finitos discretos, ejes enteros |
| Señales · energía y potencia de lista/expresión/teoría, RMS y densidad | `operations.finite_measures`, `measures_symbolic`, `ExpressionMeasuresPanel` | `test_expression_measures`, `test_toolbox`: definición → ventana → Fourier | Parcial: expresiones por intervalo, globales y periódicas con condiciones; falta auditoría completa HP de densidad y estados especiales |
| Sistemas LTI · convolución discreta/continua | `operations.linear_convolution`, `continuous.convolution`, CAS `continuous_convolution`; menús y proyecto | `test_migrated_operations`, `test_continuous`, `test_toolbox`; cuadratura independiente y casos algebraicos | Parcial: discreta, continua de interpolantes lineales finitos y expresiones causales/bilaterales incorporadas; falta auditoría del alcance HP completo y estados especiales |
| Sistemas LTI · correlación cruzada/auto, lineal/circular/periódica/normalizada | `operations.correlation`, `continuous.correlation/periodic_correlation`, CAS y menús dedicados | `test_correlation_variants`, `test_toolbox`: orígenes, suma, cuadratura, complejo, escalas y UI | Parcial: familias discretas/continuas, periódicas y ruta algebraica accesibles; quedan funciones generales/distribuciones y cotejo completo de casos HP |
| Sistemas LTI · resolver ecuación en diferencias | `filters.Transfer.apply`; panel LTI | `test_filters.py`, recurrencia analítica y condiciones iniciales | Parcial: registros finitos; estados N/D pendientes |
| Sistemas LTI · respuestas impulso/escalón | `Transfer.excitation_response`; panel LTI | primer orden contra solución cerrada; prueba UI | Parcial: digital en reposo; continuo pendiente |
| Sistemas LTI · coeficientes, polos/ceros y estabilidad | `Transfer`, `from_poles_zeros`; panel LTI | retardo puro, polos dentro/fuera, límite 0/0 | Parcial: análisis y diseño por coordenadas; editor gráfico pendiente |
| Transformadas · Laplace directa/inversa, expresiones y listas | `symbolic.py; panel CAS` | Validación 0.2 pendiente | Parcial: Unilateral/causal; bilateral y listas temporales pendientes |
| Transformadas · Z directa/inversa, región de convergencia | `symbolic.py; panel CAS` | Validación 0.2 pendiente | Parcial: Z finita y expansión racional derecha; otros soportes/ROC pendientes |
| Transformadas · EDO simbólica y bilineal H(s)→H(z) | `symbolic.py; filters.bilinear` | Validación 0.2 pendiente | Parcial: EDO constante con condiciones iniciales; EDO general pendiente |
| Transformadas · teoría, propiedades y Textbook | Pendiente | `SYM-01` pendiente | Pendiente |
| Fourier · series continua/discreta y trenes de pulso/Dirac | `fourier.py; panel Fourier` | Validación 0.2 pendiente | Parcial: Series numéricas y síntesis; trenes ideales pendientes |
| Fourier · CTFT/ICTFT simbólica y numérica | `fourier.ctft, ictft`; CAS angular y `SymbolicFourierPanel` | `test_symbolic_fourier`: pares, desplazamiento, inversa; `test_toolbox`: expresión → muestras → inversa numérica | Parcial: directa/inversa algebraicas añadidas con condiciones; faltan cobertura completa HP y distribuciones generales |
| Fourier · DFT/IDFT/serie discreta | `operations.dft`, `idft`; UI en worker | `DFT-01`, `IDFT-01`; `tests/test_migrated_operations.py` | Parcial: DFT/IDFT finitas; series discretas pendientes |
| Fourier · DTFT finita y simbólica, superposición DFT/DTFT | `fourier.dtft`, `FourierPanel.compare`; CAS `dtft_expression` | `test_symbolic_fourier`: suma compleja finita, geométricas derecha/izquierda, caso divergente; `test_toolbox`: unidades | Parcial: DTFT algebraica finita y series convergentes incorporadas; faltan auditoría completa y distribuciones periódicas |
| Fourier · magnitud/fase, fase desenrollada, retardo y espectros | `FourierPanel._accept` | Validación 0.2 pendiente | Parcial: Vistas numéricas; estados especiales y vistas HP completas pendientes |
| Fourier · densidad de energía, periodograma, PSD calibrada/Welch | `fourier.energy_density, spectral_density` | Validación 0.2 pendiente | Parcial: Motores y UI agregados; auditoría de escalas pendiente |
| Fourier · convolución lineal/circular y correlación | `operations.circular_convolution`, `correlation`; rutas UI | Validación nueva pendiente | Parcial: variantes discretas incorporadas |
| Muestreo A/D · muestrear expresión t0, Ts, N y editar | `sampling.sample_expression; SamplingPanel` | Validación 0.2 pendiente | Parcial: Muestras y reloj físico; estados especiales pendientes |
| Muestreo A/D · Nyquist, aliasing, laboratorio y diagnóstico | `sampling.alias_frequency` | Validación 0.2 pendiente | Parcial: Alias de tono; laboratorio completo pendiente |
| Muestreo A/D · diezmar, expansión, interp. lineal/SINC, ZOH | `sampling.resample`, `resample_rational`; menú con FIR Kaiser configurable | `test_rational_resampling`: suma FIR explícita, reloj, aliasing; `test_toolbox`: proyecto/UI | Parcial: conversión racional con antialias incorporada; quedan auditoría completa HP y banco de pruebas de los métodos anteriores |
| Muestreo A/D · reconstrucción D/A ZOH/lineal/SINC | `sampling.reconstruct` | Validación 0.2 pendiente | Parcial: Intervalo del registro; ventana arbitraria pendiente |
| Muestreo A/D · cuantización, SNR por intervalo y punto fijo | `sampling.quantize, fixed_point` | Validación 0.2 pendiente | Parcial: Cuantización/SNR y punto fijo exacto agregados; comparación gráfica y validación pendientes |
| Filtros · FIR ventana, biquad IIR, RC analógico | `filters.fir`, `biquad`, `rc`; panel | `test_filters.py`: sinc, pico Q, esquina RC | Parcial: diseños operativos; RC por fc y componente conocido agregado, validación pendiente |
| Filtros · aplicar b/a, respuesta, polos y ceros | `Transfer`; panel con gráficos y CSV | recurrencia, retardo, polos y cancelación exacta | Parcial: falta editor gráfico HP y estados especiales en filtrado |
| Filtros · bilineal, estructuras y teoría | `filters.bilinear`; panel | H(s)=1/(s+1), T=1 contra resultado exacto | Parcial: bilineal numérica; estructuras/teoría pendientes |
| Control · segundo orden, H(jw), Bode y H(e^jw) | `control.second_order, analog_response; SystemsPanel` | Validación 0.2 pendiente | Parcial: Motores y vistas agregados; auditoría de métricas y validación pendientes |
| Control · realimentación, lugar de raíces, estabilidad | `control.feedback, root_locus; Transfer.stability` | Validación 0.2 pendiente | Parcial: Lazo y locus finitos; auditoría de singularidades y validación pendientes |
| Teoría · conceptos, fórmulas e instrucciones por módulo | `theory_data, TheoryPanel` | Validación 0.2 pendiente | Parcial: 20 secciones estáticas; ayuda dinámica y adaptación PC pendientes |
| Historial/recientes, banco y guardar/recuperar salidas | `project.Project`, selección en entradas y sistemas; JSON de proyecto con procedencia | `test_project`, `test_toolbox`; recorridos guardados en work/project-preview y work/continuous-preview | Parcial: banco persistente y procedencia incorporados; persistencia de toda la sesión y cobertura homogénea de informes pendientes |
| Tablas y gráfico con cursor/zoom | `SignalEditorPanel`: tabla compleja paginada, origen/paso y nuevos objetos; toolbar Matplotlib | `test_toolbox`: edición de página posterior, original inmutable, borrador persistido | Parcial: editor recuperado en UI actual; falta cursor especializado y comparación por componentes |
| Exportación e importación | `storage.save_json/load_json/save_csv` | `JSON-01`, `CSV-01` | Parcial: formatos PC propios, sin exportación HP Home/banco |
| UI: dashboard, menús completos, ayuda, guardado y navegación | catálogo de 8 módulos + rutas inventariadas | revisión manual de navegación pendiente | Parcial: lista completa de primer nivel; rutas no implementadas muestran pendiente |

## Convenciones heredadas que condicionan cada port

1. No tratar una lista finita como señal infinita/periódica sin declarar el modelo.
2. Separar expresión exacta, aproximación numérica y dibujo de ventana.
3. Frecuencia angular en rad/s o rad/muestra no es Hz; informar conversión y Ts.
4. DFT HP: suma sin dividir N; IDFT divide N; serie discreta c[k]=DFT/N. Cualquier API usada debe normalizarse explícitamente.
5. N/D y datos inválidos no se convierten en cero; no unir huecos como si probara continuidad.
6. Índices de secuencias son enteros. Ejes importados guardan origen y paso.
7. Impulso de Kronecker discreto es diferente de la distribución Dirac continua, cuya amplitud de línea se relaciona con el área.
8. Limpieza visual no cambia ni tabla original ni archivo exportado; fase de cero es N/D.
9. Transformada simbólica sin resultado probado debe identificarse como pendiente/no resuelta.
10. No copiar defectos HP: verificar independientemente ecuaciones y ejemplos.

## Próximo lote de regresión

Casos de `PRUEBAS.md` incluyen DFT con lista modificada después de elegir N, IDFT negativa, impulso discreto, convolución con índices negativos, PSD integrada de constante, remuestreo con origen/paso, filtros con tolerancia de cancelación, bilineal y respuestas de retardo. Cada caso requiere fórmula, unidades, resultado esperado y estado separado para HP y PC; el JSON inicial contiene sólo las entradas de prueba ya definidos para el flujo implementado y los principales contratos que guiarán portados siguientes.

### Incorporaciones pendientes de validación

Correlación discreta auto/cruzada, circular, normalizada por energía y promedio periódico; convolución circular HP. Motor en operations.py y rutas UI en LTI/Fourier. Aún no se consideran filas completas: faltan validación y variantes continuas.

## Ampliaciones 0.2 adicionales

- sampling.quantize/fixed_point: cuantización, SNR y punto fijo exacto; validación pendiente.
- control.py y panel Filtros/LTI: segundo orden, respuesta continua, realimentación y locus; validación pendiente.
- theory_data.py/theory_panel.py: 20 secciones estáticas importadas; ayuda contextual dinámica pendiente.
- jobs.py y symbolic_process.py: cancelación y proceso CAS aislado; validación pendiente.

Ampliación PC 0.10: espacio de estados MIMO numérico, conversión y discretización. No reemplaza el cierre pendiente de las filas HP ni demuestra análisis matricial algebraico.

## Inventario reproducible y contrato de intercambio
El inventario histórico de 109 menús era parcial: el escaneo léxico encuentra 157 llamadas SSMenu (110 títulos literales), 751 expresiones de opción, siete textos calculados y cinco listas dinámicas. No son 751 funciones ni prueba de migración. Detalle en INVENTARIO_REPRODUCIBLE_HP.md. Catálogo de 57 rutas PC, esquema de capacidades 1 y comparación bidireccional verificados por test_capabilities.py. Suite actual: 113 pruebas aprobadas (work/regression-capabilities.txt). Las filas pendientes mantienen su estado.

## Incremento 0.12
Medidas de expresiones y sus ventanas numéricas vinculadas; ver AVANCE_0_12.md. El nuevo alcance no declara resueltos todos los casos simbólicos ni todas las filas de esta matriz.
