# SignalLab PC 0.74 · escritorio científico y Aleatorias visible

27/10/2026. Compilación de desarrollo hacia 1.0.

## Cambios

- Nueva apariencia integral de escritorio: superficies claras neutras, bordes finos, acentos azules, selección discreta y controles compactos. Se conserva la organización actual por problemas, sus documentos y opciones internas.
- Campos de fórmulas y números con fuente monoespaciada; informes con tipografía de lectura matemática, fórmulas oscuras y fondo blanco. Exportación del informe con la misma paleta.
- Biblioteca, esquemas de bandas, dibujos de las funciones básicas y regiones de convergencia adaptados al nuevo contraste. Figuras externas con fondo claro y colores distinguibles.
- Señales aleatorias vuelve a la navegación principal y al inicio, junto a las otras seis áreas. Se conservan generación, estadística y autocorrelación/autocovarianza dentro de su problema agrupado. Su ampliación puede esperar; sus funciones actuales siguen disponibles.
- Nombres de distribuciones en español en el informe de generación y explicación de vistas de autocorrelación coherente con su presentación inicial.

## Comprobación dirigida

Se verificó la presencia de las siete áreas y los siete grupos del inicio. Se generó una realización de 64 muestras y se reutilizó en estadísticas y autocorrelación, calculando en cada destino. Se comprobó además un informe de energía/potencia, un diseño FIR y su ayuda ilustrada; se revisaron capturas del escritorio, informes y ayuda. La entrada de Aleatorias se comprobó a 800×600 y 640×480 sin desplazamiento horizontal del documento. No se realizó una campaña general de pruebas numéricas ni se modificaron algoritmos de cálculo en esta entrega.

Se mantiene la corrección 0.73.1: un solo acceso a polos y ceros dentro del análisis. Las versiones anteriores del portable se conservan. La aplicación todavía no se declara 1.0 estable; el alcance y las carencias pendientes siguen en CIERRE_1.0.md y COBERTURA_SYS_I_II_ACTUAL.md.
