# Línea base de Fase 06

| Referencia verificada | Estado al inicio |
| --- | --- |
| `develop` | `85d986500d807c58aa949bf2ececcc0d6bcc8afd`, con la actualización estratégica y el árbol de trabajo limpio. |
| `main` | `10fe3f218de2cdf183a4cc282ebd54aed403a981`, cierre de Fase 05. |
| Preview aceptada | `v2.3.1` en `1311df1f0f954f06eaf5f20c33f645d15748660a`. La matriz oficial y los cinco controles posteriores al merge aprobaron. [Cierre](../phase_05/PHASE_05_INTEGRATION.md) · [Matriz del candidato](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46070995974) · [Controles del merge](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46076665338) |
| Canal Stable | `v2.0.0` en `adfad5c093a236b0565f00f5e97845acf040ec96`. Se consultaron el release público y ambos canales del actualizador. Sus manifiestos devolvieron 2.0.0 Stable y 2.3.1 Preview. |
| Catálogo | 51 herramientas, 105 variantes canónicas y 53 módulos de cobertura crítica en la base aprobada. [Inventario](../TOOL_INVENTORY.md) · [Críticos](../SCIENTIFIC_ENGINE_INVENTORY.md) |

Cada sistema aprobó 1 437 pruebas integrales, 150 preventivas y 384 contrastes científicos. Windows registró 90,06 % de líneas y 77,71 % de ramas. Ubuntu registró 90,01 % y 77,70 %. Los perfiles de estadística y persistencia registraron picos de RSS de 132,48 y 152,30 MiB, y máximos del pulso Qt offscreen de 76,52 y 98,45 ms. Se conserva por separado la línea base de navegación entre documentos abiertos. [Recibo de auditoría](../evidence/post-phase-05-baseline.json) · [Cambio de navegación](../phase_05/IMPLEMENTATION_LOG.md#navegación-entre-herramientas)

La política de MAT para archivos confiables, la admisión estimada de memoria, la cancelación cooperativa, el bloqueo entre procesos en disco local y el seguimiento de Authenticode mantienen su alcance documentado. Los informes de cada plataforma acreditarán las nuevas escalas de RF. [Riesgos](../RISK_REGISTER.md#situación-posterior-a-fase-05) · [Límites de Fase 05](../phase_05/TECHNICAL_DEBT_REGISTER.md)
