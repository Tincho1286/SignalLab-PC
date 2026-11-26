# Límites y deuda técnica de Fase 04

| Elemento | Alcance actual | Revisión posterior |
| --- | --- | --- |
| Trayectorias de retardo fraccionario | El canal determinista admite retardos enteros. El deterioro temporal separado usa interpolación de sinc truncado con errores y bordes documentados. | Para retardos fraccionarios por camino, definir ancho de banda, error de módulo y fase, latencia y extensión en los bordes antes de habilitarlos. [Decisión](DECISION_LOG.md#retardos-fraccionarios-y-coherencia-del-impulso) |
| Escenarios geométricos | El laboratorio conserva modelos explícitos de pérdidas, fading de banda base y una cadena configurable. | La evaluación de perfiles 3GPP, redes y antenas requiere oráculos y presupuesto propios. [Referencias](INTEGRATION_CATALOG.md#elección-de-referencias) |
| Cancelación durante bloques nativos | El motor comprueba la cancelación entre bloques y conserva el archivo anterior hasta finalizar. La latencia solo se afirma para los perfiles medidos. | Repetir la caracterización ante nuevas cargas. Evaluar aislamiento de proceso si un perfil aprobado supera el criterio. [Criterios](QUALITY_GATE_CRITERIA.md) |
| Selección de Fs en Workbench | Clarke y los desplazamientos en Hz requieren una señal con reloj. En la herramienta se puede cargar un archivo con Fs o reutilizar el resultado de una generación o enlace. | Evaluar la conveniencia de un selector de reloj en la misma herramienta. El criterio de cálculo sigue exigiendo una tasa válida y declarada. [Uso del laboratorio](README.md) |

Este registro delimita características futuras. Los controles de aceptación pendientes se siguen en la [matriz](VALIDATION_MATRIX.md) y conservan sus umbrales.
