# SignalLab PC 0.79 · CAS legible y sistemas reutilizables

27/10/2026. Compilación de desarrollo hacia 1.0; se conservan los portables anteriores.

## CAS

- Las imágenes matemáticas dejan de reducirse para encajar en el ancho de cada celda. Las potencias conservan el tamaño nativo de lectura, también en ventanas angostas y dentro de matrices.
- Fórmulas anchas: desplazamiento horizontal explícito y enlace Ampliar resultado, con ventana aparte. Hoja permite aumentar/reducir el tamaño. Copia y exportación mantienen la expresión completa; las vistas parciales de matrices/listas siguen señaladas.
- assume(x>0), assume(x,real), assume(n,integer) y propiedades complex, positive, negative, nonnegative, nonpositive, nonzero (real no nulo) y zero. Se acumulan supuestos por símbolo, limitados a la hoja actual; Hoja → Variables y supuestos los muestra y purge(x) los elimina junto con la definición.
- Comparaciones simples de un símbolo con constantes reales finitas: assume(x>2,x<4). Se derivan las hipótesis de signo y se restringen soluciones a su dominio. x!=0 no presupone que x sea real. Una contradicción, una asignación incompatible o una raíz numérica que no cumpla los supuestos no cambia el estado.
- Los supuestos no son un demostrador general: no se aceptan relaciones como x>y, supuestos sobre funciones ni condiciones paramétricas como verificadas sin evidencia. Las soluciones de sistemas con condiciones que no puedan verificarse se informan sin presentarlas como incondicionales.
- exp2trig(expr) aplica Euler a las exponenciales. trig2exp(expr) expresa trigonometría/hiperbólicas mediante exponenciales. Disponibles desde Álgebra y explicadas en la biblioteca; unidades en radianes.

## Análisis de sistemas

- Una fórmula racional numérica H(s)/H(z) usa las acciones comunes de los demás resultados: exportar y enviar a respuesta temporal, conexiones, diseño por raíces, ajustes, conversión y, si corresponde, Z inversa.
- Ajustar ganancia y fase permite seleccionar Ganancia o Fase mínima / paso todo desde el destino agrupado, sin crear herramientas nuevas ni perder la selección entre variantes.
- Editar fórmula, coeficientes o dominio ya no elimina el último sistema analizado ni desactiva sus acciones. Datos modificados avisa que hay un borrador pendiente; exportar/enviar sigue usando el Transfer y registro del último cálculo.
- La comprobación inicial reprodujo el envío correcto de fórmulas comunes a respuesta temporal; no se atribuye todo fallo posible a una única causa no demostrada. Se corrigieron las inconsistencias comprobadas de disponibilidad y destinos.
- Parámetros libres: explicación de la necesidad de valores numéricos. Avances de H(z): se conserva el análisis de la fórmula completa y la exportación de respuesta; no se transforma un avance en retardo ni se envía silenciosamente como filtro causal.

## Comprobación dirigida

- Ocho casos CAS existentes pasaron tras incorporar el estado de supuestos.
- Cuatro casos persistentes nuevos en tests/test_cas_assumptions.py: Euler, dominios/historial, contradicciones/asignaciones/raíces numéricas y soluciones complejas/de sistemas.
- Recorrido específico del motor con procesos reales: supuestos conservados entre solicitudes, nombres libres anteriores reinterpretados al reutilizarlos, real/entero/signo/límites/no cero, purge y atomicidad de fallos. Registro: check_cas81.log.
- Interfaz real a 1200×760 y 640×480: imágenes de ancho nativo constante, barra horizontal, ampliación, ajuste de tamaño y entrada accesible. Envíos mediante acciones reales a respuesta temporal, ganancia, fase y conversión, con conservación del resultado tras editar la fórmula; JSON coincide con los coeficientes calculados. Casos con parámetros y avances explicados. Registro: check_cas_ui81.log.
- Revisión visual de CAS y de su ventana ampliada. No se realizó una campaña general de regresión ni de instalación; el usuario realiza la revisión general del portable.

## Pendientes de 1.0

Se mantienen los pendientes declarados en CIERRE_1.0.md y COBERTURA_SYS_I_II_ACTUAL.md: diagramas de realización, relaciones módulo–fase/compensación y aritmética de implementación. Esta entrega no declara cobertura universal ni la versión estable terminada.
