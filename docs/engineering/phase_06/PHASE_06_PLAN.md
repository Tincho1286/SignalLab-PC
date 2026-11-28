# Plan de ejecución de Fase 06

| Paquete | Salida verificable | Insumos |
| --- | --- | --- |
| WP-00 · Auditoría | Ramas, versiones, cobertura, recursos, catálogo, referencias y expediente inicial verificados. | Evidencia aceptada de 2.3.1. |
| WP-01 · Modelo | Frecuencias explícitas, tipo de parámetro, orden, referencias por puerto, unidades, convención, metadatos e identidad. | `ExecutionContext` y procedencia. |
| WP-02 · Redes | Conversiones, cascadas, terminación y magnitudes con diagnóstico de singularidad. Demostrador A. | Modelo WP-01, oráculos de circuito. |
| WP-03 · Líneas y adaptación | Líneas con y sin pérdidas, Smith, adaptación puntual y respuesta en banda. Demostrador B. | Redes y solver WP-02. |
| WP-04 · Filtros | Bessel con normalización, comparación y sensibilidad sobre el diseñador existente. Demostrador C. | `Transfer`, respuesta y diseño analógico. |
| WP-05 · Enlaces y dispositivos | Presupuesto, ruido, cascada de Friis y modelo analítico de compresión e intermodulación. Demostrador D. | Propagación, potencia y ruido de referencia. |
| WP-06 · Espectros y ventanas | CZT, Zoom FFT, ventanas ampliadas, métricas y picos. Demostrador E. | `Signal`, DFT, windowing y medidas. |
| WP-07 · Experimentos | Sensibilidad, tolerancias y campañas reanudables con parámetros y procedencia. | Motores WP-02 a WP-06 y campaña de Fase 05. |
| WP-08 · Interfaces y archivos | Workbench, Python, CLI, Touchstone, almacenamiento y demostrador F de ida y vuelta. | Contratos comunes y formatos históricos. |
| WP-09 · Calificación | Oráculos, demostradores A–F, cobertura, compatibilidad, seguridad y perfiles. | Evidencia acumulada y pruebas de WP-01 a WP-08. |
| WP-10 · Entrega | Matriz Windows/Linux sobre un SHA, paquetes verificados y 2.4.0 Preview con manifiesto firmado. | Gate aprobado y expediente de cierre. |

La publicación habilita la revisión del propietario. El merge y la apertura de Fase 07 requieren sus propias autorizaciones. [Política](../RELEASE_POLICY.md)
