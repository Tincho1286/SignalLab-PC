# Señales periódicas y trenes

[Volver a la documentación](README.md)

## Escribir un período y repetirlo

En **Señales → Crear una señal**, elegí el dominio y activá **Repetir un período en todo el eje**. En **Fórmula**, escribí el tramo base y completá **Inicio del período** y **Período**. En **Muestras**, cargá un ciclo en orden. En continuo, el paso separa dos puntos consecutivos y la interpolación lineal también une el último con el primero del siguiente ciclo.

La ventana del gráfico indica qué índices o instantes se muestran. Por ejemplo, una secuencia de período 4 se puede dibujar desde n = −8 con 17 muestras. En **Resultados** guardás la definición periódica y el registro visible. Usá la definición para calcular la transformada o la potencia de todo el eje.

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

En **Energía y potencia → Medir en todo el eje**, un tren de pulsos unitarios de ancho D y período P da potencia D/P. Un tren discreto de un impulso unitario por período da 1/P. Las Dirac continuas se estudian como distribuciones en Fourier o Laplace. Su cuadrado no está definido para el cálculo de energía ordinaria.

Probá `cos(n)` y `cos(pi*n)` en discreto. La primera tiene potencia 1/2. En la segunda, cada muestra vale 1 o −1, así que la potencia es 1. Para `cos(pi*t)` en continuo, la potencia es 1/2. Una señal que decae también puede tener energía finita, como `cos(n)/sqrt(1+n^2)`, o infinita, como `cos(n)/sqrt(1+abs(n))`. Ambas tienen potencia cero.

Para conservar sólo la mitad derecha de un tren, multiplicá su fórmula por `Step(t)` o `Step(n)`. Por ejemplo, `Step(t)*PulseTrain(t,1,1/4)` tiene energía infinita y potencia media global 1/8. El tren completo tiene potencia 1/4. Si además lo cortás en t = 2 con `(Step(t)-Step(t-2))`, la energía queda en 1/2 y la potencia global en cero.

## Graficar y reutilizar transformadas

En **DTFT algebraica**, usá `ImpulseTrain(n-1,4)` con límites `-oo` y `oo` para obtener todo el espectro. Abrí **Graficar resultado** para ver las líneas por frecuencia y peso. Para recuperar la secuencia elegí **DTFT inversa algebraica** en **Usar espectro en…**.

En **Fourier continua**, `PulseTrain(t-1,4,2)` da líneas separadas por 2π/4 rad/s. Reutilizá el espectro guardado en **Fourier continua inversa** para reconstruir el período. También podés pegar la fórmula del espectro de un tren rectangular u otro período formado por tramos polinómicos. En un salto, el resultado toma el promedio de los límites laterales.

En **Laplace → Directa → Unilateral**, el cálculo integra un período desde t = 0 y suma las repeticiones hacia la derecha. En **Bilateral**, un tren periódico no nulo tiene región de convergencia vacía y su espectro de Fourier se puede reutilizar. En Z ocurre algo equivalente al elegir `-oo` y `oo` para un tren discreto. El informe conserva su DTFT.
