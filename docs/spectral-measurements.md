# Medidas espectrales

[← Herramientas](tools.md)

En **Medir un espectro** podés calcular cuánto aporte queda dentro de una banda y localizar sus picos. Cargá una fórmula o un registro, o elegí un espectro, una densidad o una DFT desde Resultados.

## Elegir qué se mide

La interpretación automática utiliza el tipo y la normalización del resultado generado en SignalLab. Para una densidad ingresada manualmente, elegí su convención explícitamente.

| Entrada | Medida |
|---|---|
| Espectro complejo X angular | Energía, integral de \|X\|²/(2π) |
| X(f) en Hz | Energía, integral de \|X(f)\|² |
| DFT | Energía por Parseval, suma \|X[k]\|²/N |
| Densidad de energía | Integral de la densidad, con el factor angular correspondiente |
| PSD Sx angular | Potencia, integral de Sx/(2π) |
| PSD en Hz o potencia por unidad del eje | Potencia, integral directa |
| Respuesta H | Área de \|H\|² en la unidad del eje, sin factor de Parseval |
| Coeficientes de serie normalizados | Potencia, suma \|c[k]\|² |
| Líneas de potencia conocidas | Suma de pesos divididos por 2π |

Los impulsos de frecuencia no se interpretan como alturas finitas ni se elevan al cuadrado. Una densidad de fluctuaciones excluye la línea de media en cero; el informe lo indica. El periodograma antiguo sin calibración debe recalcularse con un estimador calibrado antes de medir potencia.

## Energía y Parseval

La densidad espectral de energía integra |X(ω)|² por trapecios sobre la banda disponible. Si la entrada es una DFT completa, el informe agrega la suma |X[k]|²/N por Parseval. Esa suma cubre todo el período y la integral abarca los extremos del intervalo dibujado.

Para contrastar la DTFT de un registro de N muestras con su energía temporal, elegí un período de 2π y al menos N+1 puntos si incluís los dos extremos. En continuo, la referencia temporal integra el registro muestreado y la banda de frecuencia cubre parte del espectro. Con paso temporal Δt, una banda mayor que 2π/Δt puede incluir réplicas de la aproximación muestreada.

## Bandas y porcentajes

Agregá una fila por banda con su nombre, inicio y final. Se admiten expresiones como `pi/4` y `1e-3`. Dejar un extremo vacío utiliza el límite disponible. Las bandas deben estar contenidas en ese intervalo: la herramienta no extrapola el espectro.

Para una curva, la herramienta integra la densidad interpolada entre muestras. Para coeficientes DFT o líneas espectrales, suma los aportes desde el primer extremo y excluye el último. Así, dos bandas contiguas cuentan una sola vez el coeficiente del borde. Agregá otra banda si querés incluir el reflejo de una banda positiva.

El porcentaje se refiere al total disponible. Si las bandas se superponen, sus porcentajes no forman una partición; el informe lo advierte. Un intervalo parcial no demuestra que el espectro sea cero fuera de él.

En **Espectro y bandas**, elegí una fila y activá **Seleccionar banda con el mouse** para arrastrar sus extremos. Cambiar la selección prepara la entrada y marca el resultado como pendiente; es necesario recalcular. Los cursores A/B se suspenden durante esta selección, y zoom o desplazamiento la desactivan para evitar acciones simultáneas.

## Acumulada, centro y ancho

La fracción acumulada muestra cuánto peso se ha reunido desde el extremo inferior y termina en 1. Para bins y líneas es escalonada; en curvas se muestran sus valores en los puntos calculados. Es una medida sin fase y no puede sustituir al espectro en una inversa.

El centro espectral es el promedio de frecuencia ponderado por la medida. El ancho RMS es la desviación cuadrática respecto de ese centro, expresada en la unidad del eje. Ambos describen el intervalo disponible, sin certificar una banda ocupada. En ejes periódicos dependen del corte elegido para el período. Si el peso total es cero, ni la fracción ni esos momentos están definidos.

## Picos medidos y estimados

El nivel mínimo descarta pesos por debajo del umbral en dB respecto del máximo. La prominencia compara cuánto sobresale un pico de su entorno con el peso máximo; no representa su fracción de energía. Las mesetas quedan identificadas. Un extremo de una curva puede ser máximo del intervalo, pero no tiene prominencia definida.

La tabla conserva la coordenada medida y, si se solicita, una estimación entre bins mediante tres puntos del logaritmo del peso. Esta aproximación se muestra en otra columna: no cambia las muestras ni mejora la resolución física del registro.

## Potencia por banda en STFT

En la herramienta STFT, **Potencia por banda** integra la densidad calibrada de cada ventana y genera una curva por intervalo. El valor corresponde a potencia del tramo ponderada por w², sin quitar la media. El relleno con ceros puede reducir el nivel de las ventanas de los extremos.

Una entrada discreta utiliza rad/muestra y un índice de ventanas. Si registra Fs, puede utilizar rad/s y segundos. La curva nativa conserva el reloj Fs/salto y la correspondencia de cada ventana con su centro original. Una entrada continua utiliza rad/s y segundos. Cambiar las unidades no altera la potencia integrada.

Los informes, tablas y curvas se registran en Resultados y se pueden exportar o reutilizar en destinos compatibles. Las tablas CSV incluyen la unidad, la regla de integración y los extremos numéricos utilizados.
