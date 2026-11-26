# Deuda técnica al evaluar el candidato

| Hallazgo | Estado que se lleva a revisión | Evidencia principal |
| --- | --- | --- |
| C-01 · P1 | Mitigación de entradas y dependencias fijadas. Excepción de distribución abierta. | Auditoría de seguridad y SBOM por plataforma |
| C-02 · P1 | Lecturas JSON y HDF5 acotadas. Riesgo residual del decodificador MATLAB clásico. | Pruebas de integridad de entrada |
| C-03 · P0 | Corrección de asociaciones, cambios y parámetros con verificación atómica. | Regresiones de DFT, DSP, diseño FIR, normalización histórica y reapertura |
| C-04 · P1 | Eje PSD corregido con oráculos por familias. | Auditoría integral y preventiva |
| C-05 · P1 | Límite cooperativo documentado y medido. Pendiente la aceptación de la envolvente. | Banco de recursos y pruebas de pool, plazos y archivos |
| C-06 · P2 | Integridad y alcance de persistencia comprobados. Pendiente proyecto de gran volumen y hojas CAS activas. | SLBIN, sesiones históricas y banco de almacenamiento |
| C-07 · P2 | Controles críticos ampliados. Quedan los objetivos de cobertura indicados en el informe. | Cobertura por plataforma y módulo |
| C-08 · P2 | Interacción compacta Windows comprobada. DPI real y Linux real pendientes. | Capturas y protocolo manual |
| C-09 · P1 | Instaladores y firma de prueba comprobados. Entrega pública pendiente. | Matriz nativa y comparación de versiones |
| C-10 · P2 | Frontera headless y dependencias auditadas. Acoplamientos históricos registrados. | Prueba sin Qt y grafo de imports |

El [registro de riesgos](RESIDUAL_RISK_REGISTER.md) identifica responsables y condiciones de revisión. La valoración anterior conserva el origen documentado en el registro maestro.

## Continuidad de 02C

| Hallazgo | Estado en el nuevo candidato | Condición pendiente |
| --- | --- | --- |
| C-01 | Revaluación de ruedas y binarios en ambos SBOM. | Actualización nativa de Qt y OpenJPEG o decisión explícita E-01. |
| C-02 | MATLAB clásico y HDF5 separados con cuota y plazo. | Rueda HDF5 corregida o decisión E-02 sobre el alcance local mitigado. |
| C-05 | Se cuantificaron memoria de trabajo, concurrencia, escritura y cancelación. | E-03 conserva los límites cooperativos del Core y el simbólico sin cuota de memoria. |
| C-06 | `.slproj` opcional y CAS delimitado. Compatibilidad con JSON verificada. | Validar un barrido de tamaño real y revisar recuperación automática para proyectos grandes. |
| C-07 | E-06c–j alcanzaron el objetivo. | E-06a y E-06b siguen activos. Se priorizan despacho Qt, paneles y escritorio. |
| C-08 | Validación Windows real con gráfico, informe y proyecto científico. | E-05 para Linux real y otros DPI. |
| C-09 | Actualización aislada 2.0.0 → 2.0.1 aprobada. | Firma Windows y canal de distribución siguen como condición independiente E-04. |

## Saldo de la continuación autónoma

SLPROJ superó su objetivo en `54adaa0` y el almacenamiento por lotes verificó 48 corridas. El contrato CAS y el escritor asíncrono completan la persistencia de sesión dentro de su alcance. Se corrigieron la reapertura con foco, los checkpoints obsoletos y la publicación prematura de entradas LTI. La prioridad técnica sigue en la cobertura global, con pruebas de traspaso de datos, diseño, tablas, recuperación y errores. [Registro maestro](../audit/MASTER_TECHNICAL_DEBT_REGISTER.md) · [Matriz por candidato](FINAL_VALIDATION_MATRIX.md#continuación-autónoma)

## Saldo de la matriz de 623c9dd

| Hallazgo | Evidencia | Pendiente |
| --- | --- | --- |
| C-07 · Cobertura | 85 % de líneas y 75 % de ramas alcanzados en ambos runners. Pasaron los 23 controles de los componentes designados en cada plataforma. | Mantener objetivos en la siguiente revisión integral. |
| C-11 · Prueba de fondos | `b6bcb85` corrige la aserción que comparaba rutas por texto y pasa las pruebas locales. | Verificar el nuevo SHA en el runner correspondiente. |
| C-08 · Selector de figuras | `87b74ed` corrige el cambio compacto a amplio. Pasaron el ensayo en Windows real y 83 pruebas locales. | Completar Linux físico y otros DPI. |
| C-01, C-02 y C-05 | Versiones y mitigaciones revisadas. La matriz aprobó el inventario, los perfiles de cancelación y la campaña de persistencia. | Resolver E-01 y E-02 según disponibilidad y alcance. Confirmar el uso dentro de la envolvente E-03. |
| C-09 · Distribución | Actualización aislada y portables verificados. | Resolver firma y canal público por separado. |

[Quality Gate actual](QUALITY_GATE_REPORT.md#evaluación-del-candidato-623c9dd)

En `8e274e7` se verificó en el runner Windows la corrección C-11 de identidad de rutas y la regresión C-08 de figuras. El seguimiento restante separa la evidencia integral sobre un único SHA, el escritorio físico y las condiciones de proveedor y distribución. [Regresiones verificadas](FINAL_VALIDATION_MATRIX.md#regresiones-focalizadas-en-windows-sobre-8e274e7)

## Saldo del candidato a80508c

La matriz única verificó las correcciones C-11 de identidad de rutas y C-08 de figuras, y acreditó las condiciones de cobertura C-07 y E-06a–j. El mantenedor aprobó E-02 y E-03 para archivos MAT confiables y perfiles operativos probados, respectivamente. C-01 y C-02 conservan el seguimiento de proveedores. E-05 mantiene pendiente la validación en Linux real con el alcance Windows aprobado. C-09 conserva firma y canal público como condiciones independientes. [Dictámenes vigentes](QUALITY_GATE_REPORT.md#evaluación-del-candidato-a80508c) · [Aprobaciones](EXCEPTION_APPROVAL_REGISTER.md#aprobaciones-del-mantenedor-del-26-de-noviembre-de-2026)

C-01 resuelve E-01 con los binarios de `64dc3c4` en las dos plataformas. El seguimiento de HDF5 corresponde a C-02 y al alcance ya aprobado de MAT. La firma y el canal público conservan E-04. [Resolución técnica](EXCEPTION_APPROVAL_REGISTER.md#resolución-técnica-de-e-01)

La aprobación del mantenedor de sus pruebas manuales de Linux completa E-05. El saldo de distribución pública corresponde a E-04. [Resolución de E-05](EXCEPTION_APPROVAL_REGISTER.md#resolución-de-e-05) · [Cierre del Core](QUALITY_GATE_REPORT.md#cierre-técnico-de-fase-02c)
