# Contratos científicos de RF

## Red, ejes y referencias

`RFNetwork` representa una matriz compleja por frecuencia. Los ejes son Hz, crecientes, finitos y no negativos. La forma es `(frecuencia, puerto de salida, puerto de entrada)`. Las etiquetas de puertos son únicas y corresponden al orden de la matriz. El índice Python comienza en cero. Los nombres de puerto predeterminados comienzan en uno. S es adimensional, Z se expresa en Ω y Y en S. ABCD usa A y D adimensionales, B en Ω y C en S.

Se admiten referencias **reales, positivas y finitas**, distintas por puerto e incluso por frecuencia. Usando fasores RMS e `I` entrando en cada puerto, `a = (V + R I)/(2 sqrt(R))` y `b = (V − R I)/(2 sqrt(R))`. La potencia que entra es `∑(|a|² − |b|²)`. Para estas referencias, el convenio `e^{+jωt}` da fase decreciente para un retardo positivo. Las referencias complejas, pseudoondas y mixed-mode requieren una extensión expresa del contrato. [Comparación de convenios](https://scikit-rf.readthedocs.io/en/latest/examples/networktheory/Working%20with%20Complex%20Characteristic%20Impedances.html)

## Conversiones

Normalizar cada puerto con $v=V/\sqrt R$ e $i=I\sqrt R$. Representar el sistema mediante $C_v v+C_i i=0$. Las formas S, Z y Y conducen respectivamente a $(I-S)v-(I+S)i=0$, $v-z i=0$ y $i-y v=0$. Aquí $z=R^{-1/2}ZR^{-1/2}$ e $y=R^{1/2}YR^{1/2}$. Para S, sustituir $v=a+b$ e $i=a-b$. La cadena ABCD de dos puertos usa $[V_1,I_1]^T = M[V_2,-I_2]^T$. Esta relación permite convertir una unión ideal a ABCD aun cuando Z o Y sean singulares.

La conversión resuelve el sistema de las incógnitas del formato destino. Equilibrar por fila tras normalizar, estimar valores singulares y rechazar un pivote con $\sigma_\text{min} \le 10^{-12}\max(1,\sigma_\text{max})$ en ese sistema. Se registra la frecuencia de la primera fila de resultados inválida. La cota es un criterio de resolución en doble precisión, no una garantía de exactitud de datos medidos.

La renormalización conserva tensión y corriente. Se cambia la base de las ondas con las raíces de las referencias anteriores y nuevas. El producto usa sistemas lineales y preserva reflexiones de paso directo y circuitos ideales. La conexión de dos puertos debe igualar sus referencias en el enlace interno o renormalizar explícitamente. Las rejillas se cotejan punto a punto y cualquier interpolación se solicita de forma explícita dentro de la banda de origen.

## Análisis y alcance de potencia

En S, el retorno se reporta como $-20\log_{10}|S_{ii}|$. El nivel $S_{ii}$ en dB tiene el signo opuesto. La pérdida de inserción con puertos adaptados se define frente a paso unidad. Terminar los demás puertos conserva el orden elegido de los puertos retenidos. Impedancia de entrada, VSWR y retardo de grupo usan el modelo de la carga y sus dominios. La fase y el retardo se evalúan en tramos con amplitud suficiente y respetan ceros y discontinuidades.

Reciprocidad en ondas normalizadas se verifica con simetría traspuesta y referencias reales. La pasividad se caracteriza por singular máxima de S no mayor que uno dentro de tolerancia. Una red activa sigue siendo un modelo válido.

Medir la matriz S supone que el resto de los puertos se adapta a sus referencias. En índices `[salida, entrada]`, la pérdida de inserción usa esa dirección y el aislamiento su dirección inversa. La simetría reportada evalúa inversión del orden, separada de reciprocidad. Los nulos se excluyen de las derivadas de fase. Una pendiente entre puntos presupone que el incremento de fase real está resuelto por la malla. En un puerto, impedancia o admitancia infinita queda marcada como indefinida en el vector correspondiente y el VSWR ideal es infinito. Las tolerancias de unas pocas ULP alrededor de Γ = ±1 identifican los límites ideales resolubles.

## Líneas y adaptación

Una línea uniforme admite Zc real, un factor de velocidad entre 0 y 1 y atenuación escalar o por frecuencia en dB/m. RLGC admite pérdidas pasivas y L/C positivos por metro, a frecuencias estrictamente positivas. Se calcula γ usando las raíces principales de las variables serie y paralelo de línea. El cálculo de potencia sobre referencias reales usa una cadena escalada por exp(−γℓ) para evitar desbordamientos en líneas atenuantes. Se discrimina la reflexión de ondas de tensión sobre Zc de la reflexión de potencia medida sobre la impedancia de referencia. [Steer, teoría de líneas](https://repository.lib.ncsu.edu/server/api/core/bitstreams/a20b497c-5449-44ad-a010-80b1becbe5ec/content)

L y stub sintetizan soluciones ideales de adaptación en una frecuencia utilizando cargas con parte real positiva. Cuarto de onda requiere carga resistiva. El barrido conserva los componentes en sus unidades físicas y admite cargar una impedancia dependiente de frecuencia. Un resultado adaptado en la frecuencia de diseño puede tener pérdidas de desadaptación fuera de ese punto. Para Pi y T haría falta definir una impedancia intermedia o un criterio adicional de Q, ancho de banda o valores realizables. No se completa esa elección de forma implícita.

## Presupuesto RF y ventana de validez

El enlace trabaja con potencias absolutas en dBm y ganancias relativas en dB o dBi para antenas. La temperatura de referencia para la figura de ruido es 290 K. La temperatura de la fuente y el ancho equivalente de ruido determinan la potencia disponible de entrada mediante kTB. Friis suma las temperaturas de ruido referidas a entrada bajo etapas adaptadas, no correlacionadas y lineales. El modelo de tercer orden describe uno o dos tonos de igual nivel con productos no coincidentes, dentro del umbral de 1 dB de compresión de la fundamental. El SFDR de dos tonos se informa si el cruce extrapolado del IM3 con el piso de ruido integrado está dentro de ese dominio. [Constante de Boltzmann](https://physics.nist.gov/cuu/Constants/Value/k.html) · [Figura de ruido](https://helpfiles.keysight.com/csg/NA520xA/Applications/Noise_Figure.htm)

## Rejillas y ventanas

Zoom FFT recorre un intervalo cerrado de longitud máxima de un período. El eje puede usar Hz con tasa registrada o explícita coincidente, o rad/muestra. Su fase usa los índices n de la señal. La longitud L fija la separación nominal 2π/L y la duración L/Fs cuando existe reloj. La densidad de la nueva rejilla es independiente de la resolución física. Chirp-Z calcula la evaluación sobre radios geométricos y ángulos lineales. Sobre el círculo usa Zoom FFT. Fuera del círculo usa sumas escaladas por bloques con un límite de productos precisado en su contrato. Los picos interpolados se estiman dentro de la rejilla para tonos complejos aislados. La frecuencia se refina con la derivada de |X|² y amplitud y fase con la evaluación compleja dividida por la suma de la ventana. Fuga, ruido y cercanía de otros tonos pueden sesgar esas estimaciones. [Zoom FFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ZoomFFT.html)

## Archivos y procedencia

Touchstone 1.0 usa extensiones `.sNp`, referencia escalar y Z/Y normalizados. Touchstone 2.0 declara el orden de dos puertos, admite matrices triangulares y referencias reales por puerto, y guarda Z/Y en unidades físicas. El importador admite RI, MA, DB, Hz/kHz/MHz/GHz y comentarios sin ejecutar contenido. Rechaza mezcla modal, ruido, formatos híbridos, referencias no representables y archivos ambiguos o sin cerrar. El exportador RI conserva números en doble precisión y usa reemplazo atómico. [Especificación IBIS](https://ibis.org/touchstone_ver2.0/touchstone_ver2_0.pdf)

Los registros RF JSON reutilizan los cálculos tipados y la procedencia verificada. La instantánea conserva tres bloques en binario little-endian, frecuencia, referencias y matrices, con SHA-256. SLPROJ usa la versión 2 sólo cuando incluye esos bloques RF fuera del manifiesto y mantiene la lectura de la versión 1. SLBIN sigue representando un registro uniforme de señal. Su eje escalar y su semántica de señal no describen una matriz RF con rejilla irregular.
