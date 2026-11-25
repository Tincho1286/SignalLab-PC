# Registro de riesgos

**Estado** describe la evidencia. Una versión de dependencia afectada prueba el riesgo de ese componente. La exposición de la aplicación depende del formato, el binario y su ruta observable. Los enlaces de verificación se desarrollan en los informes vinculados.

| ID | Prioridad | Estado | Efecto | Reducción propuesta |
| --- | --- | --- | --- | --- |
| R01 | Alta | Regresión comprobada en el árbol local | Una entrada inválida en ramas de diseño de filtros puede producir `NameError` al mostrar el error por `show_input_error` no definido. | Separar los cambios locales, corregir la frontera de validación en Fase 01 y probar un formulario real con entradas inválidas. |
| R02 | Alta | Aviso confirmado para Qt 6.10.0, ruta con autodetección identificada | La carga de un formato de imagen diferente de los permitidos por el diálogo podría alcanzar Qt SVG. El alcance del artefacto requiere inventario. | Aplicar parche o versión compatible, validar formato real y comprobar en ambos paquetes. [Dependencias](DEPENDENCY_AUDIT.md). |
| R03 | Alta | Runtime anterior a parches confirmados | CPython 3.12.10 y componentes nativos requieren revisión para actualizaciones y archivos externos. | Inventario y escaneo por plataforma. Revisar autenticidad, extracción y runtime con parches. |
| R04 | Alta | Diferencia numérica reproducida | Presentar DFT de registro y DFT sobre índices físicos con el mismo rótulo induce lecturas de fase distintas en Fourier. | Alinear contrato, exportación y ayuda conservando la inversión y los registros históricos. [Matemática](MATHEMATICAL_AUDIT.md). |
| R05 | Alta | Discrepancia comprobada | La API confirmó estable 1.9.6 y preliminar 1.9.9 al iniciar. En el commit 1.9.9, la aplicación declara el canal `stable` para el rótulo del escritorio. | Conciliar canal de la app, release, manifiesto y procedencia en la validación de cada entrega. |
| R06 | Alta | Acoplamiento medido | El grafo diferido conecta 229 módulos. Cambios globales pueden afectar rutas de GUI, transportes y cálculo. | Extraer límites por flujo con contratos y pruebas de compatibilidad. |
| R07 | Alta | Límites parciales | Lecturas completas de JSON/`.m` y cálculos simbólicos potencialmente caros pueden consumir memoria o tiempo. El presupuesto dinámico existente ya cubre otros tramos. | Presupuesto coherente por entrada y control de cancelación, plazo y entrega atómica. |
| R08 | Alta | Riesgo de compatibilidad | Persistencia de esquemas históricos y campos de GUI enlazados a nombres de widgets. | Fixtures versionadas para proyectos y sesiones con relojes, resultados y ayudas de procedencia. |
| R09 | Media | Medición incompleta | CI ejecuta familias dirigidas. Cobertura, inventario nativo y compatibilidad en pantallas reales necesitan una verificación reproducible. | Añadir evidencias y criterios por dominio en Fase 01. |
| R10 | Media | Diferencia comprobada de instalación | Tres archivos de requisitos cubren superficies distintas. Una instalación con el archivo mínimo puede fallar en importación o actualización. | Definir perfiles inequívocos con pruebas en entornos limpios. |
| R11 | Media | Riesgo futuro | Adoptar bibliotecas con licencias, dependencias nativas o drivers sin inventario puede dificultar Windows/Linux y la redistribución. | Adaptadores opcionales y aprobación por dependencia, versión y modalidad. |
| R12 | Media | Semántica de dominio | Circulan modelos con unidades y reloj inferido en metadatos libres. Combinar sistemas de comunicaciones, SDR o RF requiere metadatos inequívocos. | Introducir contratos versionados e invariantes de conversión antes de unificar modelos. |

## Actualización de Fase 01

| Riesgo | Estado y alcance actualizado |
| --- | --- |
| R01 · Manejo de error de filtros | Corregido y verificado en 2.0.0. La guarda del candidato vuelve a pasar. |
| R02 · Qt SVG | Mitigado parcialmente en la publicación. La rama actualiza de Qt 6.10.0 a 6.12.0. Los resultados por plataforma y el resto de los avisos tienen seguimiento propio. |
| R03 · CPython y bibliotecas nativas | Runtimes principales verificados en ambos portables. Continúan pendientes CPython parcheado, inventario nativo transitivo y análisis completo de exposición. |
| R04 · Fase DFT/DTFT | Corregido y verificado con oráculos, round trips y sesiones de tres escritores históricos. |
| R05 · Canal y procedencia | Verificado para la estable 2.0.0. Mantener la verificación integrada en toda futura distribución. |
| R06 · Acoplamiento | Verificado con el grafo del candidato. El componente mayor se conserva y el ADR delimita un futuro piloto. |
| R07 · Tamaños y cancelación | Mitigado parcialmente con presupuesto previo para scripts MATLAB. Quedan plazos y estrés por entorno. |
| R08 · Sesiones | Verificado para DFT de los tres esquemas con restauración y guardado. Pendiente ampliar representatividad y compatibilidad de proyectos heredados. |
| R09 · Evidencia de pruebas | Medición de línea y rama verificada en ambos sistemas. Cobertura por debajo de los objetivos orientativos. Pendiente verificar UI con pantallas y DPI reales. |
| R10 · Dependencias de instalación | Los archivos de requisitos coinciden para Qt Essentials. Falta consolidar el alcance de los perfiles de instalación y verificar hashes de cada wheel. |

La [línea base de seguridad](SECURITY_BASELINE.md) y la [matriz](VALIDATION_MATRIX.md) distinguen mitigaciones vigentes y correcciones del candidato. R11 y R12 siguen abiertos como condiciones futuras.
