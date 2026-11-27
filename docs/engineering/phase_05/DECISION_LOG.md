# Decisiones de Fase 05

## Línea base y continuidad

La cobertura y el rendimiento iniciales se obtuvieron de los artefactos de 2.2.1 Preview, identificados por SHA y cotejados con sus recibos. `d545ffa` solo cambió documentación con respecto al candidato. Se añadieron regresiones focalizadas en el equipo Windows sobre el estado de inicio. [Línea base](PHASE_05_BASELINE.md)

## Reutilización estadística

Se encapsulan las distribuciones conservando parametrización, soporte, estados y semántica de resultados. SciPy es el motor escalar. La validación usa fórmulas y recuentos independientes. Las colas Rician usan la identidad con chi-cuadrado no central. Se constató pérdida de cola al restar una CDF redondeada a uno y se contrastó la corrección con cuadratura independiente. Los motores de fading existentes mantienen su contrato y sus realizaciones.

Se conserva la familia actual del catálogo. Las leyes y consultas son variantes y la covarianza usa el editor de matrices existente. Las opciones originales mantienen índices, campos y el camino de generación histórica. Los nuevos métodos guardan sus registros como señales reutilizables con derivación de semilla y parámetros verificables. [Arquitectura](ARCHITECTURE.md)

## Gate acumulativo

La opción de Actions `phase_05` valida rama, canal y familia/versiones antes de ejecutar el empaquetado. El verificador de Fase 05 reutiliza la decisión de Fase 04 para ambas plataformas. Añade requisitos estadísticos, demostradores, cobertura, recursos y una comprobación empaquetada de probabilidad. El publicador exige fase y número coincidentes para 2.3.x. La calibración científica no puede aprobar mientras falten reportes de calificación o perfiles. [Criterios](QUALITY_GATE_CRITERIA.md)

El bloqueo de campañas ejecuta una ruta nativa exclusiva por plataforma. El verificador combina sus arcos y líneas sin alterar el conjunto total medido, exige exclusión entre procesos en cada sistema y conserva las cifras desagregadas. Las demás comparaciones de cobertura siguen midiendo cada plataforma. [Criterios específicos](QUALITY_GATE_CRITERIA.md#registro-de-componentes-críticos)

## Inicialización de ARMA y comparación teórica

El estado manual representa las fluctuaciones alrededor de la media y conserva la convención directa II transpuesta. El calentamiento se simula antes del primer índice visible. Se conserva el estado estacionario como opción predeterminada para que los proyectos anteriores mantengan su interpretación. Para la comparación descriptiva, la CDF teórica discreta se presenta en las ubicaciones evaluadas mediante puntos. El informe identifica su distribución y sus parámetros conocidos. [Auditoría matemática y de interfaz](AUDIT_AND_SCOPE_REPORT.md)

## Aceptación de 2.3.1 y autorización de integración

El 27 de noviembre de 2026, el propietario confirmó que probó los gráficos de 2.3.1 Preview y que funcionaban bien. Aprobó el cierre de Fase 05 y autorizó integrar `develop` en `main`. La aceptación corresponde al candidato publicado `1311df1f0f954f06eaf5f20c33f645d15748660a`. [Validación técnica](CORRECTIVE_PREVIEW_2_3_1.md) · [Publicación](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.3.1)
