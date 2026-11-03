# SignalLab PC 0.84 · Formatos numéricos y precisión de coeficientes

27/10/2026. Compilación de desarrollo hacia 1.0. Se conservan las versiones anteriores.

## Organización

Cuantización y representación → Formatos y coeficientes reemplaza la presentación aislada de Punto fijo en su misma ruta. Conserva el estudio de un número y añade coeficientes de un filtro como segunda modalidad, sin nuevas familias ni rutas: siguen siendo 31 y 72.

La entrada de H(z) es independiente y acepta fórmula o coeficientes. Copiar un filtro anterior y enviar uno desde otros menús son opciones adicionales. La representación SOS/polinómica sólo se elige cuando existen secciones conservadas; no se ofrece un control sin efecto sobre una entrada directa.

## Representación de números

- Punto fijo Q con signo, bits enteros incluyendo signo, bits fraccionarios, saturación y redondeo con empates alejándose de cero o truncamiento hacia cero.
- IEEE 754 binary16, binary32 y binary64, con signo/exponente/fracción, normales, subnormales, cero con signo y desborde a infinito.
- Conversión de racionales directamente al formato elegido con enteros y fracciones exactas; se evita convertir primero a float64 y causar doble redondeo al pasar a binary16/32. En IEEE se utiliza el más cercano con empates al par.
- Constantes racionales y notación científica se leen exactamente. Constantes irracionales, como pi, se aproximan con 100 cifras antes de codificar y el informe lo aclara.
- JSON conserva palabra completa y valores; la vista abrevia palabras o fracciones extensas, mostrando una aproximación indicada y manteniendo los datos exactos de esa referencia en la exportación.

## Coeficientes de filtros

Se cuantizan componentes reales e imaginarias de los coeficientes almacenados. a[0]=1 queda como constante implícita de la recurrencia: no se cuantiza ni se renormaliza luego. En Q se indican las saturaciones. Un coeficiente que pasa a infinito en un formato flotante se rechaza, en lugar de crear una transferencia inválida.

Se conservan SOS cuando la entrada las trae y se elige esa opción. El resultado puede compararse también desde los polinomios directos. La tabla/CSV muestra original, representado, error salida−entrada, clase y palabra binaria. Las acciones existentes analizan, exportan y envían Hq a otros menús.

La comparación de respuesta usa módulo, fase principal y retardo sobre un eje común de 0…π rad/muestra. El informe muestra radios de polos, estados de estabilidad de los denominadores y puntos de frecuencia no definidos. Para medir error sin desbordes se utiliza S, máximo valor absoluto de las componentes finitas de ambas respuestas con mínimo uno, e informa el máximo muestreado de |Hq−H|/S. No es un error relativo punto a punto ni una cota entre todas las frecuencias.

Sólo se calculan raíces de denominadores para esos radios, evitando resolver ceros de FIR largos que no intervienen en el informe. Los coeficientes originales no se modifican y editar entradas conserva el resultado anterior marcado hasta recalcular.

## Alcance explícito

Después de cuantizar el almacenamiento, las respuestas se evalúan en doble precisión. No se redondea cada multiplicación, suma, acumulador o estado. No se declara un simulador completo de ruido aritmético, ciclos límite ni todos los modos de hardware IEEE. Los coeficientes de entrada son los valores binarios del Transfer, no una constante simbólica anterior desconocida.

La biblioteca incluye la explicación conectada de ambos estudios, referencia de campos e imagen de signo/exponente/fracción. Se agregan términos de glosario para IEEE 754, mantisa y subnormal.

## Comprobaciones dirigidas

tests/test_precision.py: cuatro casos con palabras conocidas y contraste con numpy en binary16; empates al par y un caso que falla si se redondea primero a float64; subnormales, cero negativo, infinito por desborde; Q exacto y saturación; polo 0.99 que pasa a 1 con Q(1,3); a[0] implícito; SOS preservadas, binary64 sin cambios y componentes complejas. Pasaron.

check_precision_ui86.log: familia existente, número/constante irracional, JSON, envío de filtro a representación, polos y respuesta con ejes comunes, estado de borrador, CSV y reutilización temporal. Lectura y formulario a 800×600 y 640×480. Pasó. Revisión visual del informe.

No se ejecutó una campaña general de instalación ni pruebas ajenas al cambio. Permanecen pendientes los aspectos de aritmética de ejecución y reconstrucción módulo–fase del cierre de 1.0.
