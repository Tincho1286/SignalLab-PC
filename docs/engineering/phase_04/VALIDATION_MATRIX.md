# Validación de Fase 04

| Control | Evidencia disponible | Pendiente para el candidato |
| --- | --- | --- |
| Canales deterministas | Impulso y DFT directas, desplazamientos exactos, tono analítico, proyección de I/Q, Friis y calibración de potencia. [Oráculos](MATHEMATICAL_AUDIT.md) | Repetir en ambos sistemas sobre el SHA de calificación |
| Modelos estocásticos | Marginales Rayleigh/Rice, cuadratura polar de fase, autocorrelación Clarke y masa espectral, ruido Wiener y sombra log-normal. | Suite integral y casos preventivos en ambos sistemas |
| Consistencia de interfaces | Pruebas del enlace y de resultados guardados desde Workbench, Python y CLI. La CLI se comprueba con las importaciones de Qt bloqueadas. | Suite del candidato y comprobación desde ambos portables |
| Compatibilidad y recuperación | Los ensayos abren registros históricos y proyectos compuestos. Comparan reloj, señales y huellas, reanudan barridos y conservan el archivo previo si se cancela la entrega. | Repetir y archivar resultados sobre el candidato |
| Cobertura global | `2644391` en Windows registró 89,21 % de líneas y 76,17 % de ramas. El informe local conserva una falla de espera en CAS. [Línea base local](IMPLEMENTATION_LOG.md#calificación-local-y-corrección-de-la-escala-doppler) | Resultados integrales aprobados y todos los componentes críticos por encima de sus umbrales |
| Recursos | El perfil de seis etapas se ejecutó, guardó y reabrió con 128, 2 048 y 65 536 símbolos. La exploración cubre memoria, archivo previo, cancelación y latido offscreen. [Mediciones](PERFORMANCE_REPORT.md) | Tiempo y RSS por tamaño, cancelación y concurrencia en el SHA de Windows y Linux |
| Escritorio y distribución | El ensayo offscreen abre y calcula el enlace integrado. | Registro de escritorio real, ambos portables e instaladores y actualización aislada desde 2.0.0 |

## Protocolo de escritorio real

Registrar sistema operativo, SHA o huella del paquete, resolución física, escala del sistema y tema. En Windows usar dos escalas nativas, incluyendo una de 150 % o 200 %. En Linux comprobar un escritorio disponible con su escala nativa. Usar un usuario o perfil de prueba para validar el actualizador y preservar los datos de trabajo.

1. Abrir el catálogo y entrar al enlace. Configurar dos etapas de canal, calcular y exportar el experimento. Cerrar el documento desde la cruz y comprobar que el catálogo conserva el tamaño y que los botones tienen margen respecto del borde.
2. Abrir la herramienta de fading. Cargar dos trayectorias, seleccionar la segunda y abrir las distribuciones y el gráfico Doppler desde el selector de resultados. Cambiar de tema, reducir la ventana y revisar ejes, referencias, navegación y controles de la figura separada.
3. Abrir el archivo exportado. Comprobar la señal antes y después de cada etapa, la referencia de reloj y la reutilización de una señal en otra herramienta. Repetir un barrido corto y retomarlo desde el catálogo de corridas.
4. Registrar resultados y capturas de cada sistema, incluidos cortes, avisos, controles inaccesibles y pasos que necesiten ajuste. Identificar por separado las capturas simuladas y la evidencia del escritorio real.
