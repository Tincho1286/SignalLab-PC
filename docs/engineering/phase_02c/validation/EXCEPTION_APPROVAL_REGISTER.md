# Aprobación de excepciones

| ID | Excepción | Estado |
| --- | --- | --- |
| E-01 | C-01. Qt 6.12.0, OpenJPEG 2.5.4 y revisión de componentes embebidos. Condición de distribución. | Pendiente de resolución o aceptación explícita |
| E-02 | C-02. Alcance de la importación MATLAB clásica y HDF5 2.0.0 con archivos externos. | Pendiente de aceptación explícita de su alcance operativo |
| E-03 | C-05. Límite cooperativo, sin cuotas duras de memoria o tiempo por motor. | Pendiente de aceptación de la envolvente medida |
| E-04 | C-09. Firma Windows, salto de versión real y canal de distribución. | Pendiente de resolución o aceptación explícita como condición de distribución |
| E-05 | C-08. Evidencia de Linux real y DPI por monitor. | Pendiente de actas o definición expresa del alcance |
| E-06 | C-07. Brechas globales y por módulo. Cada celda por debajo del objetivo se trata individualmente. | Pendiente de aceptación. Consultar el [informe de cobertura](../testing/FINAL_COVERAGE_REPORT.md) |

La validación de Fase 02C mantiene las excepciones abiertas hasta disponer de evidencia adicional o una decisión explícita.

## Revisión del candidato faef335

| ID | Estado de la condición | Próximo criterio o decisión |
| --- | --- | --- |
| E-01 | Abierta. El portable sigue incluyendo Qt 6.12.0 y la rueda Linux de Pillow sigue incluyendo OpenJPEG 2.5.4. | Esperar componentes corregidos con binarios compatibles y repetir la matriz, o decidir individualmente su alcance de distribución. |
| E-02 | Mitigada con proceso y cuota del SO. HDF5 sigue en 2.0.0 y el lector conserva permisos de usuario. | Esperar la rueda corregida o decidir individualmente si la importación local acotada cubre el uso autorizado. |
| E-03 | Cuantificada. MAT tiene plazo y cuota efectivos. El resto conserva control cooperativo y memoria estimada. | Decidir si la envolvente medida basta para el alcance estudiado o pedir cuotas y cancelación externas para operaciones numéricas específicas. |
| E-04 | Se verificó el salto aislado desde 2.0.0. La firma Windows y el canal público siguen abiertos. | Decidir de forma independiente la política de firma y el canal, con autorización específica para distribuir. |
| E-05 | Windows real a 100 % validado para el flujo documentado. | Obtener actas de Linux real y DPI de sistema o decidir individualmente el alcance admitido. |
| E-06a | Abierta. Líneas globales por debajo de 85 %. | Mantener 85 % y continuar pruebas relevantes de GUI, escritorio y despacho de herramientas. |
| E-06b | Abierta. Ramas globales por debajo de 75 %. | Mantener 75 % y cubrir rutas de error, recuperación y traspaso entre herramientas. |
| E-06c–j | Cada componente designado alcanzó su objetivo de ramas en la matriz. | Condiciones verificadas por evidencia. |

Este registro conserva pendientes las decisiones de aceptación individual. [Cobertura](../testing/FINAL_COVERAGE_REPORT.md) · [Revisión de dependencias](../security/DEPENDENCY_CONTINUATION.md) · [Acta de escritorio](../gui/DESKTOP_CONTINUATION.md)

## Continuación autónoma

| ID | Estado e impacto | Evidencia o criterio pendiente |
| --- | --- | --- |
| E-01 | Condición externa para distribución del portable. Qt y OpenJPEG siguen bajo seguimiento. | Incorporar ruedas verificadas que reparen los avisos aplicables y reconstruir ambos paquetes. |
| E-02 | Riesgo del parser nativo con archivos no controlados. MAT conserva selección local, cuota y plazo. | Verificar una rueda h5py con corrección del parser. El proceso conserva los permisos de su cuenta. |
| E-03 | Admisión compartida implementada y validada para los perfiles medidos en Core numérico, persistencia y MAT. | Registrar operación, tamaño y latencia para cualquier alcance adicional. Las cuotas del SO aplican al lector MAT. |
| E-04 | Actualización técnica aislada revalidada en `eb50895` en ambas plataformas. | Firma Authenticode y canal público requieren evaluación propia. |
| E-05 | Windows 96 DPI real incluye recuperación CAS. | Actas de escritorio Linux real y de escalas del SO en monitores disponibles. |
| E-06a y E-06b | Pendientes internos. | Alcanzar 85 % de líneas y 75 % de ramas. Medir también los componentes críticos nuevos. |
| E-06c–j | Dentro del objetivo en ambas plataformas de `eb50895`. SLPROJ, CAS y controlador de sesiones también cumplen. | Mantener mínimos y validar en cada candidato integral. |

El [Quality Gate](QUALITY_GATE_REPORT.md#continuación-autónoma-de-fase-02c) registra los pendientes antes de cualquier solicitud de decisión. [Evaluación nativa](../security/DEPENDENCY_CONTINUATION.md) · [Protocolo de escritorio](../gui/DESKTOP_CONTINUATION.md)

## Revisión sobre 623c9dd

| ID | Estado | Criterio o decisión que queda |
| --- | --- | --- |
| E-01 | El inventario confirma Qt 6.12.0 y OpenJPEG 2.5.4. Se revisó la falta de ruedas corregidas. | Definir si el cierre exige las ruedas corregidas o admite un alcance delimitado con las mitigaciones de entrada vigentes. |
| E-02 | HDF5 sigue pendiente de versión corregida publicada. El proceso lector mantiene cuota y plazo. | Decidir si se admite el alcance actual de archivos MAT locales seleccionados, con la restricción de exposición documentada. |
| E-03 | Pasaron 22 perfiles de cancelación y ambos inventarios de recursos. | Confirmar el alcance ensayado o identificar la operación y presupuesto que requieran aislamiento adicional. |
| E-04 | Portables e instaladores probados con el canal de auditoría. | Evaluar la firma de producción y el canal público en una autorización separada. |
| E-05 | Windows real a 96 DPI verificado. El hallazgo de Abrir gráfico se corrigió y se comprobó en el mismo monitor. | Obtener las actas de Linux real y escalados físicos, o definir explícitamente los perfiles de escritorio que se aceptarán. |
| E-06a–j | Objetivos medidos alcanzados en `623c9dd` en los dos sistemas. | Conservar los umbrales. La aserción de rutas del trabajo integral se corrigió en `b6bcb85` y requiere confirmación sobre ese código. |

Ninguna excepción fue aprobada por este expediente. [Quality Gate](QUALITY_GATE_REPORT.md#evaluación-del-candidato-623c9dd)

El despacho focalizado de `8e274e7` confirmó en Windows 2022 la corrección de la prueba de fondos y el comportamiento de figuras al redimensionar. Los objetivos E-06 siguen acreditados por la matriz de `623c9dd`. El control integral del SHA corregido y las actas físicas restantes de E-05 conservan sus propios criterios. [Regresiones en Windows](FINAL_VALIDATION_MATRIX.md#regresiones-focalizadas-en-windows-sobre-8e274e7)

## Decisiones del candidato a80508c

| ID y evidencia | Alternativas y recomendación técnica | Riesgo al aceptar el alcance o mantenerlo pendiente | Impacto |
| --- | --- | --- | --- |
| E-01 · Siguen pendientes ruedas Qt corregidas y una publicación OpenJPEG con la corrección. El SBOM identifica el material que se distribuye. | Esperar los binarios corregidos y validar ambos empaquetados. Cualquier aceptación anticipada debe delimitar los formatos de entrada y mantener la revisión de componentes. | La aceptación conserva código nativo con avisos. La espera demora el dictamen de distribución. | Condición de distribución y seguimiento del cierre. |
| E-02 · HDF5 2.0.0 sigue afectado según el proveedor. El importador aplica proceso separado, cuota, plazo y validación de entradas. | Esperar la rueda corregida o aceptar explícitamente MAT para archivos locales seleccionados, sin ingreso automático de archivos externos. Se recomienda conservar el alcance local durante la espera. | La aceptación deja exposición al parser con los permisos de la cuenta. La espera mantiene pendiente la condición de importación. | Cierre del Core, preparación para Fase 03 y alcance de la distribución. |
| E-03 · Se acreditaron 71 perfiles y 22 cancelaciones por plataforma. La cuota del SO corresponde al lector MAT. | Aprobar los tamaños y operaciones ensayados, o identificar las operaciones que requieren un plazo forzado o una cuota adicional. Se recomienda basar la decisión en la envolvente publicada. | La aceptación mantiene la variación fuera de los perfiles y los límites cooperativos. Exigir garantías adicionales obliga a medir y revalidar la operación que se amplíe. | Cierre del Core y alcance técnico de Fase 03. |
| E-04 · Actualización de 2.0.0 a 2.0.1 e instaladores verificados con el canal aislado. | Mantener pendiente la distribución hasta contar con un criterio de firma de producción y autorización del canal. | Distribuir fuera de ese criterio conserva el posible bloqueo de Windows y la falta de validación pública. La espera mantiene disponible el canal estable existente. | Distribución pública. |
| E-05 · Acta física de Windows a 100 % y 125 %. Faltan Linux real y los perfiles de DPI que el monitor disponible no ofrece. | Completar el protocolo en otro escritorio o aprobar expresamente los perfiles cubiertos. Se recomienda aportar las actas faltantes. | Aceptar sólo la evidencia disponible deja sin comprobar esos perfiles. Mantener el protocolo completo requiere acceso a otro entorno. | Cierre del Core y disponibilidad de evidencia de escritorio para Fase 03 y distribución. |

El informe deja pendientes las decisiones individuales. La distribución pública requiere una autorización separada. [Dependencias y SBOM](../security/DEPENDENCY_CONTINUATION.md#inventario-del-candidato-a80508c) · [Acta y protocolo](../gui/DESKTOP_CONTINUATION.md#acta-windows-del-candidato-a80508c) · [Resultados de distribución y recursos](FINAL_VALIDATION_MATRIX.md#distribución-recursos-y-almacenamiento-de-a80508c)

E-06a–j quedaron acreditadas por medición en los dos sistemas. Se alcanzaron los umbrales globales y los de los componentes designados. [Cobertura por plataforma y componente](../testing/FINAL_COVERAGE_REPORT.md#cobertura-del-candidato-a80508c)
