# SignalLab PC 0.66 — documentos agrupados y análisis de raíces

Actualización: 27/10/2026. Compilación de desarrollo hacia la primera estable.

## Organización

El explorador y el menú Herramientas muestran 16 documentos principales. Se reúnen creación/edición/transformación de señales; medidas de energía y potencia; convoluciones; correlaciones; Fourier/FFT; series; densidades; Hilbert/STFT; muestreo/reconstrucción/cambio de tasa; cuantización; espacio de estados; Laplace/ecuaciones; y las herramientas aleatorias ya existentes. Filtros, conexiones y Z conservan documentos propios. No se amplió el alcance de Señales Aleatorias.

Cada documento tiene opciones con nombres de dominio y método. Las entradas y resultados se conservan por opción. La creación es diferida: abrir un documento no construye todas sus herramientas. Las rutas antiguas de envío siguen disponibles internamente. Al enviar una señal sólo se ofrecen las entradas de la opción activa; los formularios ocultos no reciben datos. Buscar una operación y abrir la coincidencia lleva a esa opción cuando su nombre coincide.

La estructura toma como referencia las familias de la guía SignalLab HP Prime 5.0 (Señales, LTI, Fourier, Muestreo, Transformadas y Filtros/Control), sin copiar sus accesos duplicados. La app PC mantiene independencia funcional y no incorpora referencias a la calculadora en la interfaz.

## Diseño y análisis

Filtros distingue Analizar, Diseñar, Ajustar, Ideales y por tramos, Convertir y Respuesta temporal. Normalizar ganancia y modificar fase están en Ajustar. Los ideales tienen una herramienta que define, analiza y aplica H, por lo que no quedan exclusivamente bajo Diseño.

Analizar acepta H(s)/H(z) por fórmula o coeficientes y muestra módulo, fase y retardo. Ver polos y ceros obtiene el plano del mismo resultado sin entrar en el editor de diseño. Es una consulta con coordenadas binómicas o polares; incluye raíces y criterio de ubicación de polos. Se calculan bajo demanda para evitar el costo innecesario en FIR largos. La vista de diseño conserva edición con mouse.

El plano respeta los avances de z de la fórmula, cancela los polos artificiales del representante causal en el origen y conserva el aviso de no causalidad. No cancela raíces por cercanía. Las raíces son numéricas: multiplicidades y órdenes altos pueden amplificar errores. Se distingue la ubicación de polos de las condiciones de ROC, causalidad, transferencia propia y estabilidad interna. La pestaña de raíces se invalida al editar H o recalcular para evitar presentar un plano anterior como nuevo.

## Presentación y ayuda

Nombres compactos y descripción breve en el encabezado. Las opciones ocultas ya no imponen su tamaño mínimo a la página activa. En pantallas angostas se apilan controles y acciones; las figuras continúan en ventanas independientes. F1 muestra la ayuda de la opción activa. Se retiran las fichas duplicadas de rutas reemplazadas y se corrigen textos que negaban el FIR por ventana ya implementado.

## Comprobaciones acotadas

- Apertura de todas las opciones agrupadas y su ayuda; preservación de rutas heredadas.
- Envío de señal a la opción activa, sin ofrecer entradas ocultas; conservación de parámetros.
- Raíces digitales y analógicas, avance neto de z, coordenadas polares y ausencia de cambios en el filtro por consultar el plano.
- Actualización e invalidación del plano al modificar H.
- Ancho de 800×600 en muestreo, generación y análisis de filtros: sin desplazamiento horizontal del documento en los casos revisados.
- Búsqueda de una ecuación diferencial abre esa opción dentro de Laplace.

No se repite una campaña matemática completa: la reorganización reutiliza los motores existentes y estas comprobaciones se concentran en navegación, intercambio y el análisis añadido.
