# Auditoría matemática y modernización de herramientas

## Hallazgos corregidos

| Hallazgo | Causa | Evidencia de regresión |
| --- | --- | --- |
| Un cambio de herramienta hacía trabajo sobre los documentos ocultos. | La activación volvía a preparar formularios y gráficos que ya tenían una vista. | Se midieron 50 cambios reales de herramienta con eventos de Qt procesados. La mediana pasó de 184,8 a 39,4 ms y se conservó el borrador al regresar. |
| El traspaso a Serie de Fourier permitía elegir una entrada de correlación. | El buscador de destinos enumeraba los controles por dominio, incluidos los que la herramienta mantenía ocultos para otros análisis. | La transferencia usa el período de tres muestras de una señal con vista de dos. El selector sigue disponible para las dos entradas en pestañas de Multiplicar señales. |
| La simulación de ARMA siempre iniciaba con un estado estacionario e ignoraba condiciones iniciales alternativas. | El muestreo del estado y el filtrado se hacían en una única ruta. | Una recurrencia escalar reconstruida con innovaciones conocidas coincide con el estado manual y el prefijo descartado. La realización estacionaria coincide con el filtrado en un solo tramo. |
| Una combinación representable de ganancia y ruido podía producir error o varianza cero. | El motor elevaba coeficientes grandes al cuadrado antes de aplicar la escala del ruido. Una innovación de varianza subrepresentable podía redondearse a cero. | La covarianza y PSD de un MA(1) con ganancia de 10²⁰⁰ y desviación de 10⁻¹⁵⁰ coinciden con las fórmulas cerradas. El ruido positivo fuera del rango de varianza recibe un diagnóstico. |
| La consola podía preparar una campaña antes de rechazar la exportación a su catálogo. | La validación se hacía dentro de la escritura del CSV. El bloqueo de Windows escribía un centinela antes de adquirir la exclusión. | Una salida inválida conserva los archivos anteriores y la carpeta aún inexistente. Dos procesos no adquieren el mismo bloqueo a la vez y el segundo puede reintentar. |

Los cinco demostradores amplían la revisión a estimación de parámetros, identificación, filtrado óptimo y adaptativo, campañas reproducibles y análisis de señales de canales. Los oráculos se desarrollan por separado de la ruta evaluada y sus tolerancias quedan en los informes de cada caso. [Protocolo de validación](STATISTICAL_VALIDATION_PROTOCOL.md) · [Demostradores](INTEGRATION_CATALOG.md#demostradores)

## Herramientas y experiencia de uso

Las herramientas de la fase conservan sus accesos habituales en Señales aleatorias, Fourier y Estimación. Los motores de ley, correlación, espectros y estimación se reutilizan desde el Workbench y las rutas headless expuestas. Se pueden guardar las curvas como resultados con su entrada y retomar el análisis desde el proyecto. El informe de ARMA presenta la condición de inicio y las variantes válidas de una comparación de parámetros sobre el mismo eje.

El cambio de navegación conserva el contenido de las herramientas abiertas y retrasa el dibujo de las figuras cerradas. La primera apertura incluye la creación de controles. Se probaron el regreso a un borrador, el acceso a figuras, la aplicación de temas y la recuperación de sesiones. Los resultados offscreen se registran como diagnósticos automatizados de interfaz. [Registro de implementación](IMPLEMENTATION_LOG.md) · [Perfiles de interfaz](PERFORMANCE_REPORT.md)

## Evidencia todavía pendiente

La matriz del candidato debe consolidar cobertura, regresiones matemáticas, recursos, empaquetado, actualización y verificación de archivos en ambos sistemas. Los intervalos de Bartlett se califican con sus supuestos de ruido blanco y bloques disjuntos. La extensión a otros estimadores depende de que el método y sus hipótesis justifiquen la cobertura publicada. [Trazabilidad](TRACEABILITY_MATRIX.md) · [Criterios de aprobación](QUALITY_GATE_CRITERIA.md)
