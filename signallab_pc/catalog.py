"""Navegación HP 5.0 auditada para reflejar el alcance en construcción."""

MODULES = {
    "Señales": ["Crear secuencia x[n]", "Crear expresión o señal por tramos", "Transformar o sumar secuencias", "Calcular energía y potencia", "Conceptos y clasificación", "Volver al inicio"],
    "Sistemas LTI": ["Convolución discreta x[n]*h[n]", "Convolución continua numérica", "Correlación y autocorrelación", "Resolver ecuación en diferencias", "Respuesta a impulso o escalón", "Polos, ceros y estabilidad", "Conceptos y propiedades LTI", "Volver al inicio"],
    "Transformadas": ["Laplace directa: x(t) a X(s)", "Laplace inversa: X(s) a x(t)", "Transformada Z de secuencia", "Z inversa: X(z) a x[n]", "Resolver una EDO simbólica", "Bilineal: H(s) a H(z)", "Teoría, convergencia y ROC", "Volver al inicio"],
    "Fourier": ["Serie de Fourier continua", "Serie de Fourier discreta", "Transformada continua directa", "Transformada continua inversa", "Fourier discreta: DFT y DTFT", "Densidad de energía y PSD", "Convolución y correlación", "Teoría y propiedades de Fourier", "Volver al inicio"],
    "Muestreo A/D": ["Muestrear: x(t) a x[n]", "Analizar Nyquist y aliasing", "Diezmar, expandir o interpolar", "Reconstruir: x[n] a x(t)", "Cuantizar y calcular SNR", "Representar en punto fijo", "Conceptos de conversión A/D y D/A", "Volver al inicio"],
    "Filtros": ["Diseñar FIR por ventanas", "Diseñar IIR biquad", "Diseñar filtro analógico RC", "Filtrar una señal con b/a", "Respuesta digital H(e^jw)", "Polos/ceros: analizar o diseñar", "Transformación bilineal H(s)-H(z)", "Teoría y estructuras de filtros", "Volver al inicio"],
    "Control": ["Respuesta de segundo orden", "Respuesta lineal H(jw)", "Diagramas de Bode H(jw)", "Respuesta discreta H(e^jw)", "Realimentación unitaria", "Lugar de raíces", "Polos, ceros y estabilidad", "Teoría de sistemas y control", "Volver al inicio"],
    "Teoría": ["Sistemas I: ejes 1-4", "Sistemas I: Fourier", "Sistemas I: muestreo/control", "Sistemas II: procesamiento", "Sistemas II: espectro", "Sistemas II: filtros", "Fórmulas clave", "Instrucciones de uso", "Volver al inicio"],
    "Recientes y banco": ["Reutilizar última señal", "Importar señal…", "Abrir carpeta de intercambio"],
    "Acerca de": ["Estado de migración", "Referencia HP vinculada", "Dependencias y distribución"],
}

IMPLEMENTED = {
    "Señales": {"Crear secuencia x[n]", "Crear expresión o señal por tramos", "Transformar o sumar secuencias", "Calcular energía y potencia"},
    "Sistemas LTI": {"Convolución discreta x[n]*h[n]", "Correlación y autocorrelación"},
    "Fourier": {"Fourier discreta: DFT y DTFT"},
    "Recientes y banco": {"Reutilizar última señal", "Importar señal…", "Abrir carpeta de intercambio"},
    "Acerca de": set(MODULES["Acerca de"]),
}

FUTURE_MENU_MAP = {
    "Señales": "generación, tramos, desplazamiento, inversión, escala, suma, paridad e indicadores de energía/potencia",
    "Sistemas LTI": "convolución discreta/continua, correlaciones lineales/circulares/periódicas/normalizadas, ecuaciones en diferencias, respuestas, P/Z",
    "Transformadas": "Laplace/Z directas e inversas, resolución simbólica de EDO, bilineal y ROC",
    "Fourier": "series continuas/discretas, trenes, Fourier integral, DFT/IDFT/DTFT, superposición, espectros, densidades y operaciones",
    "Muestreo A/D": "muestreo y aliasing, cambio de tasa, reconstrucción, cuantización/SNR y punto fijo",
    "Filtros": "FIR, biquad IIR, RC, filtros b/a, P/Z, respuestas y bilineal",
    "Control": "segundo orden, H(jw), Bode, H(e^jw), realimentación, lugar de raíces, estabilidad",
    "Teoría": "conceptos, fórmulas, convenciones e instrucciones por tema",
}
