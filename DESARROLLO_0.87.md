# SignalLab PC 0.87 — frecuencia en diseño y análisis no causal

27/10/2026. Corrección de organización y del bloqueo general informado por el usuario. Misma familia de diseño y mismas rutas públicas.

## Diseño por polos y ceros

La pestaña Respuesta en frecuencia calcula módulo lineal/dB, fase desenrollada y retardo de grupo junto al plano de diseño. Tiene intervalo y cantidad de puntos propios, exportación CSV/JSON y figura externa con ejes compartidos. El plano conserva su lienzo independiente: mover un punto actualiza la respuesta sin convertir el gráfico de edición en otro gráfico.

El cálculo del diseño actualiza su respuesta por defecto. Si el intervalo de frecuencia es inválido, se conserva el diseño válido y se explica qué corregir en esa pestaña. Un cambio de intervalo puede recalcular sólo la respuesta. Se distinguen fase/retardo no definidos y el módulo nulo en dB.

Usar filtro en vuelve a incluir Análisis de sistemas; Analizar conserva sus accesos rápidos. Se retiran del formulario de raíces los botones heredados de plano y exportación que duplicaban las pestañas o apuntaban a una respuesta antigua. Se conserva el texto escrito en las raíces al calcular y sólo se supervisan los cuatro campos relevantes para ese diseño: dominio, ceros, polos y ganancia. Así no se muestra Datos modificados por cambios internos de campos ocultos.

## Sistemas con avance temporal

Se elimina la prohibición de más ceros que polos en un diseño digital. La definición positiva k·producto(z−c)/producto(z−p) se representa como z^m·B(z^−1)/A(z^−1), con avance explícito cuando corresponde. Los diseños causales anteriores mantienen su convención y los retardos se conservan como ceros iniciales de b. Un avance y un retardo inicial exactamente redundantes se reducen sin modificar H.

El factor se conserva en frecuencia, fase, retardo, polos/ceros en el origen, fórmula, registros del proyecto y transferencia exportada. No aparecen polos ficticios en cero por analizar sólo el núcleo en z^−1. Análisis de sistemas ya no deshabilita la reutilización/exportación de una fórmula numérica con avance.

También se corrige el envío a la Transformada Z unificada: recibe la fórmula completa y su inversa puede entregar muestras en índices negativos, según la ROC elegida. La normalización de ganancia mantiene el factor. Los destinos ofrecidos para sistemas con avance corresponden a capacidades que lo conservan: análisis, diseño, ganancia y Z inversa.

## Alcance y compatibilidad

La frecuencia evalúa la expresión racional sobre el círculo unidad o el eje imaginario. Su interpretación como transformada de Fourier exige que ese círculo/eje pertenezca a la ROC. La fórmula sola no selecciona causalidad, estabilidad bilateral ni una ROC.

La respuesta temporal mediante una recurrencia causal, la aritmética de ejecución causal y la realización por una cadena ordinaria de retardos siguen requiriendo una definición sin avance. Esas operaciones no descartan ni cambian el avance; se indica usar análisis o Z inversa con ROC. El análisis de frecuencia/raíces no queda bloqueado por esa restricción de implementación.

El JSON de transferencia con avance usa versión 2 y un campo advance obligatorio en la definición generada; las versiones anteriores rechazan el número de formato en lugar de ignorar un factor que cambia el sistema. Los sistemas sin avance siguen exportándose como versión 1. La versión actual lee ambos formatos. Los registros del proyecto conservan el avance explícito.

## Evidencia dirigida

Cuatro casos nuevos pasaron: comparación de diseños no causales con su expresión positiva en z y raíces en el origen; fórmulas/exportación/proyecto con avance aplicado una sola vez; inversa por contorno con muestras negativas y límites de operaciones causales; convenciones causales y analógicas anteriores. Se ejecutaron además los ocho casos existentes de frecuencia compartida: rejillas, márgenes, ceros, fase, retardo y exportación. Total: doce casos, 0.66 s localmente.

Recorrido Qt: diseño automático de H(z)=z², retardo −2, actualización por la ruta del editor con mouse, menú de reutilización a análisis, plano sin polos artificiales, fórmula z²+1, JSON con avance, envío a Z inversa y muestras δ[n+2]+δ[n]. Se comprobó también que un intervalo de frecuencia inválido no anule el diseño. Recorrido a 640/800 px y revisión visual del panel/figura. Una comprobación de presentación confirmó estado actualizado y ausencia de botones duplicados heredados.

La generación del portable no se considera cierre de 1.0. Siguen pendientes los alcances registrados en CIERRE_1.0.md.
