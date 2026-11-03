# SignalLab PC 0.90 — transformadas hacia análisis y borradores por vista

28/10/2026. Corrección del recorrido afectado y consolidación de la navegación. Se mantienen las 31 familias y 72 rutas públicas.

## Copiar resultado a la inversa

Se reprodujo el fallo en Z y Laplace: el aviso era una fila oculta de QFormLayout, pero el botón mostraba directamente su QLabel. Como el formulario seguía considerando la fila oculta, el aviso conservaba una geometría inicial de 640×480 y tapaba los controles. Ahora se muestra u oculta la fila mediante el formulario. Editar la expresión también retira su aviso correctamente.

Copiar conserva la entrada directa y sus resultados, prepara la expresión inversa y mantiene las condiciones originales visibles. No calcula automáticamente ni inventa una ROC. El recorrido puede repetirse aunque ya exista un resultado inverso anterior.

## Enviar al análisis de sistemas

Laplace y Z disponen de una acción directa para interpretar la expresión como H(s) o H(z):

- En Directa y Muestras finitas usa X del último resultado calculado, aunque después se haya editado el borrador.
- En Inversa usa la X ingresada en ese momento, sin exigir calcular la inversa.

La acción obtiene la transferencia numérica y abre la herramienta pública Analizar un sistema, que permite frecuencia, retardo, polos/ceros y realización. Se calcula allí con sus propios datos. Las potencias positivas y negativas de z se conservan, y el origen de la expresión queda vinculado al resultado cuando corresponde. Las transformadas y sus resultados no se reemplazan.

Se aceptan expresiones racionales con coeficientes numéricos. Los parámetros libres requieren valores; una expresión no racional no se convierte en una transferencia polinómica ficticia. Las condiciones de una señal no se reinterpretan como una ROC seleccionada automáticamente para H. La biblioteca explica qué entrada usa la acción en cada modo.

## Borradores al cambiar de variante

Antes, cada cambio entre variantes volvía a copiar la entrada anterior sobre el destino, incluso si ya existía un borrador propio en esa vista. Ahora sólo se prepara una copia compatible al abrir una variante por primera vez. Al regresar se conservan sus datos; un enlace breve permite copiar expresamente la entrada de la vista anterior. Las salidas ya calculadas permanecen inmutables y se indica que requieren recalcular si sus datos cambian.

La copia mantiene dominio, fórmula, secciones SOS y procedencia. Se retira una definición importada antigua cuando se sustituye por otros coeficientes, evitando reutilizar por accidente sus secciones ocultas. Los dominios diferentes y los avances que no admite una realización causal no se convierten automáticamente. Tampoco se confunden una reconstrucción de módulo/fase, coeficientes de serie y muestras temporales.

## Evidencia dirigida y pendientes

- Fallo reproducido y corrección verificada en la geometría real del formulario de Z y Laplace.
- Recorrido con los botones reales: directa → análisis, directa → inversa → cálculo, inversa ingresada → análisis, H(z) con avance, retorno a resultados anteriores, copias repetidas y tamaños 1366/800/640.
- Recorrido de variantes: frecuencia/temporal con SOS, borradores diferentes, copia explícita, resultado calculado conservado, procedencia y caché correctas; DTFT/DFT con registro importado de origen negativo y posterior fórmula propia.
- Inspección visual de las pantallas corregidas. Se actualizan las ayudas y se genera el portable sin repetir campañas generales de instalación o pruebas.

Esta entrega atiende la corrección de transformadas antes de continuar otras mejoras. Se detectó que discretizar estados y convertirlos a transferencia aún requieren pasar por Resultados anteriores para reutilizar la salida; faltan acciones directas junto al cálculo. También queda por revisar la convención de índices en entradas de simulación discreta de estados. Estas tareas permanecen abiertas y no se declara finalizada la 1.0.
