# Backlog de SignalLab Engineering

## Próximas decisiones

| Momento | Trabajo de planificación o seguimiento | Evidencia esperada |
| --- | --- | --- |
| Tras autorizar Fase 05 | Confirmar el alcance estadístico, las capacidades reutilizables y el primer recorrido con complejidad progresiva. | Requisitos, contratos, oráculos, presupuesto y plan de regresiones antes de implementar. [Plan de modernización](TOOL_MODERNIZATION_PLAN.md#fase-05--probabilidad-y-estadística) |
| Antes de calificar la primera 2.3.x | Evaluar la habilitación del Quality Gate y empaquetado para la fase nueva. Las modificaciones funcionales de infraestructura requieren autorización. | Informes, paquetes, SHA y manifiesto verificados con los controles vigentes. [Brechas del flujo](../development/releases.md#adaptaciones-pendientes-del-flujo) |
| Durante fases autorizadas | Revisar solapamientos, rendimientos y riesgos del dominio antes de añadir métodos, motores o dependencias. | Trazabilidad, reutilización o justificación de una herramienta independiente, y validación con oráculos. [Roadmap](ROADMAP.md) · [Catálogo de integración](INTEGRATION_CATALOG.md) |
| Seguimiento | Preservar E-04 y los pendientes nativos de Fase 04. Las pruebas específicas de escalado sirven de diagnóstico. | Alcance de cada comprobación y registro de defectos reproducibles. [Estado vigente](PROJECT_STATE.md) · [Riesgos de Fase 04](phase_04/RESIDUAL_RISK_REGISTER.md) |

## Registros históricos

La [matriz de Fase 02B](phase_02b/PHASE_02B_TRACEABILITY_MATRIX.md) registra los nuevos paquetes y sus criterios. Los controles y riesgos de estabilización siguen debajo como referencia.

Prioridades de Fase 01 y condiciones de continuidad. El estado de los controles del candidato está en la [matriz de validación](VALIDATION_MATRIX.md). Los riesgos se registran en [RISK_REGISTER](RISK_REGISTER.md).

| ID | Prioridad | Trabajo | Criterios de aceptación |
| --- | --- | --- | --- |
| E01 | Alta | Resolver R01 y separar la línea base del rediseño no versionado. | Guardar huellas de commit y árbol evaluado. `check_static.py` sin nombres indefinidos. Un campo FIR/IIR inválido muestra el error y conserva la salida previa. Recalcular después de corregirlo produce el resultado esperado. |
| E02 | Alta | Inventariar artefactos y revisar avisos de Python, Qt y dependencias nativas. R02/R03. | SBOM de ambos paquetes, versiones nativas y correspondencia con alertas, parches o decisiones de alcance registradas. Las imágenes válidas se cargan y los formatos no permitidos se rechazan con muestras benignas. Verificar firma, integridad y confianza de actualizaciones en entornos aislados. |
| E03 | Alta | Conciliar versión, canal y procedencia. R05. | Comparar versión y canal de la UI, marca preliminar de GitHub, tag, commit, manifiestos, instaladores y sumas. Usar un solo flujo reproducible para producir esos valores y comprobarlos antes de aprobar el artefacto. |
| E04 | Alta | Definir la fase por origen de DFT/DTFT. R04. | El caso de cuatro muestras del informe reproduce el factor `exp(−jωn₀)` para orígenes positivos y negativos y N par/impar. La opción, el gráfico y la exportación dicen qué convención usan. La IDFT recupera el eje correcto y lee proyectos anteriores. |
| E05 | Alta | Consolidar la línea base matemática y de interacción. R06/R09. | Pruebas completas, gates por familia y oráculos independientes en Windows/Linux. Publicar cobertura de líneas/rutas de proceso y criterios por dominio. Incluir 640×420, 1366×768 y DPI alto con interacción manual en figuras y editores especiales. |
| E06 | Alta | Probar persistencia y reutilización real. R08. | Abrir fixtures de proyecto 1/2 y sesión 1/2/3 en el entorno candidato. Las fórmulas, ROC, clock, conexiones y dependencias conservan significado. La importación inválida no altera la sesión activa. |
| E07 | Alta | Presupuestos por formato y ejecución. R07. | Archivos válidos, corruptos y tamaños límite generan resultados o errores legibles sin comprometer la sesión. La cancelación libera el proceso y los temporales. Medir tiempo y memoria con escalas documentadas. |
| E08 | Media | Perfiles de dependencias y CI. R10/R11. | Una instalación limpia por perfil admite las herramientas declaradas. Capturar dependencias con hashes y avisos por artefacto, evitando añadir runtimes opcionales al núcleo. |
| E09 | Media | Evidencia independiente de diseño por tolerancias y precisión finita. | Probar pasabajos/pasa banda e IIR con extremos verificados fuera de la rejilla de diseño. Para FIR estimado, indicar orden más bajo comprobado y método. Para punto fijo, comparar vectores exactos y reglas de saturación. |
| E10 | Media | Medir acoplamiento antes de modularizar. D01–D06. | Mapa de llamadas y dependencias para un flujo de importación, cálculo y reutilización. Detectar código muerto por referencias estáticas, registro dinámico y ejecución. Mantener el resultado tras extraer la primera frontera. |

### Seguimiento de Fase 01

- E01 se corrigió en la primera estable y la guarda estática del candidato pasa con 375 archivos.
- E02 verificó los runtimes publicados y completó el inventario de archivos nativos del candidato. Se acreditó la revisión de OpenSSL de Ubuntu. Continúan abiertos Qt 6.12.1, los componentes embebidos y el seguimiento de avisos.
- E03 se verificó para la distribución 2.0.0. El candidato se valida como rama de trabajo.
- E04 incorpora la convención explícita, comparaciones analíticas y round trips con las versiones históricas.
- E05 instrumenta líneas, ramas y el worker simbólico. Muestreo y Fourier superan el objetivo de líneas. La cobertura global y la interacción en escritorios con DPI del sistema heterogéneo siguen abiertas.
- E06 verifica tres formatos de sesiones, dos de proyectos, tres de diagramas, ROC y reutilización de un resultado de la hoja CAS. Se conserva el historial ya publicado en la biblioteca.
- E07 mide cálculos representativos y cancelación con limpieza en Windows/Linux. Quedan perfiles de estrés, concurrencia y una política común de plazos y memoria.
- E08 usa ruedas Qt Essentials fijadas. Se contrastaron las bibliotecas nativas empaquetadas con los archivos de sus proveedores. El inventario de dependencias aportadas por el anfitrión queda abierto.
- E09 mantiene los controles de diseño y precisión del gate. Falta ampliar referencias independientes de extremos en banda y orden mínimo.
- E10 actualiza el grafo y propone la DFT como el único piloto mediante ADR.

El criterio para empezar Fase 02 es la salida de estabilización de [ROADMAP](ROADMAP.md) y su autorización específica.

### Seguimiento de Fase 02C

Los hallazgos y acciones pendientes de 02C se gestionan con su prioridad, condición de salida y evidencia. La procedencia verificada y el error de escala de PSD tienen regresiones dedicadas. La cobertura, el escritorio real y la distribución tienen criterios de revisión propios. [Deuda de Fase 02C](phase_02c/validation/FINAL_TECHNICAL_DEBT_REGISTER.md)

## Riesgos y evidencia de 02C

La cobertura global y los controles críticos se alcanzaron en las dos plataformas de la matriz integral. Se conserva la revisión de HDF5 y el alcance aprobado para MAT y los recursos. La matriz de arranque de Fase 03 comprueba en conjunto el motor y el empaquetado definitivos. [Cobertura](phase_02c/testing/FINAL_COVERAGE_REPORT.md) · [Riesgos residuales](phase_02c/validation/RESIDUAL_RISK_REGISTER.md)
