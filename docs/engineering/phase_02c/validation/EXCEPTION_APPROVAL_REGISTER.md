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
