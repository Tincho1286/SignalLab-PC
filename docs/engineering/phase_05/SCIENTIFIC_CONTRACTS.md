# Contratos científicos de Fase 05

## Distribución y observación

La familia y los parámetros tienen una versión. Los parámetros de forma, ubicación, escala, soporte y unidades se normalizan antes de ejecutar. Densidad y masa son magnitudes distintas. La supervivencia se evalúa directamente, y los valores de cola tienen evaluación logarítmica. Un momento divergente o indefinido se registra como estado y los datos persistidos conservan JSON finito. Una realización usa `Signal` por componente o por réplica. Cada registro conserva reloj si se suministró. El índice de una muestra de distribución por sí solo no fija una frecuencia física.

Para un vector complejo centrado $Z$, se usa $C=E[ZZ^H]$ y $P=E[ZZ^T]$. La matriz aumentada debe ser semidefinida positiva. El caso propio satisface $P=0$. Los informes distinguen medias vectoriales, proyecciones y varianza compleja $E|Z-EZ|^2$. Representar las observaciones con partes real e imaginaria o magnitud y fase incluye declarar explícitamente la proyección.

## Modelos y estimadores

Una teoría usa parámetros poblacionales o del modelo. Los estadísticos y ajustes describen observaciones e indican método, hipótesis, denominador, condiciones numéricas e incertidumbre. La correlación discreta conserva el sentido histórico $R_{xy}[k]=E(x[n+k]\overline{y[n]})$. Cada estimador registra la intersección de soportes y el número de pares. Las PSD declaran ancho de banda, ventana y escala bilateral/unilateral, reloj y convención de densidad.

Los procesos declaran estado inicial, paso temporal, parámetros, método de transición o regularización y dominio. Una realización finita produce evidencia experimental dentro del tamaño y diseño de la observación. Los intervalos para muestras IID, series correlacionadas y réplicas independientes tienen requisitos distintos.

## Ejecución y persistencia

Los servicios científicos se llaman sin Qt. Se usa `ExecutionContext` para admisión por estimación, cancelación cooperativa y publicación atómica. Se conservan semilla maestra, versión de NumPy, algoritmo RNG y subflujo. Una réplica se reproduce por su identidad aunque cambie el orden de un barrido. Un resultado persistido conserva parámetros normalizados, condiciones de validez, procedencia y referencias a entradas. Los formatos compatibles se reabren con sus lectores actuales.
