# Calificación y publicación de Fase 05

La **2.3.0 Preview** incorpora probabilidad, análisis estadístico, procesos estocásticos y experimentos reproducibles. El proceso de calificación integró las herramientas nuevas con sesiones, gráficos, resultados y registros del laboratorio de canales. Windows Server 2022 y Ubuntu 22.04 validaron el mismo candidato `bde8eaa10bdfb878c22f6dad0c5a93a5e6c932fe`. [Matriz](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46059832440) · [Release](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.3.0)

## Dictámenes

| Dictamen | Resultado |
| --- | --- |
| Calificación científica | Aprobada con oráculos independientes, campañas y cinco demostradores. |
| Calificación técnica | Aprobada para el mismo SHA en Windows y Linux dentro de los perfiles medidos. |
| Distribución Preview | Publicada y verificada con cuatro paquetes, código fuente, comprobantes, inventarios y manifiesto firmado. |
| Aceptación funcional | Pendiente de la revisión del propietario en sus equipos. |
| Integración | Pendiente de aceptación funcional y autorización expresa. `main` continúa en `0c9e3bc`. |
| Fase 06 | Sujeta a autorización expresa. La ejecución sigue en Fase 05. |

## Alcance científico y cambios en las herramientas

Los paquetes WP-00 a WP-10 cubren línea base y calificación, probabilidad, análisis e inferencia, ruido, identificación, espectros, estimación y filtrado, Monte Carlo, integración, recursos y entrega. La trazabilidad ST-00 a ST-10 enlaza las herramientas, contratos y pruebas de cada requisito. [Plan](PHASE_05_PLAN.md) · [Trazabilidad](TRACEABILITY_MATRIX.md)

| Área | Capacidades calificadas |
| --- | --- |
| Generar y analizar | Leyes discretas, continuas y multivariadas, referencias teóricas, estadística, ajuste, intervalos y pruebas con supuestos declarados. |
| Procesos y modelos | Ruido, realizaciones con semilla, correlación y covarianza complejas, AR/MA/ARMA con inicio y calentamiento, estimación Burg y ARIMA, diagnósticos y pronóstico. |
| Densidad y coherencia | Bartlett, Blackman–Tukey, multitaper, PSD paramétrica, espectro cruzado y Lomb–Scargle. Las herramientas distinguen una densidad o potencia normalizada del espectro complejo requerido por una inversa. |
| Estimación y filtrado | ML, MAP, MMSE y LMMSE gaussianos, Wiener, Kalman lineal discreto y adaptación LMS, NLMS y RLS. |
| Experimentos e integración | Réplicas, barridos, números aleatorios comunes y bootstrap. Las campañas conservan los bloques completos para reanudar y las realizaciones de canal conservan su reloj y procedencia. |

Workbench y la consola reutilizan los servicios de Python sin volver a implementar la matemática. La fase conserva `Signal`, `Transfer`, `StateModel`, `Project`, los archivos JSON, SLBIN y SLPROJ y el presupuesto compartido. La entrega de modelos y resultados usa el catálogo transaccional y las campañas aprovechan el bloqueo nativo y los bloques completos. [Arquitectura](ARCHITECTURE.md) · [Contratos científicos](SCIENTIFIC_CONTRACTS.md)

La navegación dejó de preparar documentos ocultos al cambiar de herramienta. En 50 alternancias entre herramientas abiertas en Windows, la mediana pasó de 184,8 a 39,4 ms y el percentil 95 de 213,5 a 45,5 ms. La primera apertura sigue construyendo sus controles. Se verificó el traspaso de un período completo a Serie discreta de Fourier y la selección de destino para herramientas con más de una entrada. [Auditoría matemática y de interfaz](AUDIT_AND_SCOPE_REPORT.md)

## Evidencia matemática y de ingeniería

Los demostradores A–E contraponen distribuciones e intervalos, identificación bajo modelo conocido, filtrado y estimación, campañas recuperadas y análisis de canales. En total verificaron **384 contrastes** por plataforma, con semillas y tolerancias registradas. Las pruebas preventivas cubrieron las familias de cálculo históricas con las semillas del protocolo. [Protocolo](STATISTICAL_VALIDATION_PROTOCOL.md) · [Cómo repetir los estudios](INTEGRATION_CATALOG.md#demostradores)

| Plataforma | Integrales | Preventivas | Líneas | Ramas | Línea base de Fase 04 |
| --- | --- | --- | --- | --- | --- |
| Windows Server 2022 | 1434 | 150 | 90,04 % | 77,69 % | 89,20 % / 76,28 % |
| Ubuntu 22.04 | 1434 | 150 | 89,99 % | 77,68 % | 89,14 % / 76,25 % |

La revisión de seguridad cotejó las huellas del SBOM con el inventario de archivos nativos. Se conservaron los requisitos fijados de Python y bibliotecas, la importación MATLAB para archivos confiables y el seguimiento de Authenticode. Las reservas son estimaciones de admisión y los plazos medidos corresponden a puntos cooperativos. El salto aislado desde 2.0.0 preservó el proyecto y rechazó descargas alteradas. [Seguridad y riesgos](SECURITY_REVIEW.md) · [Rendimiento](PERFORMANCE_REPORT.md) · [Deuda técnica](TECHNICAL_DEBT_REGISTER.md)

| Plataforma | Pico RSS de los perfiles | Mayor pausa de Qt offscreen | Máxima latencia cooperativa medida | Archivo de 262 144 muestras |
| --- | --- | --- | --- | --- |
| Windows Server 2022 | 132,88 MiB | 74,33 ms | 0,644 ms | 4 194 779 bytes |
| Ubuntu 22.04 | 152,21 MiB | 93,04 ms | 0,777 ms | 4 194 779 bytes |

## Paquetes y revisión funcional

| Plataforma | Instalador | Portable |
| --- | --- | --- |
| Windows x64 | [Instalador EXE](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.0/SignalLab-PC-2.3.0-setup.exe) | [Portable EXE](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.0/SignalLab-PC-2.3.0.exe) |
| Linux x86_64 | [Instalador RUN](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.0/SignalLab-PC-2.3.0-linux-x86_64.run) | [Portable TAR.GZ](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.0/SignalLab-PC-2.3.0-linux-x86_64.tar.gz) |

Se comprobaron los adjuntos públicos, sus tamaños y huellas, la etiqueta `v2.3.0` y el manifiesto Ed25519 de los dos instaladores. El actualizador con Preview activada selecciona 2.3.0. El canal estable sigue sirviendo 2.0.0 con los mismos hashes de instalador verificados antes de publicar. [Firma del manifiesto](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.0/SignalLab-updates.json) · [SHA-256](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.0/SHA256SUMS-2.3.0.txt) · [Evidencia del Quality Gate](QUALITY_GATE_REPORT.md)

La aceptación funcional puede reproducirse con seis recorridos breves, incluidos el cambio de menú que motivó la corrección y la reapertura de una campaña. [Protocolo de revisión](FUNCTIONAL_ACCEPTANCE.md)
