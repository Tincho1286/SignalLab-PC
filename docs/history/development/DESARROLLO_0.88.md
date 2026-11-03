# SignalLab PC 0.88 — reconstrucción de módulo y fase

28/10/2026. Tercer estudio dentro de Ajustar ganancia y fase → Fase y compensación. Se mantienen las 31 familias y 72 rutas públicas.

## Problema y solución

Antes se podían separar factores o diseñar un compensador partiendo de H(z), pero no reconstruir una respuesta a partir de módulo o fase independientes. Ahora se puede ingresar módulo lineal, módulo en dB o fase desenrollada, como fórmula/tramos, lista, archivo o resultado compatible.

El estudio emplea un modelo cepstral causal del logaritmo de la respuesta. La relación entre fase mínima y cepstrum causal está desarrollada en [Minimum-Phase Filter Design, Julius O. Smith](https://www.dsprelated.com/freebooks/sasp/Minimum_Phase_Filter_Design.html). El módulo no fija factores paso todo, fase constante o desplazamiento; la fase sola tampoco fija la escala de ganancia. La herramienta requiere convenciones o datos para esa información, en lugar de presentarla como recuperada.

## Datos y modelo

- Módulo lineal/dB → modelo base de fase mínima. Se puede agregar una fase constante y un desplazamiento entero d: positivo retrasa y negativo adelanta.
- Fase desenrollada → módulo, imponiendo un valor positivo conocido en ω=0. Se quita el desplazamiento conocido antes de reconstruir y después se aplica de nuevo. Una fase que no cierre el período o tenga saltos no resueltos se rechaza con explicación.
- Fórmulas y listas usan −π…π con ambos extremos. El cálculo no duplica el punto final. Un archivo de período completo uniforme puede comenzar en otra frecuencia; se centra mediante interpolación trigonométrica del dato logarítmico o de la fase corregida.
- Se acepta 0…π cuando se activa Completar por simetría real. El módulo se completa como función par; en fase se comprueban los extremos y se completa la parte impar después de quitar el desplazamiento y la constante de signo. Se registra que esa simetría es una hipótesis de entrada.
- Los ceros del módulo requieren tratamiento explícito: con piso cero se rechazan; un piso positivo modifica el dato y el informe cuenta los puntos afectados. El piso siempre está en amplitud lineal, incluso al cargar dB.

## Salidas útiles y alcance

H reconstruida es una respuesta compleja en rad/muestra, con extremo repetido entre −π y π. Se puede exportar como señal o enviar a Filtros ideales y por tramos para analizar su impulso o aplicarla a una entrada. Su JSON incluye el modelo logarítmico, desplazamiento, convenciones, piso y diagnósticos.

El selector también ofrece h[n]: registro de la inversa numérica en una ventana centrada en d. La frecuencia finita produce aliasing temporal; ese registro no es automáticamente un FIR exacto ni la respuesta infinita completa.

Las figuras externas muestran módulo/dB, fase desenrollada y retardo derivado del modelo cepstral, con eje angular compartido. El CSV de reconstrucción conserva H real/imaginaria y esas curvas. La cantidad de puntos y, cuando procede, la comparación con la mitad de resolución ayudan a estudiar sensibilidad; no son una cota de error frente al sistema real. Se explica la convención del armónico Nyquist en rejillas pares y la posible pérdida de ese componente en un viaje módulo→fase→módulo.

Esta opción es discreta, periódica y numérica. No se recuperan factores paso todo desconocidos, no se deduce una respuesta única a partir de una banda arbitraria y no se ajusta un cociente racional exacto. La reconstrucción analógica general permanece fuera del alcance implementado.

## Organización y ayuda

Los campos H(z) desaparecen en Reconstruir y reaparecen al factorizar o compensar. Recibir una transferencia desde otro menú vuelve al estudio que consume H, evitando dejarla cargada en una operación que la ignora. Cada cálculo conserva su salida anterior al editar el borrador.

Se integran explicaciones en la misma biblioteca y una imagen con dos fases de igual módulo: base mínima y tres retardos adicionales. Las entradas se apilan y se reducen márgenes anidados para evitar desplazamiento horizontal en el panel de dos columnas. Se revisaron 1366, 800 y 640 px, conservando letra legible.

## Evidencia dirigida

Cuatro casos del motor pasaron: IIR analítico desde módulo y su retardo; fase con ganancia/desplazamiento conocidos; respuesta de coeficientes complejos y período desplazado; rejilla impar e impulso FIR conocido, piso explícito, rechazo de bandas incompletas, extensión real de 0…π, equivalencia dB/amplitud y exportación. El grupo tardó 0.25 s localmente.

El recorrido Qt comprobó independencia de los datos, H contra fórmula analítica, ejes compartidos, CSV y JSON, resultado conservado al editar, envío a Filtros ideales y por tramos con cálculo allí, dirección inversa, selección del impulso, ayuda y funcionamiento previo de factorización/controles de compensación. No se hizo una campaña general de pruebas del portable.

CIERRE_1.0.md mantiene el objetivo y las limitaciones vigentes; esta entrega no declara completada la versión estable.
