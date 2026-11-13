# Estimar y evaluar un modelo AR

[← Herramientas](tools.md)

La preliminar **1.8.6** amplía **Modelos de procesos → Estimar AR desde un registro**. Se mantiene Yule–Walker y la generación de realizaciones estacionarias; las nuevas opciones permiten comparar modelos y comprobar cómo predicen. La estable recomendada continúa siendo la 1.8.3.

## Ajustar una recurrencia

La entrada debe ser un registro temporal discreto real. El modelo es:

```text
x[n] = c + φ₁·x[n−1] + … + φp·x[n−p] + e[n]
A(z⁻¹) = 1 − φ₁·z⁻¹ − … − φp·z⁻p
H(z) = 1/A(z⁻¹)
```

El informe sustituye los coeficientes numéricos en la recurrencia. La constante c se conserva por separado: H describe el paso de innovaciones a x y no contiene esa constante.

**Yule–Walker** resta la media de entrenamiento y utiliza autocovarianzas con divisor N. La varianza de innovación resultante puede diferir del promedio cuadrático de los residuos. **Mínimos cuadrados condicionales** ajusta la recurrencia con una constante, usando los antecedentes observados y dejando fuera las primeras p respuestas. Orden cero proporciona una referencia de media y ruido.

La normalización numérica depende sólo del entrenamiento. La reserva no modifica ni los coeficientes ni esa escala. Se rechazan regresiones sin rango suficiente o mal condicionadas, conservando el motivo en las comparaciones.

## Reservar datos y comparar órdenes

**Muestras finales reservadas** excluye ese final antes de ajustar. Con cero no hay validación independiente del entrenamiento. La comparación utiliza mínimos cuadrados con constante y el mismo conjunto de respuestas desde p_máximo para todos los órdenes. Necesita más de 2·p_máximo+1 muestras de entrenamiento.

Para N respuestas comunes y k=p+2 parámetros —p coeficientes, constante y varianza— se utiliza la verosimilitud gaussiana condicional:

```text
D = N·[log(2π) + 1 + log(MSE_entrenamiento)]
AIC = D + 2k
BIC = D + k·log(N)
AICc = AIC + 2k(k+1)/(N−k−1), sólo si N > k+1
```

Los criterios comparan ajuste y complejidad: menor puntuación es preferible dentro del conjunto evaluado. No demuestran el orden verdadero. No se aplican esas puntuaciones de máxima verosimilitud a Yule–Walker. Un ajuste compatible con redondeo no recibe una puntuación infinita ficticia.

También se puede elegir por MSE de la reserva. Si no hay un criterio válido, la herramienta conserva los intentos sin inventar un ganador. Seleccioná una fila válida para inspeccionar su modelo. Una fila fallida deshabilita las acciones del filtro anterior, pero permite volver a otra fila.

## Predicción de un paso y pronóstico

La predicción de un paso usa valores anteriores observados, tanto en entrenamiento como en reserva. Al avanzar dentro de la reserva, los valores ya observados de ese tramo pueden utilizarse como antecedentes. Su MSE no equivale al error de una predicción recursiva de toda la reserva.

El pronóstico comienza después de la última muestra del registro, sin volver a ajustar los parámetros con la reserva. A partir de allí reutiliza sus propias salidas. Cada curva conserva sus índices y el reloj Fs disponible; los intervalos se muestran y exportan como salidas separadas.

La cobertura elegida genera intervalos predictivos condicionales gaussianos. Con respuesta de innovaciones ψ[j], la varianza a h pasos es σe²·Σ(j=0…h−1)ψ[j]². Se incluyen innovaciones futuras, suponiendo independencia y parámetros fijados; se excluye incertidumbre de parámetros, orden y forma del modelo. Por eso el porcentaje nominal no es una garantía sobre un proceso desconocido.

## Residuos y Ljung–Box

El diagnóstico utiliza sólo residuos de entrenamiento, centrados y con divisor N. La tabla muestra su autocorrelación y:

```text
Q(L) = N(N+2)·Σ(k=1…L) r[k]²/(N−k)
grados de libertad = L−p
```

El valor p se obtiene de una aproximación χ² si L>p. Es asintótica y puede ser poco fiable con pocas muestras o un modelo inadecuado. Un valor p pequeño señala incompatibilidad con ausencia de correlación bajo esas hipótesis; uno grande no demuestra blancura ni independencia. No se normaliza un residuo nulo ni se asignan valores p a errores compatibles con redondeo.

## Reutilización y límites

El modelo, las curvas y las tablas quedan en Resultados. Las tablas CSV registran el criterio, el alcance y el origen del registro; CAS conserva los datos numéricos y las referencias al sistema y las curvas. Cambiar el formulario no modifica esos resultados. Elegir otra fila consulta el registro y las opciones del último cálculo aceptado.

Un ajuste no estacionario conserva sus coeficientes y las predicciones representables. No se le asigna una PSD ni una varianza estacionaria. Si una etapa complementaria no se puede calcular, el ajuste sigue disponible con la explicación correspondiente.

Referencias: la documentación de [AutoReg](https://www.statsmodels.org/stable/generated/statsmodels.tsa.ar_model.AutoReg.html) describe el ajuste condicional y el uso de respuestas comunes para comparar órdenes; la de [Ljung–Box](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.acorr_ljungbox.html) explica la corrección de grados de libertad. SignalLab implementa estas operaciones con sus dependencias NumPy y SciPy existentes; no incorpora statsmodels como dependencia.
