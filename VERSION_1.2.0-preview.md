# SignalLab PC 1.2.0 preliminar

Entrega del 2 de noviembre de 2026. Implementación sobre main de la versión 1.1.3. Se conservan la arquitectura Qt/Python, las entradas independientes y la paleta oscura.

## Cambios incorporados

- Transformada Z tiene Directa e Inversa. La secuencia finita es una entrada de Directa; Inversa permite un intervalo o el soporte completo de un polinomio de Laurent, incluidos índices negativos. Las rutas antiguas siguen dirigiendo a la opción correspondiente.
- Enviar a CAS y Analizar X(z) como H(z) están disponibles de manera uniforme. CAS usa X(z) calculada en la directa y x[n] calculada en la inversa; el análisis usa siempre X(z). Expresiones, condiciones, índices, reloj y ROC registrada acompañan la reutilización compatible.
- Evaluación numérica y simbólica comparten extensiones continuas en singularidades removibles. Se exigen límites laterales finitos e iguales; no se reemplazan polos por cero. sinc conserva la convención normalizada sin(πx)/(πx), con valor 1 en cero. Se admiten desplazamientos, escalas y multiplicación numérica implícita, por ejemplo sinc(2n), sin alterar 1e-3.
- H(z) tiene una vista independiente del plano complejo: mapa de 20 log10|H(z)|, expresión, polos/ceros, círculo unitario y ROC seleccionada. Ambos ejes tienen igual escala. La respuesta en frecuencia se conserva en otra pestaña y sólo se calcula si el círculo unitario pertenece a la ROC elegida.
- Diseño por bandas: amplitud positiva configurable para LP, HP y BP; dos amplitudes independientes para BS FIR. El ideal BS se construye como A1·LP(c1)+A2·HP(c2), antes de enventanar. No se sustituye por una ganancia global.
- Tolerancias absolutas A±δp; relativas A(1±δp); en dB A·10^(±rp/20). El rechazo relativo/en dB toma Aref=max(A de las bandas). Gráficos con ideal, límites y respuesta; aviso persistente si el resultado queda fuera de tolerancias en la rejilla.
- Importador compartido: CSV/TSV, MATLAB .mat/.m y JSON de los formatos existentes; selección exportada de Resultados y expresiones algebraicas JSON. Cada operando numérico puede importar su archivo. Los selectores de Resultados también permiten importar allí datos compatibles y conservar su procedencia.
- Carga de expresiones compatible en convolución/correlación algebraica (ambos operandos), ecuaciones en diferencias, medidas, muestreo, Fourier, transformadas y respuestas ideales. El CAS incorpora carga directa de archivos/resultados. Las ayudas existentes incluyen las nuevas convenciones y diagramas en colores.

## Resolución matemática

La normalización léxica usa tokens, sin eval ni ejecución de archivos .m. La evaluación conserva la gramática restringida existente. Sólo los puntos numéricos no finitos pasan al cálculo exacto del límite; ambos lados reales deben coincidir y ser finitos. Antes de simplificar sobre un índice entero se extienden también las singularidades reales aisladas que el motor simbólico puede identificar exactamente. Los tramos explícitos mantienen sus condiciones y los valores finitos que el usuario haya definido.

El plano usa polinomios de potencias positivas para tratar correctamente z=0 y los avances. Los factores polinómicos comunes se cancelan de forma exacta sobre los coeficientes almacenados, nunca emparejando raíces próximas. La ROC anular se determina desde los polos no cancelados y la elección derecha/izquierda/radio; no se inventa a partir de la fracción. Las raíces y los contornos se representan numéricamente. Una raíz numéricamente indistinguible del círculo unitario no permite certificar que la ROC lo contiene.

El FIR combina núcleos sinc ideales con las amplitudes individuales, los desplaza por D=(L−1)/2 y aplica la ventana simétrica. Kaiser estima longitud y β con el ancho de transición menor y el error absoluto más exigente referido a la mayor amplitud. La estimación no garantiza cumplimiento; la evaluación de las bandas originales forma parte del cálculo. Las familias IIR de ganancia común se diseñan normalizando por el límite superior y luego escalando el prototipo, lo cual respeta los límites absolutos solicitados.

## Límites de implementación

- Las familias IIR clásicas no permiten dos amplitudes distintas en un rechazabanda. La herramienta lo rechaza explícitamente y propone FIR. No se implementó un diseño IIR multibanda de ganancias independientes.
- El plano complejo de H(z) se limita a transferencias racionales con coeficientes numéricos. Se ofrece mapa de colores, no superficie 3D.
- La recuperación de soporte finito completo exige un polinomio de Laurent; para una secuencia infinita debe elegirse un intervalo. Los ceros exteriores al soporte no pueden deducirse de X(z).
- Los límites automáticos corresponden a la coordenada real de señales y secuencias. No se supone continuidad multivariable ni se inventa un límite cuando el motor no lo demuestra. Una singularidad no identificada simbólicamente se intenta resolver al evaluar un punto no finito; los parámetros pendientes siguen siendo simbólicos.
- Los archivos de muestras no se convierten automáticamente en fórmulas de soporte infinito. Los editores algebraicos importan resultados con expresión y variable compatibles; los registros CSV/MATLAB se usan en las entradas numéricas correspondientes.
- La evaluación de tolerancias usa una rejilla densa y bordes; no certifica máximos continuos. Un diseño fuera de tolerancias puede inspeccionarse y exportarse, pero queda identificado expresamente como no satisfactorio.
- La estabilidad interna de una realización con cancelaciones no se deduce de la transferencia simplificada.

## Desarrollo y pruebas

No se ejecutaron pruebas de funcionamiento, casos matemáticos de prueba, validaciones manuales de interfaz ni baterías de regresión, según indicación del usuario. La compilación de sintaxis, el empaquetado y las comprobaciones de integridad de los adjuntos forman parte de la entrega y no certifican el funcionamiento. Esta publicación es preliminar; 1.1.3 permanece como última estable.

## Archivos de código

- `build_portable.ps1`
- `signallab_pc/__init__.py`
- `signallab_pc/amplitude_design.py`
- `signallab_pc/band_edges.py`
- `signallab_pc/cas_engine.py`
- `signallab_pc/cas_import.py`
- `signallab_pc/cas_panel.py`
- `signallab_pc/cas_transfer.py`
- `signallab_pc/convolution_algebra_panel.py`
- `signallab_pc/course_tools.py`
- `signallab_pc/course_tools_panel.py`
- `signallab_pc/data_import.py`
- `signallab_pc/difference_panel.py`
- `signallab_pc/engine.py`
- `signallab_pc/expression_dialects.py`
- `signallab_pc/expression_editor.py`
- `signallab_pc/expression_import.py`
- `signallab_pc/expression_measures_panel.py`
- `signallab_pc/filters.py`
- `signallab_pc/fourier_panel.py`
- `signallab_pc/frequency_analysis.py`
- `signallab_pc/inverse_dtft_algebra.py`
- `signallab_pc/library_articles.py`
- `signallab_pc/math_source.py`
- `signallab_pc/mathematical_help.py`
- `signallab_pc/measures_symbolic.py`
- `signallab_pc/project.py`
- `signallab_pc/project_picker.py`
- `signallab_pc/result_expressions.py`
- `signallab_pc/result_summary.py`
- `signallab_pc/reuse_sources.py`
- `signallab_pc/sampling_panel.py`
- `signallab_pc/singularities.py`
- `signallab_pc/symbolic.py`
- `signallab_pc/symbolic_panel.py`
- `signallab_pc/system_analysis_panel.py`
- `signallab_pc/system_import.py`
- `signallab_pc/tool_catalog.py`
- `signallab_pc/tool_help_catalog.py`
- `signallab_pc/toolbox.py`
- `signallab_pc/transfer_plane.py`
- `signallab_pc/transform_context.py`
- `signallab_pc/transform_lab.py`
- `signallab_pc/visual_help.py`
- `signallab_pc/z_algebra.py`
- `signallab_pc/z_plane.py`
