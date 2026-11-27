# Decisiones de Fase 05

## Línea base y continuidad

La cobertura y el rendimiento iniciales se obtuvieron de los artefactos de 2.2.1 Preview, identificados por SHA y cotejados con sus recibos. `d545ffa` solo cambió documentación con respecto al candidato. Se añadieron regresiones focalizadas en el equipo Windows sobre el estado de inicio. [Línea base](PHASE_05_BASELINE.md)

## Reutilización estadística

Se encapsulan las distribuciones conservando parametrización, soporte, estados y semántica de resultados. SciPy es el motor escalar. La validación usa fórmulas y recuentos independientes. Las colas Rician usan la identidad con chi-cuadrado no central. Se constató pérdida de cola al restar una CDF redondeada a uno y se contrastó la corrección con cuadratura independiente. Los motores de fading existentes mantienen su contrato y sus realizaciones.

Se conserva la familia actual del catálogo. Las leyes y consultas son variantes y la covarianza usa el editor de matrices existente. Las opciones originales mantienen índices, campos y el camino de generación histórica. Los nuevos métodos guardan sus registros como señales reutilizables con derivación de semilla y parámetros verificables. [Arquitectura](ARCHITECTURE.md)

## Gate acumulativo

La opción de Actions `phase_05` valida rama, canal y familia/versiones antes de ejecutar el empaquetado. El verificador de Fase 05 reutiliza la decisión de Fase 04 para ambas plataformas. Añade requisitos estadísticos, demostradores, cobertura, recursos y una comprobación empaquetada de probabilidad. El publicador exige fase y número coincidentes para 2.3.x. La calibración científica no puede aprobar mientras falten reportes de calificación o perfiles. [Criterios](QUALITY_GATE_CRITERIA.md)
