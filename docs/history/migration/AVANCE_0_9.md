# Avance 0.9 — cobertura de correlación y edición de muestras

## Funciones recuperadas y ampliadas

Los menús HP 44–50 motivaron dos familias explícitas: correlación discreta y correlación continua. Ambas permiten auto/cruzada, finita/periódica y las escalas que correspondan. En discreto se conservan orígenes módulo N. En continuo periódico, N muestras representan un periodo T=N*dt sin repetir el extremo, con interpolación lineal cerrada. La integración de productos de segmentos es exacta en los retardos de la rejilla, salvo errores flotantes. La normalización de autocorrelación equivale a R(tau)/R(0); la cruzada usa sqrt(Ex*Eh). No se resta la media.

La correlación algebraica permite integral bilateral o integral de un periodo y conserva la conjugación compleja. En modo periódico se requieren fórmulas periódicas con el periodo indicado; no se inventa una extensión periódica de expresiones arbitrarias.

La nueva UI recupera la tabla de muestras: páginas de 1000 filas, edición real/imaginaria, ajuste de nombre/origen/paso y publicación de un nuevo objeto. El original permanece intacto. Guardar proyecto incorpora borradores pendientes; abrir otra entrada también preserva el borrador anterior en el proyecto.

## Evidencia

81 pruebas aprobadas, registro en work/regression-0.9.txt. Incluyen sumas explícitas para correlación circular con orígenes diferentes, cuadratura independiente para señales complejas periódicas, energía y cotas de normalización, gaussianas bilaterales, senos complejos periódicos, opciones UI y edición de la muestra absoluta 1003 desde la segunda página. Se verifica también la recuperación del borrador guardado en proyecto.

## Pendientes

No se declara cobertura matemática universal ni paridad HP completa. Continúan pendientes señales con estados especiales, distribuciones, auditoría de todos los menús restantes, gráficos avanzados, modelos de sistemas ampliados y otros puntos de OBJETIVO_LABORATORIO_PC.md. La tabla usa números complejos finitos y el modelo actual de señal; no representa Dirac como una muestra de amplitud finita.
