# Estudios de estados: coordenadas, equilibrio y memoria

Estas ampliaciones corresponden a la **1.8.11 preliminar**. Se integran en **Analizar modelo de estados** y **Simular estados y salidas**, con las mismas matrices A, B, C, D y el período disponible. Cada estudio conserva el último modelo calculado; editar las entradas principales no lo reemplaza hasta volver a analizarlo.

## Ver las matrices del diagnóstico

**Controlabilidad / observabilidad** muestra Qc=[B, AB, …, A^(n−1)B] y Qo=[C; CA; …; CA^(n−1)]. La tabla permite recorrer todos los elementos y exportarlos junto con el criterio de rango.

La SVD se calcula después de reescalar la matriz para evitar desbordes del espectro singular. El informe muestra la escala, los valores σ/escala y el umbral en esa misma escala. El rango cuenta los valores mayores que el umbral. Es un diagnóstico numérico, dependiente de las coordenadas y del condicionamiento; no se presenta como un rango algebraico exacto.

La estabilidad pertenece a los estados internos del modelo. Una transferencia de un canal puede ocultar modos que no se controlan u observan; por eso no reemplaza este análisis.

## Cambiar coordenadas

**Coordenadas** define x=Pq, con P cuadrada e invertible. Calcula Aq=P⁻¹AP, Bq=P⁻¹B, Cq=CP y Dq=D. Las entradas y salidas conservan sus coordenadas físicas. Cambiar P modifica la descripción del estado, sin agregar una variable independiente ni reducir el orden.

Indicá también el estado original x₀, o dejalo vacío para usar ceros. El informe devuelve q₀=P⁻¹x₀. **Cargar modelo y q₀ en simulación** prepara ambos datos en el destino; copiar x₀ sin transformarlo cambiaría el problema. El modelo transformado también conserva las acciones de análisis, exportación y CAS.

La inversión y los productos se resuelven exactamente sobre los valores binarios guardados. Eso no recupera una constante simbólica original que ya se convirtió a precisión numérica. El modelo reutilizable se redondea a float64; una condición grande de P puede amplificar sus errores de evaluación. Si un componente no puede representarse, se conserva la expresión exacta y no se ofrece como un modelo o estado numérico válido.

## Buscar un equilibrio

**Equilibrio** utiliza una entrada constante uₑ, con un valor por canal. En continuo exige dx/dt=0 y resuelve −Axₑ=Buₑ. En discreto exige x[n+1]=x[n] y resuelve (I−A)xₑ=Buₑ. La salida correspondiente es yₑ=Cxₑ+Duₑ.

La compatibilidad y las variables libres se resuelven algebraicamente para los números almacenados. Se distinguen un equilibrio único, una familia de equilibrios y una ecuación incompatible. Un modo muy pequeño no se declara cero por aplicar un umbral SVD.

En una familia, el informe conserva los parámetros libres y sus efectos sobre estado y salida. **Cargar equilibrio en simulación** utiliza la solución particular con esos parámetros en cero, junto con la entrada constante indicada. No se simula automáticamente. El equilibrio por sí solo no demuestra estabilidad ni que otras condiciones iniciales converjan a él.

## Separar estado cero y entrada cero

En **Simular estados y salidas**, la opción **Separar estado cero y entrada cero** calcula tres trayectorias con la misma realización:

- Total: entrada y estado inicial indicados.
- Estado cero: misma entrada, con estado inicial nulo.
- Entrada cero: entradas anuladas, con la memoria inicial indicada.

El informe compara total con la suma de las dos componentes. Se conservan sus diferencias de redondeo en lugar de modificar la trayectoria total para imponer una igualdad numérica.

La figura permite elegir entradas, estados o salidas y la componente correspondiente. Cada señal queda registrada con su eje y reloj. Las entradas continuas utilizadas se representan como retenciones constantes entre puntos; su definición original permanece vinculada por separado. Reutilización y CAS toman el canal seleccionado, o el primero en la vista conjunta. El CSV exporta todos los canales de esa vista.

## Explicar un paso guardado

**Paso a paso** prepara una vista del último cálculo, sin volver a simular. Su componente se sincroniza con la figura: total, estado cero o entrada cero. El informe identifica cuál utiliza, incluidos sus estados y entradas. La posición k cuenta desde cero dentro del registro; el informe conserva además el índice n o instante t original. Se puede consultar una salida y[k]=Cx[k]+Du[k] o un estado siguiente x[k+1]=Ax[k]+Bu[k].

En continuo, el paso de estado utiliza Ad y Bd de la discretización ZOH aplicada en esa simulación. Es la propagación para la entrada retenida, no una aproximación de Euler. La salida usa C, D y los valores del punto actual. La transición posterior a la última muestra no fue simulada y no se inventa en el inspector.

La tabla desglosa coeficientes, valores guardados y productos. La reconstrucción usa racionales de los valores binarios y se compara con la realización almacenada, sin reemplazarla. Un aporte fuera del rango float64 no se muestra como cero. La tabla elegida se exporta a CSV y los pasos grandes se preparan en segundo plano. Editar los datos conserva esta explicación hasta recalcular.
