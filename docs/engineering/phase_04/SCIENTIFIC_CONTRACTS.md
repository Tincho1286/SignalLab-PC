# Contratos científicos de canal

## Multitrayecto determinista LTI

`ChannelPath` describe un retardo entero no negativo en muestras y una ganancia compleja finita. `MultipathSpec` contiene un conjunto ordenado de trayectorias y la opción booleana de normalización. La aplicación acepta la tupla histórica como una configuración sin normalización.

Se suman las ganancias de trayectorias que comparten retardo antes de calcular la salida y el perfil. Por ejemplo, dos trayectorias de ganancia 1 al mismo retardo producen potencia 4 en ese instante. Ganancias opuestas se cancelan. Las muestras fuera del registro se consideran cero. Se conserva el soporte de salida declarado por el mayor retardo, incluso si ese tap se anula.

La respuesta impulsional se entrega en forma dispersa `(retardo, ganancia)`. Sus potencias están en unidades lineales como módulo cuadrado de la ganancia. El promedio de los retardos y la desviación RMS usan esas potencias como pesos. Los momentos de una respuesta nula quedan indefinidos. La normalización opcional fija la suma de potencias de la respuesta impulsional en uno. Una respuesta nula produce un error si se pide normalizar.

Con L muestras por símbolo, el análisis toma como referencia el tap coherente de mayor potencia, el primero en caso de empate. Suma las potencias de los demás taps que coinciden con esa fase de muestreo y divide por la potencia de referencia. Es una medida de ISI del canal a intervalos de símbolo, sin el efecto de los pulsos TX/RX ni de la sincronización. Los tiempos físicos se obtienen dividiendo los retardos en muestras por Fs.

`multipath_frequency` evalúa $H(e^{j\omega}) = \sum_d h[d]e^{-j\omega d}$ en las frecuencias periódicas de una DFT centrada. El algoritmo reduce cada retardo módulo N antes de formar las fases, de modo que los retardos enteros grandes preservan la periodicidad en esos puntos. El resultado usa rad/muestra y convención de frecuencia angular. [Modelo de banda base](https://web.stanford.edu/~dntse/papers/ch1%2B2.pdf).

El resultado temporal usa metadatos `communications_multipath` esquema 2, con la configuración original, su indicador de normalización y la huella de la señal de entrada. Los resultados escritos con esquema 1 conservan su representación histórica. La normalización opera sobre el modelo, de modo que se aplica también a sus diagnósticos.
