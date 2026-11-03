# SignalLab PC 0.14 — herramientas autónomas y resultados explícitos

## Referencia consultada
Se comparó la fuente HP canónica con la referencia del proyecto; ambas tienen SHA256 9EC7E69183AC50303A4EF0FDFAFD4B585F33D75D2164AE725E95574A75033DCB. El visor de resultados HP ofrece tabla, gráfico, fórmula, datos/eje y exportación como acciones del resultado (SSShow, alrededor de la línea 1719). Sus ayudas distinguen magnitud, fase y fase no definida en módulo cero.

## Cambios verificados
- Respuesta temporal es un panel autónomo. Parte de una definición local, no requiere un sistema generado en otro menú y usa un solo conjunto de coeficientes para el dominio elegido.
- Escalón e impulso para sistemas continuos y discretos. En discreto se muestra la cantidad de muestras; la duración continua no aparece. La edición de coeficientes se despliega desde la transferencia visible.
- Importar un resultado anterior o un archivo de transferencia JSON es opcional y copia los coeficientes al panel local. Cambiar de dominio ya no intenta ejecutar exclusivamente la rutina continua.
- Resultados de señales: vista inicial de módulo y fase principal, con alternativa real/imaginaria. La fase no se dibuja en muestras de módulo cero. Se conservan los tallos discretos y los datos originales.
- Ejemplo seleccionable de impulso discreto δ[n], además de escalón y seno. Una Dirac continua presente en una respuesta se anota con su peso, sin simular una altura infinita ni una muestra finita equivalente.
- Exportación directa JSON o CSV desde el resultado. El CSV conserva real e imaginaria y añade los metadatos a su cabecera, incluidos los pesos de Dirac cuando existen.
- Resultados anteriores: exportar una selección es independiente de guardar una sesión completa. Se ocultan identificadores internos del resumen y se eliminan acciones duplicadas para agregar sistemas al proyecto.
- Iconos de navegación, identificador visual de SignalLab y esquemas entrada–sistema–salida en respuesta temporal y herramientas de estados. Estas últimas explican qué matrices necesitan y qué responde cada análisis.

## Evidencia
129 pruebas existentes: OK. Comprobaciones específicas: respuesta continua sin objetos previos; respuesta discreta al impulso; copia de un sistema sin cálculo automático; invariancia de datos e historial al alternar vistas; impulso discreto con una única muestra unitaria; fase ausente en ceros; CSV con todas las muestras; anotación del peso de la Dirac continua; importación de un sistema desde JSON. Ver verificacion-flujo-0.14.json e interfaz-0.14-respuesta.png.

## Auditoría del objetivo nuevo: trabajo pendiente
La claridad de todos los menús aún no está acreditada. Esta entrega corrige el recorrido señalado de respuesta temporal y componentes compartidos, pero quedan por revisar:
- consistencia de entradas locales/importadas y restricciones de dominio en el resto de paneles heredados;
- orientación visual y nombres de acciones en todos los menús;
- uso de módulo/fase en las vistas particulares de estados y en las previsualizaciones del selector, que aún pueden usar real/imaginaria;
- simplificación adicional del listado de resultados y de las fórmulas numéricas importadas;
- validación visual y de interacción de todos esos recorridos.

No se declara completa la migración, la equivalencia con MATLAB/Octave ni este objetivo de interfaz.
