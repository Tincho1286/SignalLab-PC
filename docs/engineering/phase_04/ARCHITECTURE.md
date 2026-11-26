# Arquitectura de Fase 04

## Flujo actual

1. Workbench y CLI transforman los campos en contratos tipados. Comparten los analizadores de trayectorias. Python acepta los contratos directamente.
2. Los motores en `communications_channel.py` y `communications_fading.py` calculan sobre `Signal` con `ExecutionContext`. Los intervalos y relojes se validan antes de contribuir al registro expandido. Los motores no importan Qt.
3. Las salidas contienen parámetros, huella de entrada y reloj. Los puntos de publicación verifican el cálculo temporal con el Core. El proyecto registra el análisis y las realizaciones enlazados a la salida. CLI utiliza la escritura transaccional de sesiones.
4. Workbench dibuja resultados de los motores en la infraestructura de figuras existente. JSON, SLBIN y SLPROJ conservan sus lectores. Los cambios de significado se registran en el esquema de metadatos del modelo.

## Fronteras para la integración

La composición será una secuencia ordenada de contratos, ejecutada sobre el mismo registro de comunicación. Cada etapa expondrá salidas y estadísticas suficientes para verificar su efecto y para calcular las potencias en una ventana declarada. Debe poder registrar la diferencia entre desplazamiento Doppler, fading, ruido y error de sincronización.

El enlace reutilizará la cadena de pulsos y el receptor de Fase 03. El almacenamiento experimental archivará configuración, resultados intermedios y huellas por etapa. Los perfiles históricos mantendrán sus convenciones y su derivación de semillas. La persistencia y ejecución deberán rechazar un cambio de orden ambiguo o una configuración de registro inválida.

La fase conserva el monolito modular y las dependencias fijadas. La revisión de modelos, almacenamiento y recursos seguirá los controles de salida. [Plan](PHASE_04_PLAN.md) · [Contratos](SCIENTIFIC_CONTRACTS.md) · [Criterios](QUALITY_GATE_CRITERIA.md)
