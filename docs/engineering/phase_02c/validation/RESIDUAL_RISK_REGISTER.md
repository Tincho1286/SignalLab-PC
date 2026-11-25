# Riesgos residuales de Fase 02C

| Identificador | Prioridad y condición | Mitigación y responsable | Criterio de revisión |
| --- | --- | --- | --- |
| C-01 · Qt, avisos y componentes embebidos | P1 de distribución, dependencia externa | Mantenimiento de empaquetado conserva controles de decodificación raster y seguimiento del runtime | Confirmar ruedas corregidas, reconstruir ambos portables y revisar sus rutas y componentes embebidos |
| C-02 · MATLAB y HDF5 | P1 si se incorporan archivos externos sin control | Mantenimiento del importador acota los archivos y la selección de datos locales. La ruta HDF5 usa un atributo nombrado y el lector clásico usa SciPy | Revisar actualización nativa, consumo y aislamiento antes de usarlo como ingreso masivo de archivos externos |
| C-05 · Consumo y plazo nativo | P1 para cargas fuera de la envolvente | Mantenimiento del Core aplica estimaciones, pool y puntos cooperativos | Verificar de nuevo con los tamaños previstos y excluir de esa envolvente la latencia garantizada de llamadas nativas |
| C-06 · Proyecto y CAS | P2, limitación operativa | Mantenimiento de persistencia conserva JSON y prueba resultados CAS publicados | Reevaluar formatos de proyecto para volúmenes superiores y definir persistencia de hojas CAS activas |
| C-07 · Cobertura | P2 con efecto en la puerta de cierre | Mantenimiento de pruebas controla regresiones con referencias y mide brechas por módulo | Cumplir los objetivos o aceptar cada excepción detallada |
| C-08 · Escritorio | P2 de validación | Mantenimiento de GUI aporta capturas y protocolo real | Adjuntar actas de Linux y DPI de sistema a 125 %, 150 % y 200 % según disponibilidad |
| C-09 · Actualización y firma | P1 limitado a distribución | Mantenimiento de releases conserva comprobaciones aisladas con firma descartable | Confirmar una versión superior, instalar desde 2.0.0 en un entorno aislado y comprobar autoría del artefacto Windows |
| C-10 · Rutas históricas Qt | P2, mejora futura | Mantenimiento del Core conserva la frontera del piloto y hereda las pruebas de paneles | Incorporar nuevas fronteras sólo con equivalencia demostrada |

## Estado después de la continuidad

| Riesgo | Evidencia nueva | Alcance residual y responsable |
| --- | --- | --- |
| C-01 · E-01 | Ruedas públicas revisadas y SBOM de ambos paquetes. | Empaquetado debe incorporar y verificar la corrección aplicable de Qt y OpenJPEG cuando esté disponible. |
| C-02 · E-02 | El lector MATLAB aplica cuota, plazo y rechazo de referencias externas. | El responsable del importador conserva el alcance de archivos locales y seguimiento HDF5. El proceso conserva los permisos de la cuenta. |
| C-05 · E-03 | Envolvente hasta 1 048 576 muestras en los perfiles indicados, con 67 mediciones por plataforma. | El equipo de Core debe medir otros tamaños y operaciones. El motor numérico sigue sujeto al costo de una llamada nativa y el simbólico separado conserva consumo sin cuota propia. |
| C-06 | Proyecto opcional transaccional con recuperación ante escritura interrumpida y compatibilidad JSON. | Persistencia debe evaluar el perfil de barrido completo y el costo de autoguardado JSON. Hoja CAS activa, variables y borradores permanecen en memoria. |
| C-07 · E-06a/b | Las ramas requeridas de componentes designados alcanzaron los objetivos. | Cobertura global de líneas y ramas sigue bajo objetivo. El contenedor nuevo requiere más pruebas de errores y recuperación antes de usarlo en campañas grandes. |
| C-08 · E-05 | Flujo manual de Windows, dos tamaños, 100 %. | Validación de Linux real y transiciones DPI pendiente. |
| C-09 · E-04 | Salto 2.0.0 → 2.0.1 probado con instaladores reales y firma descartable. | Autoría y confianza del binario Windows y decisión de canal siguen en manos de distribución. |

[Envolvente](../resources/OPERATIONAL_ENVELOPE.md) · [Evidencia de escritorio](../gui/DESKTOP_CONTINUATION.md) · [Cobertura](../testing/FINAL_COVERAGE_REPORT.md)
