# Registro de riesgos de Fase 03

| Riesgo | Condición a vigilar | Control y criterio |
| --- | --- | --- |
| R03-01 | Normalización de ruido mezclada con potencia finita, sobremuestreo o ganancia del filtro. | Derivar las magnitudes por dominio real o complejo. Contrastar varianza y curvas de referencia. |
| R03-02 | Mal condicionamiento junto a singularidades de los pulsos. | Cuadratura independiente cerca de cada polo y pruebas de límites. |
| R03-03 | BER cero con tamaño insuficiente o confianza binomial aplicada a observaciones correlacionadas. | Registrar denominadores, método, nivel, hipótesis y exclusiones. Usar réplicas independientes cuando corresponda. |
| R03-04 | Crecimiento de puntos, muestras e índices al barrer parámetros. | Estimación previa, reserva compartida, procesamiento acotado y campañas por corrida. |
| R03-05 | Corridas incompletas o corrupción de datos recuperados. | Escritura atómica, huellas, reapertura y ensayos de interrupción. |
| R03-06 | Diferencias de plataforma o convenciones de módulos externos. | Oráculos aislados, lock actual, prueba de GUI, Python y CLI y matriz sobre SHA común. |
| R03-07 | El margen global de ramas de 02C es sensible a rutas nuevas sin pruebas. | Incluir comprobaciones observables de dominio, fallos y cancelación en cada paquete y medir globalmente con la configuración vigente. |

Los alcances aprobados de MAT y de recursos y el seguimiento de firma se conservan en 02C. [Registro 02C](../phase_02c/validation/RESIDUAL_RISK_REGISTER.md) · [Criterios](QUALITY_GATE_CRITERIA.md)
