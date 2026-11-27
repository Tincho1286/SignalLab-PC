# ADR 004 · Expansión con modernización de herramientas existentes

**Estado:** decisión estratégica aprobada para la planificación el 27 de noviembre de 2026.

**Alcance:** evolución de la arquitectura y del Workbench en futuras fases autorizadas.

## Contexto

SignalLab ya tiene familias de herramientas, formatos históricos y servicios reutilizados por Workbench, Python y CLI. El inventario identificó capacidades compartidas entre los nuevos dominios y las herramientas originales. Entre ellas están las estadísticas de registros, la PSD, el análisis de ventanas, el punto fijo, el editor LTI y la STFT inversa. [Auditoría de la actualización](STRATEGIC_UPDATE_REPORT.md) · [Plan de modernización](TOOL_MODERNIZATION_PLAN.md)

## Decisión

Mantener Qt y el monolito modular como arquitectura de referencia. Ampliar primero las familias que resuelven la misma tarea e integrar motores detrás de contratos de aplicación verificables sin Qt. Evolucionar los diagramas por casos de uso y preservar la compatibilidad de sesiones, relojes, rutas y procedencia. Validar el patrón de complejidad progresiva en probabilidad y estadística cuando esa fase se autorice. [Arquitectura objetivo](ARCHITECTURE_TO_BE.md) · [Principios del Workbench](UX_DESIGN_PRINCIPLES.md)

Los adaptadores de hardware se evalúan en la Fase 10. Las capacidades de adquisición y procesamiento continuo deberán demostrar recursos medidos, equivalencia científica e independencia del núcleo frente a los drivers. El alcance de redes RF de Fase 06 es analítico.

## Alternativas y consecuencias

Duplicar herramientas por algoritmo aumentaría las rutas, las convenciones y las pruebas de restauración que deben mantenerse. Un editor general, un framework de plugins o la distribución en servicios anticiparían contratos y dependencias antes de tener un caso acreditado. La evolución incremental conserva los recorridos existentes y hace visible el coste de cada ampliación. Un límite que impida cumplir un requisito justifica reconsiderar la alternativa con evidencia y aprobación de alcance.

Cada fase identifica las operaciones reutilizadas y documenta paridad, oráculos, riesgos, presupuestos y compatibilidad antes de calificar su candidato. La política de publicación y aceptación se registra por separado. [Validación](VALIDATION_MATRIX.md#criterios-vigentes) · [Política de entregas](RELEASE_POLICY.md)
