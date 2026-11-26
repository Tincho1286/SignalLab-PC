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

## Riesgo residual de la continuación autónoma

| Riesgo | Cambio verificado | Condición residual |
| --- | --- | --- |
| C-01 y C-02 | NumPy y SciPy actualizados. Cuota, plazo y lectura local de MAT activos. | Revisar Qt, OpenJPEG y HDF5 cuando exista una actualización corregida y reproducible. |
| C-05 | Admisión compartida y medición de cancelación ampliadas. | El motor numérico tiene control cooperativo sobre llamadas nativas. MAT tiene terminación y cuota de proceso. |
| C-06 | CAS persistente, proyecto binario y recuperación asíncrona. Campaña completa verificada. | La envolvente de campañas usa proyectos por corrida y catálogo verificado. El formato manual predeterminado sigue siendo JSON. |
| C-07 | Avance global de cobertura y SLPROJ dentro de objetivo. | Cumplir cobertura global y cualquier brecha de componentes críticos que subsista en el candidato. |
| C-08 | Acta Windows real a 96 DPI ampliada. | Validar DPI real y Linux donde estén disponibles. |
| C-09 | Instaladores y salto aislado verificados en `54adaa0`. | Validar el nuevo presupuesto de CI. Firma e infraestructura conservan evaluación particular. |

[Matriz de evidencia](FINAL_VALIDATION_MATRIX.md) · [Registro de excepciones](EXCEPTION_APPROVAL_REGISTER.md)

## Revisión sobre 623c9dd

La brecha global de cobertura quedó satisfecha en los dos sistemas. El riesgo de entorno se materializó en una aserción del test de fondos de Windows y se corrigió localmente con una comparación de identidad. La condición integral permanece abierta para el SHA corregido. El ensayo de escritorio descubrió y aisló el fallo de cambio de disposición. Se verificó su corrección en Windows a 96 DPI. [Quality Gate](QUALITY_GATE_REPORT.md#evaluación-del-candidato-623c9dd) · [Acta](../gui/DESKTOP_CONTINUATION.md#medidas-de-frecuencia-en-el-candidato-623c9dd)

Los controles de presupuesto y cancelación pasaron en los tamaños y operaciones del banco. La admisión estimada y la cancelación cooperativa mantienen su alcance. El importador MAT conserva su cuota de proceso y plazo. Las condiciones nativas de Qt, OpenJPEG y HDF5, la validación física de Linux y DPI y la distribución pública siguen abiertas por sus criterios específicos. [Envolvente](../resources/OPERATIONAL_ENVELOPE.md) · [Decisiones individuales](EXCEPTION_APPROVAL_REGISTER.md#revisión-sobre-623c9dd)

## Alcance residual de a80508c

| Riesgo | Evidencia nueva | Alcance y responsable |
| --- | --- | --- |
| C-01 y C-02 · Dependencias | Ambos SBOM y OpenSSL de Ubuntu verificados. El mantenedor aprobó el uso de MAT con archivos confiables. | Empaquetado conserva el seguimiento de Qt, OpenJPEG y HDF5. El responsable de MAT debe mantener cuota y plazo. El lector conserva los permisos de la cuenta. |
| C-05 · Recursos | Las 22 cancelaciones de cada plataforma conservaron el estado observado. El mantenedor aprobó los perfiles probados. | Las llamadas nativas del motor numérico conservan límites cooperativos, con cuota efectiva del SO sólo en MAT. Los compromisos de recursos fuera de los perfiles aprobados requieren mediciones propias. |
| C-08 · Escritorio | Windows a 100 % y 125 % acreditado en el acta. El mantenedor informó que probó el 150 % y 200 % y aprobó Windows. | Queda pendiente la validación en Linux de escritorio. |
| C-09 · Distribución | El actualizador aislado conservó el destino y la sesión en los dos instaladores. | Distribución debe evaluar la firma de producción y el canal público por separado. |

[Matriz](FINAL_VALIDATION_MATRIX.md#distribución-recursos-y-almacenamiento-de-a80508c) · [Aprobaciones](EXCEPTION_APPROVAL_REGISTER.md#aprobaciones-del-mantenedor-del-26-de-noviembre-de-2026)

## Dependencias después de resolver E-01

La auditoría de `64dc3c4` acreditó Qt 6.12.1 y la retirada de OpenJPEG en los portables x64. La disponibilidad del lote de ruedas fijado corresponde al mantenimiento del entorno de construcción. El seguimiento del lector HDF5 sigue bajo C-02 y los alcances de E-02 y E-03 conservan sus aprobaciones. [Inventarios y criterio](../security/DEPENDENCY_CONTINUATION.md#verificación-de-e-01-en-64dc3c4) · [Decisión](EXCEPTION_APPROVAL_REGISTER.md#resolución-técnica-de-e-01)

## Aceptación de escritorio al cierre

E-05 queda aprobada por las pruebas manuales de Linux informadas por el mantenedor y por el acta de Windows. Una reproducción independiente en Linux conserva el protocolo de escalado y los flujos de interfaz. La firma de producción y el canal público permanecen bajo E-04. [Acta](../gui/DESKTOP_CONTINUATION.md#aprobación-de-linux-de-escritorio) · [Dictamen](QUALITY_GATE_REPORT.md#cierre-técnico-de-fase-02c)
