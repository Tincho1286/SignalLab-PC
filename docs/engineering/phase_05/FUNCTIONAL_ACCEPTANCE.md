# Revisión funcional de la Preview 2.3.0

La revisión se puede hacer en Windows o Linux con una copia temporal del proyecto y una carpeta vacía para la campaña. Para registrar una diferencia, guardá el resultado, los parámetros, la semilla, el sistema operativo y la versión que muestra la aplicación.

1. **Cambiar entre herramientas.** Abrí dos herramientas con **Ctrl+K**, dejá un borrador distinto en cada una y alterná varias veces. Los controles deben responder al cambio y conservar los dos borradores. Si una figura está cerrada, su acción debe seguir disponible. Enviá una señal periódica a Serie discreta de Fourier y comprobá que el cálculo toma el período entero.
2. **Generar y analizar una distribución.** En **Generar realización**, elegí Poisson con media 2, dos réplicas, 1024 muestras y semilla 123. La consulta CDF en 1 debe dar aproximadamente 0,40600585. Repetí la generación con la misma configuración y verificá que se conservan los valores de cada réplica. Enviá una al panel descriptivo y comparala con la misma ley.
3. **Simular un modelo temporal.** En **Analizar modelo AR, MA o ARMA**, ingresá `1, -0.5` como denominador, ruido sin media ni desviación, estado manual `8` y dos muestras de calentamiento. Pedí tres muestras. Deben ser 2, 1 y 0,5. Variá el coeficiente del polo en una segunda consulta con ruido activo y revisá la comparación espectral.
4. **Analizar un registro de canal.** En la herramienta de canal, calculá un caso de fading y enviá el coeficiente a Estadísticas e histograma. Comprobá que el reloj del registro se conserva. Abrí su densidad espectral y revisá sus ejes y unidades.
5. **Recuperar una campaña.** En Monte Carlo, ejecutá varias réplicas con semilla fija y una carpeta vacía. Cancelá después de que haya terminado algún bloque y continuá desde la misma carpeta. Los resultados deben coincidir con una repetición completa con la misma configuración. Guardá el proyecto y volvé a abrirlo para revisar resultados y referencias.
6. **Verificar el actualizador.** Comprobá el canal Preview desde **Ayuda → Buscar actualizaciones**. En el canal estable, la versión seleccionada sigue siendo 2.0.0. La autorización de integración se registra después de la aceptación funcional.

[Ejemplos reproducibles](INTEGRATION_CATALOG.md) · [Política de actualizaciones](../RELEASE_POLICY.md)
