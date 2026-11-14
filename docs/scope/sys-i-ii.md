# Alcance de Sistemas y Señales I y II

[← Documentación](../README.md)

Esta matriz relaciona los temas de señales y sistemas con las herramientas disponibles y sus límites. Las ampliaciones posteriores a la base 1.0 se detallan al final; las funciones preliminares se identifican por versión. La presencia de una herramienta no implica que todo ejercicio o expresión tenga una solución automática.

La ubicación de las operaciones se define en `tool_catalog.py` y `workflow_catalog.py`. Las [convenciones matemáticas](../conventions.md) y las [notas de versiones](../releases/README.md) completan esta guía.

## Sistemas y Señales I

| Eje | Dónde se trabaja | Alcance y carencia concreta |
|---|---|---|
| 1. Señales y sistemas | Señales; Sistemas LTI | Fórmulas/tramos, muestras, transformaciones, medidas y estados. Correlación en retardo cero permite estudiar productos internos con el modelo elegido. No es un demostrador automático de propiedades de operadores arbitrarios ni un simulador de parámetros distribuidos. |
| 2. Sistemas LTI | Convolución; Analizar un sistema; Conectar sistemas; Ecuaciones diferenciales | Convolución continua/discreta, respuesta temporal y memoria inicial discreta, ecuaciones y bloques de transferencias. Realización dentro del análisis presenta sumadores, ganancias e integradores/retardos, con ecuaciones y matrices reutilizables. Alcance: H(s) propia y H(z) causal, forma directa II y cascada SOS conservada; no implementa derivadores ni avances. |
| 3. Laplace y sistemas continuos | Transformada de Laplace; Analizar un sistema; Diseñar filtro (RC y segundo orden) | Directa unilateral/bilateral e inversa causal o racional bilateral con ROC, polos/ceros y modelos RC/segundo orden. La ROC puede ser derecha, izquierda o franja elegida por una línea interior. La inversa bilateral admite un desplazamiento global exp(-d*s), pero no cualquier X(s) trascendente ni sumas de retardos distintos. Realización genera el diagrama de H(s) propia y sus matrices; una ecuación diferencial LTI se representa con sus listas de coeficientes ordenadas como potencias descendentes de s. |
| 4. Z y sistemas discretos | Transformada Z; Analizar un sistema | Directa por expresión/soporte o registro finito; inversa racional con ROC; análisis y respuesta temporal. La inversa racional conserva raíces exactas definidas por polinomios, sin exigir expresarlas mediante radicales; las aproximaciones numéricas se identifican con esas raíces. Realización muestra retardos, sumadores y ganancias para H(z) causal. Los coeficientes de una ecuación en diferencias se cargan en potencias ascendentes de z⁻¹; el informe explica el orden de los estados. |
| 5–6. Series de Fourier continuas y discretas | Series de Fourier y líneas espectrales; Filtros ideales; Diseñar filtro (RC y segundo orden) | Análisis/síntesis, armónicos, potencia y filtrado. Permite estudiar truncamiento y Gibbs numéricamente. No certifica convergencia de toda serie ni convierte muestras de un período en una demostración sobre la señal infinita. |
| 7–8. Transformadas de Fourier | Transformada de Fourier; Energía espectral; Densidad de potencia; Hilbert | Directas/inversas numéricas y algebraicas, DFT/DTFT, Parseval por resultados, densidades, Hilbert y señal analítica. Distribuciones y condiciones conservan su significado. El análisis general de H reúne módulo lineal/dB, frecuencia lineal/logarítmica, fase y retardo. El selector de módulo actúa sobre los datos ya calculados; el eje logarítmico evalúa puntos por décadas. |
| 9. Muestreo | Muestreo y aliasing; Reconstruir; Cambiar tasa | Muestreo, Nyquist de tono, tasas pasabanda, ZOH, lineal y SINC, cambio racional con antialias. Modelos de registro finito; no retenciones arbitrarias de cualquier orden ni hardware físico completo. |
| 10. Control introductorio | Conectar sistemas; Analizar un sistema; Espacio de estados | Realimentación, polos, respuestas y estados. El análisis común estima cruces y márgenes de lazo abierto con coeficientes reales, en el intervalo evaluado y con realimentación negativa unitaria. No encontrar cruces no se interpreta como margen infinito ni como prueba de estabilidad; la rejilla puede omitir cruces entre puntos. El barrido de raíces al variar K fue retirado de la navegación. |

## Sistemas y Señales II

| Eje | Dónde se trabaja | Alcance y carencia concreta |
|---|---|---|
| 1. Procesamiento continuo/discreto y cuantificación | Muestreo; Cuantización y representación; Sistemas LTI | Conversión A/D/D/A como modelos, punto fijo exacto, saturación, redondeo y SNR. Formatos Q e IEEE 754 binary16/32/64, con comparación de coeficientes de H(z), respuesta y polos; SOS o polinomios directos. Se estudia almacenamiento y luego se evalúa en doble precisión. DF-II transpuesta y SOS permiten ejecutar con redondeo de productos, sumas, salida y memorias, medir errores/SNR del registro y detectar repeticiones exactas con entrada nula. No se modelan todas las realizaciones ni una teoría estadística general de ruido. |
| 2. Diezmado e interpolación | Cambiar tasa de muestreo | Operaciones enteras y conversión racional L/M con FIR antialias. Los modos elementales no filtran automáticamente; se explicita esa diferencia. |
| 3. DFT y procesamiento por bloques | Transformada de Fourier; Convolución | DFT/inversa, comparación con DTFT, convolución circular/lineal y OLA/OLS con cola completa. No agrega un menú por cada propiedad: se trabajan con señales propias y resultados. |
| 4. Densidad espectral y correlación | Energía espectral; Densidad de potencia; Correlación | Densidad de energía independiente, potencia periódica, periodograma/Welch, auto/cruzada, soportes finitos/periódicos y normalización. La detección puede estudiarse por alineación de correlación; no hay un detector óptimo general. |
| 5. Análisis espectral | Fourier/FFT y ventanas; STFT | Ventanas, relleno con ceros, DTFT/DFT superpuestas, referencia y espectrograma. STFT ofrece nivel relativo, amplitud y densidad bilateral calibrada por la ventana, con unidades en rad/muestra o rad/s. Sus columnas complejas se exportan y permiten reconstrucción sobre el registro finito; no constituyen una estimación universal del proceso. |
| 6. Análisis de fase y filtros | Analizar un sistema; Filtro ideal; Ajustar ganancia y fase; Diseñar por polos/ceros | Respuesta, retardo, raíces, fase mínima/paso todo y clasificación FIR. Incluye reconstrucción periódica discreta de fase mínima por modelo cepstral, desplazamiento y referencia de ganancia; no reconstrucción analógica general ni datos ausentes en una banda parcial sin hipótesis adicionales. Compensación FIR permite aproximar una respuesta compleja de ganancia y retardo en una banda, con H(z) estable de coeficientes reales; no es una solución exacta ni universal. Resonadores, ranuras y peines pueden definirse por transferencia/raíces; no se añaden herramientas duplicadas por cada caso. |
| 7. FIR | Diseñar filtro → FIR | Ventanas, cortes/longitud, especificaciones y longitud Kaiser/búsqueda; respuesta e intermedios. La comprobación es en rejilla, sin probar un mínimo global. Los bordes/tolerancias digitales se comparten con IIR por especificaciones. |
| 8. IIR y transformaciones | Diseñar filtro → IIR; Convertir analógico/digital; Espacio de estados | Butterworth, Chebyshev I/II y elíptico, prototipos, bilineal e invarianza al impulso. Estados permite además Euler adelante/atrás y Tustin/ZOH. La transferencia tiene conversiones más acotadas; no debe presentarse una opción no disponible como si se calculase en el mismo panel. |

## Alcance parcial

Modulación y demodulación no están incluidas. La cobertura de Señales Aleatorias se describe en su [guía específica](random-signals.md). Los libros de referencia orientan las convenciones; esta revisión no declara que se haya implementado todo el contenido de un libro de DSP o filtrado analógico.

## Trabajo concreto siguiente, integrado en herramientas existentes

1. Diagramas incorporados en 0.80 dentro del análisis: cadenas de integradores o retardos, coeficientes, ecuaciones, SVG/PNG y matrices para estados. H(s) impropia y avances de H(z) se informan como fuera de esta realización causal ordinaria.
2. Compensación FIR de respuesta incorporada en 0.82 dentro de Ajustar ganancia y fase. La reconstrucción periódica discreta módulo–fase se incorpora en 0.88 con un modelo cepstral de fase mínima, desplazamiento explícito y referencia de ganancia. Quedan fuera la reconstrucción analógica general y las bandas parciales sin hipótesis adicionales; no se asigna una fase única a un módulo que no la determina.
3. Formatos y almacenamiento de coeficientes incorporados en 0.84; ejecución de precisión finita en 0.86 dentro de Cuantización y representación. DF-II transpuesta y SOS, coeficientes/entrada/memorias, productos y sumas, acumulador Q ampliado, saturación/desborde cíclico, errores/SNR del registro y detección exacta de ciclos con entrada nula. No incluye otras realizaciones ni una teoría estadística universal de ruido o emulación completa del procesador.
La salida directa de edición de muestras quedó integrada en 0.75: exportación CSV/JSON y reutilización desde el editor, sin exigir navegar por Resultados. Se conservan el original y la última salida aplicada por separado.

El punto 1 cuenta con la implementación y el alcance anteriores; el punto 2 cuenta con compensación FIR y reconstrucción periódica discreta de fase mínima, manteniendo fuera la reconstrucción analógica general; el punto 3 incluye formatos, coeficientes y ejecución DF-II transpuesta/SOS con alcance explícito, y mantiene abiertos modelos teóricos generales de ruido y otras realizaciones. Su prioridad debe mantener el pedido de una interfaz sencilla: agregar capacidades dentro del problema existente, sin sumar una lista de menús para variaciones del mismo cálculo.

La representación de Bode y los márgenes locales quedaron integrados en 0.77, con ayuda ilustrada y exportación. Se conserva la diferencia entre un cruce detectado/refinado dentro de una rejilla y la demostración de todos los cruces de un sistema arbitrario.

La calculadora CAS general incorporada en 0.78 permite álgebra, derivadas/integrales, límites, ecuaciones y matrices fuera de los formularios especializados. Complementa el trabajo de Sistemas I/II, pero no sustituye las herramientas especializadas. Los diagramas se incorporan en 0.80; compensación y aritmética, pendientes en aquel momento, se incorporan en las versiones posteriores indicadas en esta matriz. Su sintaxis y supuestos están documentados en la biblioteca.

En 0.79, la hoja CAS admite supuestos escalares locales (real, entero, signo, no nulo y límites frente a constantes reales) y conversiones de Euler exp2trig/trig2exp. Las soluciones se restringen al dominio declarado; relaciones generales entre parámetros no se aceptan como si estuvieran implementadas. Las fórmulas numéricas de sistemas tienen las mismas acciones de reutilización que sus coeficientes. Esto complementa las herramientas anteriores; el estado de los pendientes se indica arriba.

En 0.80, StateModel.from_transfer usa el mismo motor de realización que el diagrama y conserva SOS. Los estados se ordenan por sección y por q dentro de ella. No se cancelan raíces por proximidad ni se afirma minimalidad. Los coeficientes extremos exactamente nulos pueden eliminarse cuando sólo representan términos ausentes; los pequeños no se descartan. No se afirma estabilidad interna a partir de una fórmula ya simplificada con estados internos desconocidos.

La compensación 0.82 ajusta módulo y fase conjuntamente porque dispone de la transferencia compleja H. C es un FIR causal estable; el error y el retardo elegido explican su aproximación, incluso para ceros no mínimos. No invierte exactamente ceros en banda, no estabiliza modos internos y no demuestra cotas entre todos los puntos. El producto se evalúa preservando H; una transferencia conjunta que pierde precisión no se publica como reutilizable.

La optimización 0.83 de Z inversa incluye el caso cúbico reportado, polos repetidos, impulsos por términos polinómicos, parámetros simbólicos y comparación de ROC derecha/izquierda/intermedia con una integración de contorno independiente. El caso de grado cinco se representa mediante raíces algebraicas exactas aunque no haya radicales simples. No se devuelven resultados si falta un polo o no se puede decidir la posición del radio.

La comparación de coeficientes 0.84 cuantiza los valores binarios almacenados de H(z), con a[0]=1 implícito. Puede mostrar un cambio de polos por redondeo, incluso hacia la frontera de estabilidad. Las curvas son evaluaciones posteriores en doble precisión, sin una implementación de hardware ni un análisis estadístico completo del ruido de redondeo.

En 0.87, diseño por polos/ceros permite grados no causales de H(z), consulta frecuencia en el mismo documento y conserva el factor z^m al enviarlo al análisis o a Z inversa. Fórmula, raíces, fase, retardo y JSON mantienen ese factor. La evaluación de H(e^jω) no selecciona una ROC por sí sola; los avances no se simulan mediante una recurrencia causal ni se confunden con retardos.


Consolidación 0.89: las conexiones conservan avances temporales y admiten fórmulas, archivo JSON o resultado anterior por bloque. El análisis/importación compartida conserva SOS y dominio; los consumidores que requieren causalidad rechazan un avance explícitamente. Las inversas racionales numéricas con raíces de grado alto presentan números directamente en su fórmula, con redondeo visual declarado y texto completo de mayor precisión. No amplía la selección de ROC de Laplace ni sustituye las carencias indicadas arriba.


Recorrido 0.90: Laplace y Z envían la transformada racional directamente al análisis de H(s)/H(z), sin exigir copiar coeficientes ni calcular una inversa intermedia. La entrada de cada variante se conserva al regresar y la copia entre vistas es explícita cuando ya existía un borrador. La reutilización directa de modelos discretizados y transferencias obtenidas desde estados se incorpora en 0.97; también siguen disponibles en Resultados anteriores.


Biblioteca 0.92: registro común de salidas principales/secundarias de los cálculos, CAS exacto, expresiones con condiciones y datos completos de tablas. No se exige interpretar una transformada como H para conservarla o reutilizarla. Señales, sistemas y estados conservan su tipo y los destinos del mismo problema se ofrecen por variantes compatibles. No cambia el alcance matemático de las operaciones.


DTFT inversa 0.93: numérica desde un período completo, cerrado o sin extremo repetido, y algebraica desde una fórmula/tramos. La forma racional usa las propiedades de Z con el círculo unidad dentro de la ROC y admite secuencias izquierdas/bilaterales. Las bandas ideales ordinarias se integran simbólicamente; las integrales pendientes no se declaran resueltas. Los polos sobre el círculo unidad no se tratan automáticamente como distribuciones o valores principales. La resolución numérica finita puede producir aliasing temporal; no equivale a conocer todo el espectro continuo exacto.


Enventanado 0.95: producto punto a punto de dos entradas independientes, discretas o continuas muestreadas; h[n] arbitraria con ventana simétrica estándar (Hamming, Hann, Blackman, Kaiser, Bartlett o rectangular) o secuencia w[n] propia. Incluye retardado opcional para registros de origen negativo, transferencia y respuesta en frecuencia con retardo de grupo. El intervalo finito cargado define el recorte; no se evalúa el soporte infinito fuera de él ni se normaliza la ganancia. Registros continuos se multiplican interpolando la segunda señal linealmente en los instantes de la primera; no implementa productos generales de distribuciones.


Ajuste 0.96: el FIR desde h[n] permite elegir L y la ubicación de la ventana por separado del registro, con evaluación de fórmulas en el soporte elegido y extensión por cero de datos finitos. La simulación de estados admite datos independientes por canal, conserva los índices/orígenes y distingue índice n del reloj físico T. Los canales deben compartir su eje; no se interpolan o remuestrean automáticamente. La frecuencia discreta de estados se presenta en rad/muestra, compatible con H(z), aunque el motor interno conserva su interfaz física en rad/s mediante una conversión explícita.


Reutilización de estados 0.97: modelos calculados, incluidos los discretizados, se cargan directamente en otros estudios con matrices, dominio y T conservados. El canal convertido a H(s)/H(z) muestra su fórmula y ofrece las mismas acciones de análisis que el resto de transferencias. Cargar modelo permite abrir el JSON nativo exportado, con elección si contiene varios modelos. No cambia el alcance matemático de los motores ni elimina las limitaciones de canales que ocultan modos internos.


Suma y producto 0.98: agrupados por problema, con entradas locales discretas/continuas. Suma cubre la unión de registros; Producto conserva el intervalo de la primera señal. La suma continua trata las partes ordinarias mediante interpolación lineal y combina los términos Dirac por separado. Conserva el alcance de aproximación de la rejilla finita. Los relojes discretos registrados deben coincidir y se propagan al resultado. Las rutas existentes y los destinos desde expresiones de Resultados siguen disponibles.


Contexto de reloj 0.99.2: H(z) conserva un período físico opcional al pasar desde estados, conversión analógica/digital y operaciones de filtros. La frecuencia del análisis sigue en rad/muestra. Respuesta temporal y ejecución verifican la compatibilidad con Fs de entrada, y sus salidas conservan el reloj. No implementa conexiones multirrate implícitas: dos bloques con T conocidos diferentes requieren igualar la tasa previamente. Un sistema sin reloj puede seguir operando por índices.


Transformaciones 0.99.3: las operaciones elementales se eligen directamente en ambos dominios dentro de Transformar una señal. Par e impar continuo completa la descomposición de registros ordinarios por interpolación lineal sobre una rejilla simétrica y trata separadamente los pesos Dirac; no es una descomposición simbólica universal de expresiones infinitas. Las salidas discretas conservan el contexto de reloj. Se distinguen las fórmulas de entrada de los valores transformados.

En 0.99.4, Laplace bilateral se integra con directa/inversa en el mismo formulario. Los intervalos acotados no heredan restricciones artificiales de las colas; una ROC vacía se identifica sin publicar una expresión convergente. La inversa racional usa fracciones parciales con polos repetidos, impulsos/derivadas y ROC explícita. Copia y Resultados preservan el contexto; la ayuda incluye un esquema de polos y soportes. Alcance preciso en DESARROLLO_0.99.4.md.

En 0.99.5, las capacidades se conectan mediante carga común de sistemas/expresiones y selectores por variable/unidad. Se conserva el reloj de las transferencias digitales y las condiciones de expresiones copiadas; editar prepara un cálculo independiente. Los informes de medidas guardados muestran también energía, potencia y RMS. Es una mejora de uso y presentación de las herramientas existentes, sin ampliar el programa académico ni añadir familias.

En 0.99.6, los métodos numérico/algebraico de Fourier comparten definiciones compatibles, manteniendo soporte e intervalo observados y separando directa/inversa. Una rejilla finita sigue siendo una aproximación y no una prueba de igualdad con la fórmula global. Los tramos anidados se traducen estructuralmente para reutilización numérica y las entradas copiadas no comparten datos mutables. No amplía el alcance académico declarado.

En 0.99.7, la conversión analógico/digital presenta mapeos s/z, transferencias y frecuencias de corte de referencia y medidas con un criterio de media potencia declarado. El módulo puede cambiarse entre amplitud y dB desde la figura. El plano binómico evita el colapso visual cuando las raíces están sobre un eje. No amplía familias ni cambia los algoritmos de conversión de coeficientes.

0.99.8: el CAS recibe resultados matemáticos de las herramientas y de la biblioteca. La inversa Z aplica pares geométricos, desplazamiento y linealidad cuando reconoce esa estructura, respetando la ROC; mantiene el método general para los demás casos. No amplía el catálogo de temas.

0.99.9: los campos continuos admiten sumas finitas de Dirac de orden cero con argumentos lineales, conservadas por posición y peso. CTFT y series tratan sus áreas por separado de la cuadratura ordinaria; la presentación y la ayuda distinguen esas distribuciones de muestras discretas. No extiende las medidas ordinarias ni el muestreo puntual a distribuciones, ni afirma una transformada universal.

0.99.10: se aclaran DFT/FFT, DTFT y Fourier continua dentro de una misma herramienta, separando Directa/Inversa y el cálculo. La ayuda distingue registro finito, secuencia y tiempo continuo. La búsqueda respeta combinaciones de variantes y no amplía los motores matemáticos ni la cobertura curricular.

0.99.11: modelos RC y de segundo orden, editor de raíces y FIR/IIR se encuentran dentro de Diseñar filtro. Las 80 variantes se conservan con 29 accesos por problema; no se cambia el alcance matemático por agrupar la interfaz. Analizar un sistema conserva la consulta de raíces y respuestas.

Primera estable 1.0.0: consolida las 29 herramientas y 80 variantes implementadas, sin ampliar sus alcances por cambiar la etiqueta de versión. ALCANCE_1.0.md fija las convenciones y límites publicados. La corrección final distingue entradas activas de campos derivados y conserva ediciones hechas durante un cálculo.


## Ampliación 1.1.1: ecuaciones en diferencias

Ecuaciones lineales reúne la EDO existente y la nueva recurrencia discreta de coeficientes constantes. El usuario define a₀y[n]+…+aₚy[n−p]=f[n], el primer índice n₀ y p valores anteriores, o reposo. La solución algebraica se separa en entrada cero y estado cero. Las muestras desde n₀ conservan su índice y no definen la extensión infinita de la fórmula. H(z), bajo condiciones iniciales nulas, se guarda por separado de y[n] y puede enviarse a análisis de sistemas o CAS.

Hay formas cerradas mediante propiedades de Z para las entradas polinómicas, exponenciales, senoidales, escalones, impulsos y sus tramos de intervalos admitidos. En otros casos se presenta la convolución finita exacta, identificada como representación sin forma cerrada. No se declaran resueltas recurrencias con coeficientes variables ni sistemas de recurrencias. Las condiciones iniciales siguen el orden y[n₀−1], y[n₀−2], …, distinto del orden por derivadas que corresponde a una EDO.


## Ampliación 1.1.3: ventanas independientes

Crear una señal incluye Ventana: rectangular, Hann, Hamming, Blackman, Bartlett y Kaiser simétricas. Se eligen L, origen o centrado y β cuando corresponde. El resultado se exporta como señal discreta y puede analizarse con DTFT, DFT/FFT o Z finita, o multiplicarse por otra señal. La longitud L se expresa como cantidad total de muestras. La recepción en Z selecciona Muestras finitas y conserva los índices, también si son negativos.


## 1.2.0 preliminar · 2026-11-02

Z directa/inversa integran registros finitos; transferencia racional en plano z y ROC explícita; FIR con amplitudes por banda y tolerancias absolutas/relativas/dB; importación compatible compartida. No se declara ampliación curricular ni estabilidad comprobada: esta entrega es preliminar. Las familias IIR clásicas conservan una ganancia común de paso. Ver VERSION_1.2.0-preview.md.


## 1.8.9 preliminar: observar y explicar respuestas temporales

La herramienta existente de Respuesta temporal permite extender entradas con ceros, sugerir una ventana desde los polos, comparar componentes y medir el escalón respecto de la ganancia DC estable. El inspector discreto explica los aportes de la realización guardada y del historial, incluidas las secciones SOS. Son ampliaciones de uso y análisis de sistemas LTI: no incorporan un nuevo tema curricular ni convierten una medición finita en una garantía de establecimiento. La [guía de respuesta temporal](../temporal-responses.md) precisa las condiciones y las diferencias entre muestras, interpolación y fórmula original.
