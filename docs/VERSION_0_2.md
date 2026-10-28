# SignalLab PC 0.2 — desarrollo en curso

## Primera versión conservada

La versión 0.1.0 está congelada en `releases/v0.1.0/`:

- SignalLab-PC-v0.1.0.exe
- SignalLab-PC-v0.1.0-source.zip
- manifest.json con SHA-256 y estado real
- LEEME.txt

El EXE de esa versión es el generado antes de esta ampliación. No se sobrescribe al compilar la siguiente versión. Sigue siendo una versión de desarrollo, no una declaración de paridad HP.

## Incorporaciones de 0.2

| Área | Implementación nueva | Alcance y límites pendientes |
|---|---|---|
| Señales | Plantillas, funciones adicionales y expresiones por tramos con `where(condición,a,b)` o expresión condicional; evalúa sólo la rama elegida | Estados N/D/infinito, Dirac ideal general y clasificación global todavía pendientes |
| Muestreo | Expresión temporal a secuencia; Fs/t0 en metadatos; análisis de alias de un tono | Laboratorio completo con filtro previo, comparaciones analíticas y reconstrucción arbitraria pendiente |
| Cambio de tasa | Diezmado con fase local HP, expansión, interpolación lineal/ZOH/SINC | Diezmado sin filtro implícito; no declara rechazo de alias. SINC usa toda la entrada finita y recorta la salida a su intervalo |
| Reconstrucción | ZOH, lineal y SINC sobre primera a última muestra, L subdivisiones | Ventana arbitraria y colas infinitas pendientes |
| Cuantización | Extremos HP, redondeo/FLOOR, alineación de cero, saturación, error y SNR en intervalo de filas | Hasta 52 bits por representación float64, no el tope HP de 24; gráficas de comparación dedicadas pendientes |
| Punto fijo | Fracciones exactas, saturación, redondeo/truncamiento, código con signo y complemento a dos | Sin tope HP de 32 bits; sujeto a memoria y representación de enteros de Python |
| Fourier | DTFT global, DFT/DTFT en bins exactos, series continuas/discretas y síntesis, CTFT/ICTFT numéricas | Fourier simbólica y distribuciones, trenes ideales, todas las vistas HP y comparación de métodos pendientes |
| Densidades | Densidad de energía, periodograma anterior, PSD calibrada y Welch por segmentos; ventanas simétricas HP | Bilateral, sin eliminación de media implícita; auditoría de calibración pendiente |
| Control/LTI | Segundo orden, respuesta continua, realimentación positiva/negativa, lugar de raíces por K | H(s) propia; Dirac directa del impulso se informa en metadatos; sistemas impropios requieren tratamiento de distribuciones. Locus numérico finito, polos en infinito no trazados |
| Transformadas | Laplace unilateral e inversa causal; Z finita; Z inversa racional por expansión en infinito; EDO constante con condiciones iniciales | No equivalencia bilateral automática; Z inversa entrega N términos de la rama derecha; otros soportes/ROC y EDO general pendientes |
| Teoría | 20 secciones estáticas SSTheoryView importadas del código HP, búsqueda y línea de procedencia | No incluye toda la ayuda dinámica. El texto original conserva referencias a controles HP y funciones todavía pendientes |
| Interfaz | Banco evita sobrescribir nombres repetidos; ejes enteros exactos en tabla/CSV; progreso y cancelación | Progreso por bloques; rutinas nativas monolíticas responden al finalizar. Historial persistente y mediciones especializadas pendientes |
| CAS | Proceso separado con protocolo JSON y parser AST restringido, sin eval/parse_expr de texto libre | Cancelación termina sólo el proceso de cálculo; resultados simbólicos sin evaluar se informan expresamente |

## Estado de validación

No se agregaron ni ejecutaron pruebas en este lote. Las 33 pruebas históricas documentadas corresponden a una revisión anterior y **no validan estas incorporaciones**. Compilar el EXE tampoco prueba el arranque ni la corrección matemática.

La versión completa debe auditarse contra el inventario de 109 menús estáticos y sus ramas dinámicas. El objetivo sigue siendo todas las capacidades de HP Prime; este documento registra progreso, no finalización.

## Continuación prioritaria

1. Revisión matemática y de interfaz de los módulos nuevos, y validación cuando sea solicitada.
2. Estados especiales y discontinuidades sin convertir N/D/infinito en cero; Dirac y distribuciones.
3. Convolución/correlación continuas, modelos por celdas y auto periódica continua.
4. Completar el laboratorio de aliasing, filtros antialias/antiimagen y reconstrucción fuera del registro.
5. Soportes y ROC simbólicos alternativos, Fourier simbólica, energía/potencia global y propiedades.
6. Persistencia de sesiones, editor gráfico de polos/ceros, cursor y reutilización completa de cálculos.
7. Auditoría de cada ruta HP, avisos de dependencias, EXE final independiente y documentación PC definitiva.
