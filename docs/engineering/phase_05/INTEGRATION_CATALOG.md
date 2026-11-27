# Reutilización de datos entre laboratorios

| Origen | Registro que se conserva | Análisis disponible |
| --- | --- | --- |
| Canal AWGN | Señal de salida con reloj, semilla y potencia nominal y medida | Estadística descriptiva, correlación, PSD. El demostrador C usa el registro ruidoso y la referencia limpia para medir el error de Wiener sobre muestras reservadas. |
| Rayleigh, Rician y Clarke | Coeficientes complejos por trayectoria, unidades, reloj y subflujo | Distribución de envolvente por módulo, momentos de componentes, ACF y PSD. Las curvas de fase y envolvente propias del canal también siguen disponibles. |
| Ruido de fase | Trayectoria de fase en radianes | Estadística de la fase observada. El demostrador E compara la varianza de los incrementos con el ancho de línea y el reloj. |
| Experimentos de enlace | Registros temporales, sincronización y métricas BER, SER y EVM | Los registros temporales se reutilizan en estimación, espectros y estadística. Se conservan las definiciones y validaciones de cada métrica del enlace en el flujo original. |
| Barridos | Diseño, réplicas y comprobación de cada bloque | Las campañas de Monte Carlo comparten la escritura atómica y el bloqueo entre procesos. Los diseños mantienen sus propios contratos y resultados. |

Para analizar un canal desde el Workbench, calculá el canal y buscá su realización en **Resultados**. Elegí **Usar señal en… › Señales aleatorias › Estadísticas e histograma** y seleccioná **Módulo** para la envolvente. La selección transmite el identificador del registro, las muestras y su contexto de tiempo. Los coeficientes pueden pasar también a **Densidad de potencia** desde el mismo proyecto.

La prueba automatizada `test_channel_coefficients_feed_statistics_without_an_export` parte de la herramienta de canal, reutiliza sus coeficientes y compara la media de la envolvente con la suma directa de módulos. También verifica el reloj y el origen registrado del análisis.

## Demostradores

```sh
python -B -X utf8 tools/statistical_demonstrators.py --output work/phase05-demonstrators
```

Elegí una carpeta nueva para que la prueba de cancelación y reanudación vuelva a ejecutarse. Cada caso emite un informe JSON con las observaciones, los valores de referencia y sus tolerancias. El caso D conserva los recuentos y su proyecto de Monte Carlo. El E guarda un proyecto con una realización por tipo de canal y sus resultados derivados. Los estudios usan diseños y semillas fijos. Los identificadores de registros de cada proyecto se asignan al guardarlo.

| Caso | Contraste principal |
| --- | --- |
| A | Dos tamaños de muestra y dos distribuciones. Media, máxima verosimilitud y cobertura de intervalos en réplicas independientes. |
| B | AR, MA y ARMA. Varianza y autocorrelación cerradas, Parseval, error de coeficientes, diagnóstico de residuos y origen del pronóstico. En AR se comparan mínimos cuadrados, Yule–Walker y Burg. |
| C | Wiener frente a su ganancia y MSE teóricos. Kalman frente al posterior escalar por lote. LMS, NLMS y RLS sobre el mismo ajuste y tramo de validación. |
| D | Tres probabilidades conocidas y números aleatorios comunes. Conservación de 32 réplicas al cancelar, coincidencia de la campaña reanudada con una nueva, intervalos y reapertura. |
| E | Veinticuatro realizaciones de 1024 muestras por tipo de canal. CDF de envolvente por fórmula cerrada o mezcla gamma, potencia, correlación, PSD de Clarke y varianza de incrementos de fase. |

En la matriz, `qualify_statistics.py` ejecuta los casos con un guardia que rechaza importaciones de Qt. También verifica que la misma realización Poisson y sus estadísticas coincidan entre Python y la consola. El verificador liga los informes al SHA del candidato y coteja sus huellas y valores. [Protocolo estadístico](STATISTICAL_VALIDATION_PROTOCOL.md)
