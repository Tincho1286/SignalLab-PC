# Auditoría matemática

## Evidencia posterior a Fase 05

La matriz de `1311df1` integra oráculos de Fourier y muestreo, contratos del Core, comunicaciones y canales, e inferencia y experimentos de Fase 05. Aprobó en los dos sistemas. La verificación posterior a la integración aprobó en `9474626`. Se conservan los informes de origen, semillas, tolerancias y resultados por candidato. [Quality Gate 2.3.1](phase_05/CORRECTIVE_PREVIEW_2_3_1.md) · [Controles de integración](phase_05/PHASE_05_INTEGRATION.md)

| Grupo de validación | Referencias y aspectos cubiertos |
| --- | --- |
| Core y señales | DFT por suma directa, Parseval, índices, fase, escalas, inversión, orígenes de muestreo, aliasing, ROC y validación de trayectorias de persistencia. [Catálogo de oráculos](phase_02c/mathematics/INDEPENDENT_ORACLE_CATALOG.md) |
| Comunicaciones y canales | Mapeo, pulso, ruido, BER/SER de referencia, alineación I/Q, canal multitrayecto y soporte de los modelos de fading, Doppler e interferencia. [Fase 03](phase_03/MATHEMATICAL_AUDIT.md) · [Fase 04](phase_04/MATHEMATICAL_AUDIT.md) |
| Estadística y estimación | Distribuciones y campañas de cobertura, identificación con parámetros conocidos, estimación/filtros lineales, recuperación Monte Carlo y registros de canal. Cinco demostradores, 384 contrastes por sistema en 2.3.1. [Protocolo](phase_05/STATISTICAL_VALIDATION_PROTOCOL.md) · [Fundamentos](phase_05/MATHEMATICAL_FOUNDATIONS.md) |

Al autorizar RF se fijarán los oráculos antes de implementar. Casos base propuestos son unión directa de dos puertos, carga adaptada, abierto/cortocircuito, línea de longitud conocida, cascadas recíprocas y referencias por puerto. Una operación con matriz singular debe producir un diagnóstico de dominio. Para DSP asociado, usar DFT de suma directa, análisis de lóbulos sobre la ventana declarada y derivada de fase de un modelo analítico. Los comparadores externos ayudan a localizar diferencias de convención y cada caso de aceptación debe tener una referencia verificable propia. [Dictamen de preparación](STRATEGIC_REVIEW_POST_PHASE_05.md#dictamen-de-preparación-para-fase-06)

## Auditoría histórica de Fase 00

**Fase 00 · 24 de noviembre de 2026.** Python 3.12.10, NumPy 2.5.0, SciPy 1.18.0 y SymPy 1.14.0 sobre Windows x64. Las pruebas y los contraejemplos verifican convenciones y clases de entradas declaradas. La validez general de un algoritmo requiere justificar los supuestos de cada familia.

## Evidencia ejecutada

`python -B -X utf8 tools/check_math.py` pasó en el árbol local, con **293 pruebas**, sin fallos, errores ni omisiones, y un barrido reproducible de **150 casos**. Semillas `20261103` y `2246119030`. El barrido registra su contrato, huella del código y resultado por familia en `work/math-audit.json`. Revisé las familias registradas en el gate y ejecuté además controles directos con referencias calculadas a mano.

| Familia | Convención y verificación | Alcance que queda abierto |
| --- | --- | --- |
| Fourier | DFT directa sin factor 1/N, inversa con 1/N. CTFT usa rad/s y el paso temporal en la cuadratura. DTFT usa rad/muestra. El barrido cubre desplazamiento, modulación, Parseval, series y pares algebraicos. El control directo de cuatro muestras verificó la diferencia de origen detallada más abajo. | Distribuciones, rejillas muy anchas, acumulación de errores y límites de detección de pares. |
| Laplace | Se distinguen unilateral y bilateral, condiciones laterales iniciales e impulsos. El gate incluye exponenciales, polos repetidos, desplazamientos y soporte acotado. `e^(−2t)u(t)` da `1/(s+2)` con ROC `Re(s)>−2` para la bilateral derecha. | Familias parcialmente resueltas y condiciones paramétricas con fronteras numéricas. |
| Z y ROC | Soporte discreto y potencias de `z`/`z⁻¹`, colas derechas e izquierdas, anillos y exclusiones del origen. La inversa derecha de `−18/(z+1)` entregó `[0, −18, 18, −18, 18]` desde `n=0`, como `−18(−1)^(n−1)u[n−1]`, con `|z|>1`. | Controles cruzados de recirculación CAS → análisis → inversa en el borde de ROC. No asignar ROC a una representación que sólo existe como Fourier. |
| Convolución y correlación | Suma sobre orígenes físicos. Correlación `r[m]=Σ x[n] conj(h[n−m])`. Para `[1+j, 2]` y `[2, j]` con orígenes −1 y 1, se obtuvieron `[2+2j, 3+j, 2j]` y `[1−j, 2, 4]` respectivamente. Los gates también incluyen Dirac, continuo, circular y por bloques en suites específicas. | Ampliar cruces entre métodos y relojes distintos para señales complejas en registros grandes. |
| LTI y realización | Para `H(s)=1/(s+1)`, la evaluación coincidió con `1/(1+jΩ)` en cuatro frecuencias. El gate cubre cancelación exacta, retardos, avances, realimentación y polos. | No confundir estabilidad interna con BIBO. Verificar cancelaciones y tolerancia cuando hay escalas muy distintas. |
| FIR e IIR | Las pruebas cubren longitudes, ventanas, especificaciones y evaluación compleja. Las bandas se expresan en rad/muestra o rad/s según la herramienta. Los extremos certificados de una rejilla siguen siendo mediciones de puntos. | Certificar la búsqueda de mínimo orden o declarar su alcance. Validar con una referencia independiente de puntos extremos que no replique la rejilla del diseñador. |
| Espacio de estados | Para `A=−2, B=3, C=4, D=5`, la frecuencia coincidió con `5+12/(2+jΩ)`. Se mantuvieron los controles MIMO, reloj, ZOH y respuesta bajo condiciones iniciales. | Rango y estabilidad de realizaciones mal condicionadas con tolerancia justificada. |
| Muestreo y reconstrucción | Para `cos(2πt)` a 8 muestras/s, coincidieron ocho muestras `cos(πk/4)`. Se obtuvo alias firmado `+1 Hz` para 9 Hz a 8 Hz. Sinc, lineal y retención obedecen condiciones diferentes. | Error de interpolación y fase en fuentes con reloj parcial, remuestreo sobre entradas grandes, discontinuidades y términos impulsivos. |
| Señales complejas | Referencias de Fourier, correlación y respuesta se compararon como valores complejos. En la aplicación, módulo cero deja fase indefinida y los ejes de espectros tienen unidades propias. | Condicionamiento cerca de ceros, discontinuidades de fase y ausencia de precisión nativa seleccionable. |
| Procesos aleatorios | Bernoulli con `p=1/4`, semilla 123 y PCG64 produjo valores del soporte `{0,1}`. La varianza declarada fue `3/16` y la media del registro quedó a menos de 0,03 de 1/4. El gate incluye una referencia de espectro/normalización y las pruebas específicas revisan AR. | La prueba de una realización no valida distribución ni ergodicidad. Hace falta referencia de PSD y potencia para canales I/Q antes de ampliar. |
| Cuantización | En Q(2,2), `5/8` redondeó a `3/4` con palabra `0011` y una entrada inferior al rango saturó a −2. El gate comprueba precisión, límites y estados de desborde. | Vectores bit a bit de acumulación, cuantización de coeficientes, ceros con signo y distintas políticas de empate. |
| Álgebra simbólica | Pares shifted, indeterminaciones, soporte, `Piecewise`, expresiones de energía/potencia y ecuaciones contrastadas con identidades. CAS y cálculo comparten parte del motor, por lo que una comparación entre ambos puede repetir el mismo defecto. | Parametrizar supuestos de enteros/reales, identificar límites de resolución simbólica y distinguir una fórmula válida de una suma aún no evaluada. |

Los controles adicionales se construyeron con sumas directas, identidades de orden uno, cocientes racionales y valores esperados explícitos. Para operaciones flotantes básicas se usó `rtol=atol=2·10⁻¹³`, holgada frente al error de unas decenas de operaciones binarias con magnitudes pequeñas. Ese margen no se propone para filtros de alto orden o funciones mal condicionadas.

## Hallazgo reproducido M01 · origen de la DFT

La herramienta de DFT independiente trabaja sobre el orden de almacenamiento `m=0,…,N−1`. La DFT superpuesta con DTFT evalúa la misma secuencia en sus índices físicos `n=n₀+m`. El factor que relaciona ambos resultados es `exp(−jωn₀)`.

Con `x[3]=1`, `x[4]=2`, `x[5]=x[6]=0` y `ω=π/2` se verificó `1−2j` en la DFT independiente y `2+j` en la superposición, dentro de la tolerancia. Ambos números siguen sus convenciones y tienen módulo igual. La diferencia cambia la fase y puede interpretarse como un error en el informe si los dos aparecen bajo el mismo nombre.

**Prioridad alta para el contrato.** Identificar fase por origen en el informe, la figura y los metadatos exportados. La conversión debe respetar la inversa y evitar aplicar dos veces la corrección a un resultado que ya use los índices físicos. No cambiar la convención de sesiones antiguas durante la estabilización sin una decisión documentada.

## Tiempos y memoria

| Operación | Entrada | Mediana de cinco ejecuciones después de calentamiento | Pico trazado |
| --- | --- | ---: | ---: |
| DFT centrada | 262.144 muestras constantes | 29,93 ms | 12,26 MiB |
| DTFT directa | 1.024 muestras exponenciales y 1.025 frecuencias | 34,45 ms | 5,07 MiB |

Se fijó `OPENBLAS_NUM_THREADS=1`. La memoria se midió en una ejecución separada con `tracemalloc`. El valor no incluye todo el RSS nativo de Qt, BLAS o procesos hijos. Para repetir, construir `Signal(np.ones(262144))` y `Signal(np.exp(-np.arange(1024)/128))`, cronometrar `operations.dft(..., centered=True)` y `fourier.dtft(..., -pi, pi, 1025)` con `perf_counter`, y medir pico después de `tracemalloc.start()`. Repetir sin otras cargas si se necesita comparar rendimiento entre cambios pequeños.

Una línea base de rendimiento requiere casos por orden de filtro, tamaño de sesión, matriz MIMO, muestras de capturas y operaciones simbólicas con plazo. Aquí los dos resultados son mediciones puntuales, útiles para orientar ese trabajo.
