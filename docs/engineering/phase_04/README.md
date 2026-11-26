# Fase 04 · Canales

La fase parte de `a94cd37`, la integración aprobada tras validar la 2.1.1 Preview. Amplía el canal AWGN de Fase 03 con modelos de propagación e imperfecciones del enlace. [Roadmap](../ROADMAP.md)

## Multitrayecto con retardos enteros

Para una señal discreta finita, cada trayectoria desplaza la entrada $d_k$ muestras y la multiplica por una ganancia compleja $a_k$. El canal calcula $y[n] = \sum_k a_k x[n - d_k]$. Los retardos son enteros no negativos. Las trayectorias con igual retardo se superponen con su fase. La entrada vale cero fuera del registro y la salida conserva las colas de todos los caminos. [Modelo de banda base, Tse y Viswanath, §2.2](https://web.stanford.edu/~dntse/papers/ch1%2B2.pdf)

El primer índice y el reloj de la salida coinciden con los de la entrada. Para $N$ muestras se devuelven $N + \max(d_k)$, incluso si una ganancia se declara igual a cero. Si se conoce $F_s$, cada retardo equivale a $d_k/F_s$ segundos. Las ganancias controlan la amplitud y fase sin normalización automática.

### Reproducir el cálculo

En el escritorio, abrí **Comunicaciones → Canal multitrayecto**. Cargá la entrada y escribí una trayectoria por línea. Los gráficos y el informe aparecen junto al resultado reutilizable. La vista I/Q muestra las primeras 512 muestras, como en las demás herramientas de comunicaciones. El registro guardado conserva toda la salida.

```text
0 = 1
2 = -i/2
```

Con una entrada que contiene $1+2i$ y $3-i$, la salida esperada es $1+2i,\ 3-i,\ 1-i/2,\ -1/2-3i/2$.

```python
from signallab_pc.communications_channel import ChannelPath, apply_multipath
from signallab_pc.model import Signal

x = Signal([1 + 2j, 3 - 1j], origin=-1)
y = apply_multipath(x, (ChannelPath(0), ChannelPath(2, 0, -0.5)))
print(y.axis, y.values)
```

```sh
python -m signallab_pc communications multipath --signal entrada.slbin --path=0=1 "--path=2=-i/2" --output canal.slproj
```

### Ejecución y validación

El cálculo suma copias por bloques y evita construir un FIR denso entre ecos. El trabajo crece con el producto de las muestras por las trayectorias activas. La reserva se estima con el tamaño de salida, la cantidad de trayectorias y un bloque temporal. El contexto de ejecución admite cancelación entre bloques, presupuesto de trabajo y plazo cooperativo. El proyecto conserva los parámetros, la huella de la entrada y el vínculo al registro de origen.

Las pruebas comparan contra una convolución calculada de forma independiente, verifican identidad, cancelación, reloj, fase, superposición y persistencia. La misma operación se ejecuta desde Python, CLI y escritorio.

## Alcance siguiente

Quedan por implementar Rayleigh, Rician, Doppler, offsets, interferencia, desequilibrio I/Q y las variantes de canal previstas para el enlace integrado. La caracterización de rendimiento por perfil y la matriz del Quality Gate corresponden al candidato de cierre de la fase.
