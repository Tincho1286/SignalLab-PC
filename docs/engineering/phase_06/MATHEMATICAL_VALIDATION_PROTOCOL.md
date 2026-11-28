# Protocolo de validación matemática

El protocolo compara datos, unidades, dominio, clase de fallo y procedencia. Los casos lineales de escala ordinaria usan tolerancia relativa `2e-12` y absoluta `2e-13` para datos adimensionales, o su equivalente en las unidades de la referencia. Las pruebas de rango y mal condicionamiento requieren diagnósticos explícitos. Fijar tolerancias de modelos estadísticos, estimadores y discretización junto con cada demostrador antes de ejecutarlo.

| Demostrador | Oráculos independientes y errores observables |
| --- | --- |
| A · Redes | Derivar ondas desde KCL/KVL de carga, impedancia serie/derivación y atenuador. Unión ideal, abierto, corto, referencias desiguales y transmisión no recíproca. Verificar resultados y cancelación de conversiones, cascada y reducción. |
| B · Adaptación | Ecuación de la línea terminada, transformaciones de cuarto y media onda y transformación de impedancias con reactancias conocidas. Inspección Smith contra $\Gamma=(z-1)/(z+1)$ y $z=(1+\Gamma)/(1-\Gamma)$. |
| C · Filtros | Polinomios de Bessel inversos para órdenes bajos, Butterworth de primer orden, polos, escala y retardo analítico. Respuestas temporales con condiciones conocidas. |
| D · Enlace | Sumas en dB con referencias explícitas, producto de ganancias, $kTB$, cascada de ruido derivada por etapa y dos tonos del modelo cúbico. |
| E · Espectros | Suma compleja directa y frecuencias explícitas para DFT, CZT y Zoom FFT. Ventanas de referencia, tono fuera de bin y calibración del origen. |
| F · Experimentos | Archivo Touchstone asimétrico y con referencias distintas. Barrido con fórmula, reanudación y guardado/reapertura con igualdad exacta de matrices y huellas. |

Los ensayos cruzados con comparadores externos deben documentar versión, unidades y definición de ondas. Las identidades de ida y vuelta complementan los circuitos y cálculos directos. [Referencias](AUDIT_AND_SCOPE_REPORT.md#referencias-y-adopción)
