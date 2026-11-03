# Fiabilidad matemática

SignalLab conserva una definición matemática de la entrada junto con cada resultado de Z, Laplace y Fourier. Incluye la fórmula original, la expresión efectiva exacta, la variable, el dominio, el soporte o intervalo de integración, las condiciones de entrada y los valores completados por continuidad. La representación interna conserva los índices enteros y las constantes exactas.

## Valores por continuidad y dominio

En una secuencia, cada muestra contribuye a la suma. Por eso sin(pi*n)/(pi*n), completada con 1 en n=0, mantiene esa muestra al calcular Z o DTFT, incluso con desplazamientos o soportes truncados. Un valor finito asignado por tramos tiene prioridad sobre la extensión automática. Un polo real entre dos índices no se trata como una muestra indefinida; un polo sobre un índice del soporte se rechaza cuando puede identificarse exactamente.

En una integral ordinaria, cambiar el valor aislado de una función no cambia su transformada. La definición original permanece registrada, pero las ramas aisladas pueden retirarse de la expresión de integración para facilitar el reconocimiento de los pares. Los impulsos Dirac mantienen sus pesos y su tratamiento de distribuciones.

Z y DTFT comparten la preparación de la secuencia. La sustitución z=exp(i*w) utiliza los pares de Z sólo cuando sus condiciones permiten el círculo unitario completo. Los pares de Fourier que existen únicamente sobre ese círculo, como la sinc bilateral, conservan su tratamiento propio.

## Reconocimiento independiente de la forma escrita

Antes de aplicar un par de Z se recuperan los factores separables que una expansión pueda haber combinado dentro de un denominador. El reconocimiento se basa en la potencia afín y la razón geométrica, no en una cadena literal. Para Fourier se conserva la fase de seno/coseno hasta reconocer el desplazamiento; las identidades de índices enteros se aplican después de separar los valores aislados. Los centros fraccionarios conservan su fase en cada imagen espectral y los valores asignados por tramos se incorporan como correcciones discretas.

## Convergencia en el círculo unitario

La comprobación de una ROC abierta no se utiliza como único criterio para Fourier. Las series geométricas amortiguadas convergen absolutamente en su región; para potencias recíprocas, el motor comprueba por separado la convergencia absoluta o la de Dirichlet sobre el borde. La condición de la expresión conserva las frecuencias excluidas. Una continuación racional del escalón no se declara por este camino como una DTFT ordinaria.

## Estado de un resultado

El informe distingue una expresión obtenida, una expresión con condiciones, un resultado parcial, un cálculo sin resolver y la ausencia de una región de convergencia. Una operación pendiente dentro de una fórmula no se convierte en una solución por tener activada una marca de resultado evaluado. Obtener una fórmula no equivale a demostrar independientemente su identidad.

La definición y las notas de continuidad se conservan en Resultados, la exportación del registro y la procedencia del resultado enviado al CAS. Las condiciones originales acompañan la expresión importada; no se convierten automáticamente en supuestos nuevos de la hoja CAS.

## Entrada exacta y conversión numérica

Los campos escalares y los coeficientes comparten el analizador de fórmulas. Las fracciones y los decimales se conservan como valores exactos durante el álgebra: `10^20 + 1 - 10^20` produce `1`, y `0.1 + 0.2 - 0.3` produce `0`. La conversión a números de máquina se realiza después. Los campos enteros verifican el valor exacto y no redondean índices ni cantidades fraccionarias.

Un campo real rechaza un valor complejo genuino; una potencia, pi o la notación científica no se consideran complejos por su sintaxis. Las funciones con restricciones reales, como floor o el escalón, admiten resultados intermedios representados como complejos con parte imaginaria exactamente cero y rechazan argumentos fuera de su dominio. Las ramas principales de asin y acos coinciden entre las fórmulas y su evaluación numérica.

Los valores no finitos y los componentes que desaparecerían por estar por debajo del rango numérico se rechazan al proyectar constantes. También se detecta cuando normalizar un filtro por a₀ convertiría un coeficiente no nulo en cero. Esto no elimina el error de redondeo propio del cálculo numérico; evita sustituciones silenciosas en esos pasos.

## Ecuaciones y ventanas

Las ecuaciones diferenciales y en diferencias conservan la misma definición de entrada que las transformadas. La recurrencia comparte la separación de tramos e índices usada por Z: la sinc con corte pi conserva la muestra central y se simplifica como impulso, sin quedar innecesariamente como una suma pendiente. Las condiciones iniciales siguen indicando el historial anterior al índice de arranque.

La generación de ventanas, el enventanado de h[n] y la estimación espectral utilizan las mismas muestras de ventana simétrica. La longitud de la ventana sigue siendo independiente del registro de h[n]. Los extremos definidos como cero mantienen ese valor exacto y Kaiser usa una evaluación escalada para valores grandes de beta.

## Control antes de construir un portable

Los constructores oficiales de Windows y Linux ejecutan `tools/check_math.py` antes de empaquetar. Si falla, la construcción se detiene. El contrato `mathematical-families-v2` contiene 69 pruebas con variantes, agrupadas por familia y con un grupo adicional de propiedades de transformadas. Cada grupo exige una cantidad mínima de casos y no admite omisiones silenciosas:

| Familia | Referencias principales |
|---|---|
| Transformadas | Pares de Z, Laplace y Fourier, inversas, ROC, soporte, continuidad y transporte de resultados |
| Propiedades de transformadas | Escalas y desplazamientos de sinc, expresiones equivalentes, centros fraccionarios, bordes, imágenes espectrales y proceso simbólico de la interfaz |
| Carga de expresiones | Aritmética exacta, constantes, ramas principales, variables reservadas y límites numéricos |
| Sistemas y filtros | H por fórmula, coeficientes y raíces; impulso, historial, avances, retardos, polos en cero, fase y bilineal |
| Ecuaciones | Sustitución de la solución en la ecuación original, condiciones iniciales y coherencia entre fórmula y muestras |
| Fourier y medidas | DFT por definición, Parseval, origen de DTFT, superposición, escalas de integración, PSD, energía y potencia |
| Señales y ventanas | Alineación, convolución y correlación complejas, inversión temporal, ventanas y longitud de FIR |
| Espacio de estados | Orden temporal de estados y salida, término directo y solución exponencial con estado inicial |
| Muestreo y precisión | Alias angular, interpolación sinc, redondeo y saturación en punto fijo |
| Señales aleatorias | Media compleja, potencia, varianza y autocovarianza con divisores N y N−|k| |

El registro distingue el resultado de cada familia, además del resultado global. El retardo de grupo completa los límites de factores comunes exactos del mismo orden y conserva la indefinición en ceros y polos genuinos; no realiza cancelaciones por tolerancia. Las comprobaciones de Fourier continuo sobre registros se refieren a la cuadratura o interpolación declarada, no a una transformada exacta de una función desconocida entre las muestras.

Las referencias se expresan mediante fórmulas conocidas y valores de borde; las comprobaciones de ida y vuelta son complementarias. GitHub ejecuta el mismo control en Windows y Linux al cambiar el código matemático y en las propuestas de cambios. La procedencia de cada portable registra el resultado y las versiones de las dependencias.

Para ejecutarlo localmente:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 tools/check_math.py
```

El informe local se guarda en `work/math-checks.json`. Este control cubre referencias concretas: no certifica todas las expresiones posibles ni reemplaza las condiciones de convergencia de cada cálculo. Las comparaciones numéricas aisladas tampoco constituyen una prueba de identidad general.

## Barrido preventivo de parámetros y representaciones

`tools/audit_mathematics.py` genera 56 casos por semilla. La construcción utiliza dos semillas: una fija y otra derivada de la huella de los motores y las referencias del barrido. Se normalizan los saltos de línea para que la huella y los parámetros coincidan entre Windows y Linux. El conjunto de 112 casos explora variaciones de constantes, ganancias, centros enteros y fraccionarios, frecuencias, orígenes, polos, factores comunes, condiciones iniciales y expresiones del CAS.

Las comparaciones de filtros utilizan respuestas y retardos de primer orden conocidos; las de Fourier utilizan sumas de definición; las ecuaciones se comparan con soluciones forzadas conocidas. Las conversiones del CAS comprueban identidades, raíces, restricciones de dominio y matrices exactas. Los resultados pendientes donde se espera una solución forman parte de los fallos.

El barrido se ejecuta en un proceso propio con un plazo de 20 segundos por caso. Una excepción, un resultado incompleto o un plazo agotado impiden aprobar el portable. El informe `work/math-audit.json` incluye semillas, parámetros, referencia de cada caso, tiempos y huella del código. La procedencia del portable incluye su resumen; GitHub conserva los informes completos como artefactos del control matemático.

Para reproducir una semilla indicada en un informe:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 tools/audit_mathematics.py --seed 20261103
```

Un barrido satisfactorio amplía la evidencia para los casos explorados. No convierte una comprobación numérica aislada en una prueba de identidad general ni certifica todas las entradas posibles.
