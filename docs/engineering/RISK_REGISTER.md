# Registro de riesgos

## Actualización de Fase 06

Las referencias RF reales positivas, la orientación de puertos y las conversiones mal condicionadas tienen contratos y pruebas independientes. Touchstone está acotado al perfil S/Z/Y de 1.0 y 2.0. Se midió el límite de los perfiles RF y la cancelación antes de persistir. La memoria reservada es una estimación y las operaciones nativas conservan cancelación cooperativa. Quedan vigentes las decisiones previas de MAT y distribución. [Límites de Fase 06](phase_06/TECHNICAL_DEBT_REGISTER.md) · [Seguridad](phase_06/SECURITY_REVIEW.md) · [Recursos](phase_06/PERFORMANCE_REPORT.md)

## Situación posterior a Fase 05

Las condiciones vigentes se cotejaron con los artefactos de 2.3.1 y los expedientes de aceptación. Cada modificación de alcance se evalúa con su propia evidencia y aprobación cuando corresponda. [Línea base auditada](STRATEGIC_REVIEW_POST_PHASE_05.md) · [Excepciones de Core](phase_02c/validation/EXCEPTION_APPROVAL_REGISTER.md) · [Seguridad de Fase 05](phase_05/SECURITY_REVIEW.md)

| Riesgo actual | Evidencia y límite | Próxima comprobación y responsable |
| --- | --- | --- |
| Dependencias nativas y origen · R02/R03 | E-01 se resolvió con Qt 6.12.1 y Pillow empaquetado sin OpenJPEG. CPython, OpenSSL del portátil, el vínculo de `cryptography` y los componentes del anfitrión tienen alcances distintos. | Distribución verifica SBOM, avisos, versiones y carga efectiva por candidato. Registrar el cambio de ruedas y sus hashes antes de aceptarlo. [Dependencias](DEPENDENCY_AUDIT.md#línea-base-de-la-entrega-231) |
| MAT/HDF5 · E-02 | Aprobado para archivos confiables y selección explícita. El lector separado aplica límites. | El responsable de entrada reevalúa exposición y componentes nativos. Abrir otro alcance exige mediciones, pruebas y aprobación. |
| Recursos · E-03 y R07 | Los perfiles probados tienen aprobación. El Core usa reservas estimadas y cancelación cooperativa. Una llamada nativa puede retener el control hasta terminar. | Cada motor amplía su envolvente solo con tamaños, memoria, plazos, cancelación y recuperación medidos en ambos sistemas. [Rendimiento](phase_05/PERFORMANCE_REPORT.md) |
| Integridad y escritor concurrente · R08/R13/R14 | Se verificaron esquemas históricos y campaña transaccional con bloqueo nativo en disco local. Las garantías dependen del almacenamiento y el tipo de sesión. | **09** mide cargas multidisciplinarias, archivo grande y recuperación. Cualquier uso en unidades compartidas requiere evidencia de la semántica del sistema de archivos. |
| Escritorio y visualización · R06/R09 | Hay regresiones de escritorio en ambos sistemas, correcciones de gráfico verificadas y aceptación funcional de 2.3.1. Los escalados concretos se usan como diagnóstico. | Workbench supervisa los cinco tramos de latencia y memoria y reproduce defectos observados en la plataforma afectada. [Protocolo](UX_DESIGN_PRINCIPLES.md#medir-el-rendimiento-por-tramo) |
| Authenticode y canal · E-04 | Authenticode sigue abierto como seguimiento de Windows. El manifiesto Ed25519, hashes y elección de canal sí tienen evidencia pública. | Distribución conserva el gate de integridad y firma del manifiesto. Cualquier cambio de claves o política se decide aparte. [Política](RELEASE_POLICY.md) |
| Dominio estadístico | Intervalo Bartlett y bootstrap dependen de modelo e independencia. Kalman acreditado es lineal discreto. | Mantener hipótesis visibles y evaluar nueva calibración si la fase autorizada lo requiere. [Alcance](phase_05/TECHNICAL_DEBT_REGISTER.md) |
| Redes RF y formatos · R11/R12 | Riesgo futuro de Z₀ por puerto, definiciones de onda, orientación, matrices mal condicionadas y archivos fuera de perfil. | **06**, tras autorización, fija contratos, singularidades y límites de Touchstone antes de implementar y acreditar. [Dictamen](STRATEGIC_REVIEW_POST_PHASE_05.md#dictamen-de-preparación-para-fase-06) |

## Riesgos y seguimientos históricos

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
| R03 · CPython y bibliotecas nativas | CPython 3.14.10 y Expat 2.9.0 verificados en los dos instaladores candidatos. OpenSSL de Ubuntu 22.04 coincide con `3.0.2-0ubuntu1.30`. Se identificaron las dependencias nativas distribuidas como archivos. Queda abierta la revisión periódica de avisos, componentes embebidos y dependencias del anfitrión. |
| R04 · Fase DFT/DTFT | Corregido y verificado con oráculos, round trips y sesiones de tres escritores históricos. |
| R05 · Canal y procedencia | Verificado para la estable 2.0.0. Mantener la verificación integrada en toda futura distribución. |
| R06 · Acoplamiento | Verificado con el grafo del candidato. El componente mayor se conserva y el ADR delimita un futuro piloto. |
| R07 · Tamaños y cancelación | Mitigado parcialmente. Se midieron escalas numéricas, frontera de la estimación de RAM y cancelación con limpieza. Quedan por cubrir concurrencia, cargas grandes de archivos y una política de plazos y cuotas para cálculos simbólicos. |
| R08 · Sesiones | Verificadas sesiones de tres escritores, proyectos de dos esquemas, ROC y tres formatos de diagramas. El CAS conserva resultados publicados. El estado activo de sus hojas requiere un contrato propio de persistencia. |
| R09 · Evidencia de pruebas | Muestreo y Fourier superan el objetivo de líneas. La brecha global y la prueba en escritorios reales con varios DPI quedan registradas como excepciones. La revisión visual cubrió cuatro perfiles Qt y hubo interacción en Windows. |
| R10 · Dependencias de instalación | Los archivos de requisitos coinciden para Qt Essentials. Falta consolidar el alcance de los perfiles de instalación y verificar hashes de cada wheel. |

La [línea base de seguridad](SECURITY_BASELINE.md), la [matriz](VALIDATION_MATRIX.md) y el [informe de cierre](PHASE_01_CLOSEOUT.md) detallan el alcance del candidato y las limitaciones que llevan a revisión. R11 y R12 siguen abiertos como condiciones futuras.

## Seguimiento durante el piloto DFT

| Riesgo | Evidencia y límite |
| --- | --- |
| R06 · Acoplamiento | El cálculo y la persistencia del piloto se ejecutaron con las importaciones de Qt bloqueadas. La presentación conserva sus adaptadores de escritorio. |
| R07 · Recursos | El piloto define presupuesto estimado y plazo cooperativo. El bloque FFT nativo devuelve el control al terminar. La carga de un proyecto y su serialización en JSON tienen costes propios. |
| R08 · Procedencia | La DFT publica de forma atómica su entrada nueva y el resultado. Las referencias existentes se mantienen en el proyecto. La CLI asume un escritor por archivo. |
| R02, R03, R05 y R09 · Distribución y escritorio | Continúa el seguimiento de Qt, dependencias y avisos, confianza del actualizador por el canal público y DPI en escritorios reales. |

[Informe del piloto DFT](PHASE_02_DFT_PILOT.md)

## Seguimiento de Fase 02B

| Riesgo | Prioridad | Evidencia, mitigación y criterio pendiente |
| --- | --- | --- |
| R02 · Qt | Alta antes de publicar | La línea base de esta fase conservó Qt 6.12.0. Los índices de las ruedas 6.12.1 devolvieron 404 en la revisión. Revalidar ambos portables con el parche al existir las ruedas. |
| R03 y R05 · Dependencias y distribución | Alta antes de publicar | SBOM y procedencia de OpenSSL forman parte del control de portables. Verificar la entrega real, confianza Windows y actualización por el canal público antes de promover una versión. |
| R07 · Recursos y concurrencia | Alta con datos grandes | El presupuesto del flujo considera resultados retenidos y temporales. El pool coordina los consumidores que comparten instancia. Quedan por cubrir contención entre procesos, trabajos simbólicos y plazos forzosos. |
| R08 · Hojas CAS | Media | Historias completas de CAS requieren un contrato propio de persistencia. Project y session conservan los esquemas ya verificados. |
| R09 · Escritorios y DPI | Media | Continúa la excepción de DPI del sistema y monitores reales de Linux. La matriz de GUI usa pruebas offscreen y el perfil X11 reproducible. |
| R13 · Persistencia científica | Media | El formato experimental verifica integridad y límites en una señal. Autenticación de productor, lectura parcial verificada y rendimiento de sesiones completas se revisan antes de una adopción general. |
| R14 · Publicación de flujos | Media | Project conserva resultados completos con referencias. Coordinar un único escritor por archivo de sesión. La concurrencia entre procesos necesita un contrato adicional. |

[Cierre de Fase 02B](phase_02b/closeout/PHASE_02B_CLOSEOUT.md)

## Seguimiento de Fase 02C

La Fase 02C verifica el contenido publicado y preserva asociaciones de origen al reabrir. Se mantienen en seguimiento las ruedas Qt, los componentes nativos MAT, el límite cooperativo, el uso intensivo de JSON, la cobertura y las condiciones de escritorio y distribución. [Riesgos y responsables](phase_02c/validation/RESIDUAL_RISK_REGISTER.md) · [Aprobaciones](phase_02c/validation/EXCEPTION_APPROVAL_REGISTER.md)

### Continuación autónoma

La hoja CAS activa se guarda como contrato versionado y el escritor de recuperación usa un lock por instancia. El almacenamiento binario tiene evidencia de integridad y reapertura por lotes. Los riesgos que siguen abiertos corresponden a cobertura, latencias fuera de la envolvente, ruedas nativas, escritorios reales adicionales y distribución. [Riesgos actuales](phase_02c/validation/RESIDUAL_RISK_REGISTER.md#riesgo-residual-de-la-continuación-autónoma)
