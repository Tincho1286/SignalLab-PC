# Arquitectura de Fase 04

## Flujo actual

1. Workbench y CLI transforman los campos en contratos tipados. Comparten los analizadores de trayectorias. Python acepta los contratos directamente.
2. Los motores en `communications_channel.py` y `communications_fading.py` calculan sobre `Signal` con `ExecutionContext`. Los intervalos y relojes se validan antes de contribuir al registro expandido. Los motores no importan Qt.
3. Las salidas contienen parámetros, huella de entrada y reloj. Los puntos de publicación verifican el cálculo temporal con el Core. El proyecto registra el análisis y las realizaciones enlazados a la salida. CLI utiliza la escritura transaccional de sesiones.
4. Workbench dibuja resultados de los motores en la infraestructura de figuras existente. JSON, SLBIN y SLPROJ conservan sus lectores. Los cambios de significado se registran en el esquema de metadatos del modelo.

## Fronteras para la integración

La composición ejecuta una secuencia ordenada de contratos sobre el registro que entrega cada etapa. Mantiene las señales intermedias, los componentes aleatorios, los relojes y las potencias de entrada y salida. Usa el mismo motor desde el editor de Workbench, la API y la CLI. El informe verifica configuración efectiva, orden y huellas. Los roles se resuelven con los padres del proyecto para que importar una cadena reasigne los identificadores sin alterar el cálculo.

El enlace reutiliza la cadena de pulsos y el receptor de Fase 03. El almacenamiento experimental archiva configuración, resultados intermedios y huellas por etapa. El control sin etapas conserva su convención de reloj y su derivación de semillas. La persistencia verifica las huellas y el orden efectivo de cada etapa al reabrir el proyecto. [Servicios y entradas por interfaz](INTEGRATION_CATALOG.md).

La fase conserva el monolito modular y las dependencias fijadas. La revisión de modelos, almacenamiento y recursos se registra por plataforma. [Plan](PHASE_04_PLAN.md) · [Contratos](SCIENTIFIC_CONTRACTS.md) · [Criterios](QUALITY_GATE_CRITERIA.md)
