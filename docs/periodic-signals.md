# Señales periódicas y trenes

[Volver a la documentación](README.md)

## Escribir un período y repetirlo

En **Señales → Crear una señal**, elegí el dominio y activá **Repetir un período en todo el eje**. En **Fórmula**, escribí el tramo base y completá **Inicio del período** y **Período**. En **Muestras**, cargá un ciclo en orden. En continuo, el paso separa dos puntos consecutivos y la interpolación lineal también une el último con el primero del siguiente ciclo.

La ventana del gráfico indica qué índices o instantes se muestran. Por ejemplo, una secuencia de período 4 se puede dibujar desde n = −8 con 17 muestras. En **Resultados** guardás la fórmula completa y el registro visible. Esto también funciona cuando escribís un tren directamente en Fórmula, lo activás con un escalón o sumás trenes con períodos que no coinciden. Desde **Usar señal en…**, elegí la definición para calcular Fourier, DTFT o la potencia de todo el eje.

## Referencia de fórmulas

Podés escribir estas expresiones en los campos de fórmulas y en el CAS. Desactivá la casilla de repetir si usás una función que ya incluye su propio período.

| Función | Ejemplo | Resultado |
| --- | --- | --- |
| `Repeat(f,n,N,inicio)` o `Repeat(f,t,T,inicio)` | `Repeat(n,n,4)` | Repite 0, 1, 2 y 3 desde n = 0. Si omitís el inicio, vale cero. |
| `RepeatSamples(n,inicio,(valores,))` | `RepeatSamples(n,-1,(2,0,3))` | Coloca 2, 0 y 3 en n = −1, 0 y 1 y los repite cada tres índices. |
| `RepeatSamples(t,inicio,(valores,),paso)` | `RepeatSamples(t,0,(0,1),1)` | Señal triangular de período 2 s que sube durante el primer segundo y baja durante el segundo. |
| `PulseTrain(v,P,D)` | `PulseTrain(n-1,5,2)` | Pulso de altura 1 en n = 1 y 2, repetido cada 5 muestras. D indica la duración dentro de cada período P. |
| `ImpulseTrain(v,P)` | `ImpulseTrain(t-1,4)` | Impulsos Dirac de área 1 en …, −3, 1, 5, … segundos. Con n, son muestras unitarias. |

Para cambiar la amplitud, multiplicá la fórmula por un número. En `PulseTrain(t-1,4,2)`, el pulso está alto desde t = 1 s hasta antes de t = 3 s y se repite cada 4 s. En discreto, período y duración son enteros. En continuo se expresan en segundos.

## Ajustar amplitud y medir

En **Ajustar amplitud**, la salida es `A*x+B`. Para bajar dos unidades, cargá A = 1 y B = −2. Si hay Dirac, A multiplica sus áreas y B desplaza la parte ordinaria.

En **Partes par e impar**, al reutilizar una fórmula completa se evalúa la señal original y su reflejo en una ventana simétrica. Podés guardar y reutilizar cada fórmula por separado. Cuando la entrada es una lista de muestras, cada valor fuera del registro se toma como cero.

En **Energía y potencia → Medir en todo el eje**, un tren de pulsos unitarios de ancho D y período P da potencia D/P. Un tren discreto de un impulso unitario por período da 1/P. Las Dirac continuas se estudian como distribuciones en Fourier o Laplace. Su cuadrado no está definido para el cálculo de energía ordinaria.

Probá `cos(n)` y `cos(pi*n)` en discreto. La primera tiene potencia 1/2. En la segunda, cada muestra vale 1 o −1, así que la potencia es 1. Para `cos(pi*t)` en continuo, la potencia es 1/2. Una señal que decae también puede tener energía finita, como `cos(n)/sqrt(1+n^2)`, o infinita, como `cos(n)/sqrt(1+abs(n))`. Ambas tienen potencia cero.

La fase inicial también importa cuando los tonos de frecuencia positiva y negativa coinciden en discreto. Por ejemplo, `cos(pi*n+pi/3)` alterna entre 1/2 y −1/2, de modo que su potencia es 1/4. Para `cos(pi*n+pi/2)` todas las muestras valen cero.

Para sumar varios trenes continuos que no comparten un ciclo, elegí **Medir en todo el eje**. Por ejemplo, `PulseTrain(t,1,1/4)+PulseTrain(t,sqrt(2),1/2)` da potencia `1/4 + 3*sqrt(2)/8`. El promedio conserva el producto de los niveles medios de los trenes. Si al tren de período 1 le sumás `cos(2*pi*t)`, ambas componentes comparten frecuencias y se promedian juntas. Una componente transitoria que decae, como `exp(-abs(t))`, puede modificar la energía de una ventana y su potencia media tiende a cero.

Si multiplicás esos dos trenes, la potencia es `sqrt(2)/16`. El cálculo promedia por separado los dos ciclos cuyo cociente es irracional. Cuando los períodos tienen un múltiplo común, calcula el solapamiento en ese ciclo.

En discreto, `ImpulseTrain(n,4)+cos(n)` da potencia 3/4. Con `cos(pi*n/2)`, el coseno sí coincide con un armónico del tren y la potencia vale 5/4. Las frecuencias separadas por un múltiplo de 2π representan el mismo tono discreto.

Si el tren está multiplicado por un decaimiento exponencial, el cálculo acumula las repeticiones de cada semieje con su peso. Por ejemplo, `(1/2)^abs(n)*ImpulseTrain(n,4)` tiene energía `257/255` y potencia cero.

Para conservar sólo la mitad derecha de un tren, multiplicá su fórmula por `Step(t)` o `Step(n)`. Por ejemplo, `Step(t)*PulseTrain(t,1,1/4)` tiene energía infinita y potencia media global 1/8. El tren completo tiene potencia 1/4. Si además lo cortás en t = 2 con `(Step(t)-Step(t-2))`, la energía queda en 1/2 y la potencia global en cero.

## Graficar y reutilizar transformadas

En **DTFT algebraica**, usá `ImpulseTrain(n-1,4)` con límites `-oo` y `oo` para obtener todo el espectro. Abrí **Graficar resultado** para ver las líneas por frecuencia y peso. Para recuperar la secuencia elegí **DTFT inversa algebraica** en **Usar espectro en…**.

En **Fourier continua**, `PulseTrain(t-1,4,2)` da líneas separadas por 2π/4 rad/s. Reutilizá el espectro guardado en **Fourier continua inversa** para reconstruir el período. También podés pegar la fórmula del espectro de un tren rectangular u otro período formado por tramos polinómicos. En un salto, el resultado toma el promedio de los límites laterales.

Si eliminás un período con `(1-(Step(t)-Step(t-4)))*PulseTrain(t,4,2)`, el gráfico conserva las líneas del tren y la corrección continua del recorte. Si el tren se repite hacia un solo lado, Fourier algebraica puede calcular el espectro generalizado. Probá `Step(t-1)*PulseTrain(t-1,4,2)` en continuo o `PulseTrain(n-1,4,2)` con límites `2` y `oo` en DTFT. El término `PVCot(w,P)` representa el valor principal de `cot(P*w/2)`. La gráfica separa las áreas de las líneas de la curva, que se interrumpe en los polos.

En **Laplace → Directa → Unilateral**, el cálculo integra un período desde t = 0 y suma las repeticiones hacia la derecha. En **Bilateral**, un tren periódico no nulo tiene región de convergencia vacía y su espectro de Fourier se puede reutilizar. En Z ocurre algo equivalente al elegir `-oo` y `oo` para un tren discreto. El informe conserva su DTFT.

Cuando sumás trenes continuos con períodos distintos, **Fourier continua** reúne sus familias de líneas y suma las áreas que coinciden. Si la suma se extiende sobre todo el eje, **Laplace bilateral** informa que la región de convergencia queda vacía y conserva el espectro. Si la activás en t = 0 con un escalón, la misma herramienta devuelve la fórmula en s con ROC `Re(s) > 0`.
