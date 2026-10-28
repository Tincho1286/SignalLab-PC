# SignalLab PC 0.67 — navegación por operaciones y carga rápida

## Estructura

Se reemplaza la navegación basada en 16 documentos y sus selectores anidados por un explorador de áreas, secciones y operaciones. El inicio presenta seis áreas principales: Señales, Sistemas LTI, Diseño de filtros, Fourier y espectros, Muestreo y A/D, Laplace y Z. Las herramientas estadísticas existentes siguen accesibles en su área secundaria, sin ampliaciones de alcance.

El catálogo del área explica qué hace cada operación y la abre directamente. La búsqueda recorre las 72 operaciones existentes, sus descripciones y términos alternativos: por ejemplo, retardo de grupo lleva al análisis de sistemas. El explorador, el catálogo, el menú Herramientas y Operaciones usan la misma ubicación. Los nombres de las pestañas reflejan la operación activa.

Sistemas LTI contiene análisis de transferencia, respuesta temporal, conexiones, convolución, correlación y espacio de estados. Diseño de filtros contiene síntesis FIR/IIR/analógica, diseño por raíces, ajustes de ganancia/fase, ideales y conversión. La consulta de polos y ceros permanece en análisis. Los contenedores internos y las rutas antiguas se conservan para mantener datos, resultados y envíos; sus selectores repetidos se retiran de la pantalla.

## Carga y cálculo

- Una acción de cálculo en la cabecera, siempre en la misma posición; Ctrl+Enter ejecuta esa acción.
- Entradas de señal con botones visibles Expresión, Muestras e Importar. Fórmula y Por tramos también se eligen directamente.
- Crear una señal permite elegir discreta o continua. Cada dominio conserva sus propios datos. Se utilizan los modelos y cálculos numéricos existentes.
- Coeficientes en una línea para pegar listas, con tabla de potencias opcional. La tabla y la línea se sincronizan; pi, fracciones, notación científica y complejos conservan el mismo parser.
- La definición del sistema y el intervalo de cálculo quedan junto a los datos. Exportar, reutilizar y consultar polos/ceros quedan junto al resultado.
- Los gráficos siguen en ventanas independientes. La ayuda conserva sus conceptos por herramienta y muestra su ubicación actual.

## Pantallas pequeñas

El catálogo pasa a una columna; el explorador reduce su ancho y los nombres largos pueden ocupar varias líneas. Los formularios se apilan; sus controles usan el desplazamiento del documento para evitar barras internas superpuestas. Los modos de entrada y los coeficientes usan su altura natural y no se estiran para llenar el panel.

## Comprobaciones acotadas

Cobertura de las 72 operaciones en el catálogo; apertura directa de herramientas representativas; búsqueda por retardo; ayuda contextual FIR; cálculo desde la cabecera; entrada por muestras; generación continua; reutilización de registros conservando valores y eje; sincronización línea/tabla de coeficientes; pi y 10^(-3); conversión por fórmula; análisis de raíces. Comprobados casos de generación, análisis, FIR y muestreo a 800×600 y 640×480 sin desborde horizontal del documento. Se inspeccionaron capturas del inicio, el catálogo y el análisis. Estos controles se limitan al rediseño y no repiten una campaña matemática general.

La versión continúa en desarrollo hacia la primera estable. No se afirma cobertura matemática ilimitada ni una revisión visual exhaustiva de cada combinación de campos.
