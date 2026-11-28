# Arquitectura RF

La capa RF amplía el monolito modular. El modelo de red y cada motor se ejecutan sin Qt. Los adaptadores Workbench y CLI usarán las mismas solicitudes de Python. [Decisión de representación](ADR-006-RF-NETWORK.md)

| Capa | Responsabilidad |
| --- | --- |
| RFNetwork | Eje y referencias explícitos, matrices y etiquetas, unidades, propiedad de los datos. |
| Análisis RF | Solución lineal, conversión, diagnóstico físico, líneas y adaptación. Los cálculos con modelos de red reutilizan la misma convención. |
| Core | `ExecutionContext`, checkpoints, reservas, datos y procedencia. `Transfer` representa filtros escalares y `Signal` registros con rejilla uniforme. |
| Almacenamiento e intercambio | Redes con esquema versionado dentro de `Project`, codificación compleja, huellas y guardado transaccional. Touchstone es un adaptador de intercambio. |
| Presentación | Selector por tarea, figura de Smith y medidas legibles. Los modelos científicos quedan separados del código de dibujo. |
