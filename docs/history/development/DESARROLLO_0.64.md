# SignalLab PC 0.64 — figuras independientes y conversión ideal

## Interfaz
Los gráficos de herramientas se abren en ventanas independientes, no modales, conservando zoom, exportación y lectura de muestras. Cerrar oculta la figura; Abrir gráfico la recupera. Cada herramienta conserva su figura, que se actualiza con sus resultados. Los datos, informes y controles permanecen en el documento principal. Las figuras conservan el resultado de su herramienta durante la sesión. Cerrar la ventana del gráfico no borra sus datos.

Los paneles de columnas y divisores se apilan cuando falta ancho. Se reduce el mínimo de la ventana principal y se adapta su tamaño inicial al área disponible; los formularios conservan desplazamiento. La vista previa del selector de resultados sigue siendo una vista de selección.

## Filtros analógicos ideales
En Convertir sistema analógico / digital, elegir Respuesta analógica ideal / por tramos. El editor admite tramos y fórmulas Ha(jΩ), con w en rad/s.
- Bilineal: Hd(exp(jω)) = Ha(j (2/T)tan(ω/2)). No impone soporte finito; deforma el eje de frecuencia. No certifica causalidad ni realización racional.
- Invarianza: h[n]=T ha(nT), por lo que Hd=Σk Ha(j(ω+2πk)/T). Se exige declarar soporte finito |Ω|≤Ωmáx y se define cero fuera. Todas sus réplicas se incluyen. Puede haber aliasing. Truncar un soporte infinito cambia el filtro y se declara como tal.

El resultado es H digital muestreada, exportable y reutilizable en Filtros ideales y por tramos para invertir o aplicar a señales. No se fabrican coeficientes finitos para un filtro ideal. La rejilla usa centros de celda y evita la singularidad bilineal en ±π; la inversión admite esta rejilla con cuadratura de punto medio. Refinar puntos permite estudiar la aproximación cerca de discontinuidades.

## Comprobaciones dirigidas
Corte ideal bilineal; comparación con conversión racional de primer orden; suma de réplicas con aliasing; inversión de ganancia compleja constante; cálculo desde el panel, publicación, envío y cálculo en Filtros ideales; apertura no modal, cierre y reapertura de figuras; ventana de 800×600 y ajuste de columnas. No se realizó una campaña exhaustiva de resoluciones.
