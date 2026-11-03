# Cobertura de las guías de Sistemas y Señales II

Revisión de capacidades de SignalLab PC, 23 de octubre de 2026. Se leyeron los cinco documentos y sus figuras; se compararon los enunciados con los menús y el código. Se añadieron herramientas generales, sin precargar respuestas ni parámetros de los ejercicios.

**Conclusión:** la versión 0.25 tenía cobertura parcial. Faltaban operaciones importantes para FFT con ventanas, diseño por especificaciones, conversiones y análisis de fase. La versión 0.26 incorpora esas herramientas. Esto describe capacidades implementadas; no constituye una validación de los resultados de cada ejercicio. No se ejecutaron pruebas funcionales ni se resolvieron los prácticos completos.

## Material revisado

Guías de referencia temática; los documentos de ejercicios no se incluyen en esta carpeta.

- Guía de filtros IIR
- Diseño por ubicación de polos y ceros
- Estimación espectral con FFT
- Trabajo práctico 4
- Diseño de filtros FIR
## Comparación por guía

| Guía y ejercicios | Cobertura previa | Herramientas incorporadas o ampliadas | Alcance que debe tenerse en cuenta |
|---|---|---|---|
| FFT, 1–3: espectros de señales y ventanas, DFT frente a DTFT | DFT y DTFT disponibles; faltaba un flujo explícito con ventana y tamaño FFT independientes | **Fourier → Ventanas, FFT y resolución espectral** | FFT sin normalización hacia adelante; módulo/fase o real/imaginaria. Las muestras de DFT se dibujan con STEM. |
| FFT, 4–6: Kaiser, distintas duraciones y relleno con ceros | Kaiser estaba en PSD y FIR, no como transformación reutilizable de una señal | Ventana rectangular, Hann, Hamming, Blackman o Kaiser; L independiente de NFFT; señal y ventana exportables | Aumentar NFFT interpola el espectro; no mejora la resolución de una observación fija. Se conservan resultados para compararlos. |
| FIR, 1–2: respuesta ideal, ventanas y longitud | Diseño por corte y cantidad de coeficientes; faltaba partir de tolerancias | **Filtros y sistemas → FIR por especificaciones**, respuesta ideal truncada, ventana e impulso | La respuesta ideal infinita sigue siendo un objeto teórico; se muestra su tramo usado. |
| FIR, 2–5: longitud, Kaiser, paso alto y pasabanda | No había estimación ni búsqueda por especificaciones | Estimación Kaiser; longitud manual; búsqueda de la primera longitud aceptada hasta una cota, dentro de cada ventana | La búsqueda evalúa una rejilla de frecuencias con los bordes incluidos. No prueba el mínimo entre todos los filtros ni el cumplimiento entre todos los puntos. |
| IIR, 1: Butterworth e invarianza al impulso | Biquad y bilineal; faltaba diseño de orden general y conversión por impulso | **IIR por especificaciones**: Butterworth digital o prototipo analógico con bilineal/invarianza; conserva ambos sistemas | En invarianza, cumplir las especificaciones analógicas no garantiza cumplir las digitales por aliasing. El informe evalúa la respuesta resultante. |
| IIR, 2–3 y 5–10: frecuencia, T y deformación | Bilineal de una transferencia racional | **Muestreo → Mapeo de frecuencias y período**, ramas de aliasing, predeformación y conversiones | Un filtro ideal no racional no se representa exactamente mediante una lista finita de coeficientes; el mapeo de sus bordes sí se puede estudiar. |
| IIR, 4: conversión inversa y unicidad | Sin inversas de conversión | Bilineal inversa y dos candidatos de inversa de invarianza al impulso | La inversa de invarianza implementada admite polos simples separados, sin polos en cero ni parte polinómica directa significativa. No es un inversor universal de distribuciones. |
| Polos/ceros, 1–6 y 8: diseño, rechazo, normalización, respuesta y estabilidad | Plano editable, transferencias, filtrado y respuesta temporal | **Normalizar ganancia**, reutilización de filtros, gráficos de magnitud dB/fase/retardo en las nuevas herramientas | Para un FIR diseñado por ceros, deben incluirse los polos en cero requeridos por la representación causal en z. Las afirmaciones de estabilidad requieren especificar interpretación/ROC. |
| Polos/ceros, 9: respuestas según ROC | Z inversa sólo causal/alrededor de infinito | **Transformadas → Z inversa con región de convergencia**: contorno exterior, interior, círculo unidad o radio manual | Devuelve muestras aproximadas por contorno; no una fórmula bilateral algebraica cerrada. Radios cerca de polos y pocos puntos pueden afectar la precisión. |
| Polos/ceros, 10–14: fase mínima y paso todo | Se podían introducir factores manualmente, sin una herramienta de descomposición | **Fase mínima y fase lineal**: reflexión de ceros, compensación de ganancia, factor paso todo y examen de módulo constante | No cancela raíces por proximidad. Un cero en el círculo o un polo no estable impide afirmar fase mínima estricta. Factorizaciones alternativas con un FIR de fase lineal se pueden construir con coeficientes y comprobar por conexión en cascada; no se enumeran todas automáticamente. |
| Polos/ceros, 15–16: retardo y tipos FIR | Respuesta en frecuencia, sin clasificación de simetría | Tipos I–IV sobre soporte activo, retardo y gráfico de retardo de grupo | Clasificación numérica para FIR reales; en ceros de H la fase y el retardo pueden no estar definidos. |
| TP4, 1–2 y 4: energía, potencia, Parseval y bandas | Fourier, densidad de energía y medidas temporales; faltaba integración explícita por banda y PSD de líneas | **Energía espectral por banda** y **Potencia periódica y líneas espectrales** | La primera integra X(ω) sobre una ventana disponible; la segunda muestra pesos de deltas, no alturas finitas. Las identidades teóricas no se demuestran por una cuadratura numérica. |
| TP4, 3 y 5–7: autocorrelación y correlación | Correlación continua/discreta, finita/periódica y normalizada ya disponibles | Informe de pico y convención de retardo más clara | Para señales periódicas se debe elegir el modelo periódico y la normalización promedio; no tratar una ventana finita como toda la señal. |
| TP4, 8–10: ecos, radar y correladores | Generación de señales/ruido, desplazamiento, suma, filtrado y correlación combinables | Pico del módulo y retardo en el informe de correlación | Se puede construir el experimento con herramientas generales. No hay un simulador específico de radar/BPSK ni una demostración automática de probabilidades de decisión. El máximo puede ser ambiguo por ruido, periodicidad o ecos. |

La numeración del documento de polos y ceros salta del 6 al 8; no se inventó un ejercicio 7.

## Cómo se mantienen generales las herramientas

- Las frecuencias digitales se ingresan en rad/muestra; se aceptan expresiones como `pi/4`. Las analógicas usan rad/s y T usa segundos.
- Las tolerancias FIR/IIR se expresan en amplitud lineal: paso entre 1−δp y 1+δp, rechazo hasta δs. Butterworth utiliza la subbanda de paso entre 1−δp y 1.
- Cada herramienta tiene entrada local, informe, ayuda contextual y resultados reutilizables. El diseño no depende de una señal global del proyecto.
- Los sistemas calculados se guardan como transferencias y se pueden exportar o usar en respuesta temporal/frecuencia. Las señales intermedias pueden enviarse a Fourier, filtros y otras herramientas.
- El software informa aproximaciones, tolerancias numéricas y ventanas finitas. Las explicaciones y demostraciones conceptuales siguen requiriendo interpretación del estudiante.

## Límites abiertos

No corresponde afirmar que la aplicación resuelve automáticamente todos los apartados de las cinco guías. Las demostraciones, la minimalidad global, las inversas simbólicas bilaterales generales y los casos distributivos completos exceden lo implementado. El objetivo de estas incorporaciones es disponer de instrumentos generales para plantear, calcular y explorar los ejercicios. La corrección funcional de esta entrega está pendiente de las evaluación de uso.
