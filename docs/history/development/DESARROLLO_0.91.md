# SignalLab PC 0.91 — fórmulas nítidas

28/10/2026. Cambio de presentación; no se modifica el cálculo matemático ni la organización del catálogo.

Las fórmulas se mostraban como PNG a 140 dpi reducidos a su tamaño lógico y luego reescalados por Windows. Ese recorrido podía difuminar trazos y potencias, especialmente con escalas de pantalla superiores al 100 %.

Ahora los informes, vistas previas, ecuaciones de transferencia y la hoja CAS dibujan trazados SVG directamente mediante Qt. Los caracteres están incluidos como contornos, sin depender de una sustitución de fuentes para la fórmula. La resolución final depende de la pantalla; se conserva el tamaño lógico y el control de tamaño del CAS.

Los informes HTML exportados incrustan las fórmulas como SVG y mantienen las imágenes ordinarias de ayuda como imágenes. El texto copiado y los resultados conservan su contenido y precisión. El soporte de imágenes comunes y corchetes de matrices se mantiene en el mismo documento; los recursos de fórmulas anteriores se retiran al reemplazar el informe.

Se adapta también el informe especial de transferencias a los argumentos de formato del informe común, evitando incompatibilidad con la presentación numérica introducida anteriormente.


Se mantiene el alcance abierto hacia 1.0 y los pendientes documentados en CIERRE_1.0.md.
