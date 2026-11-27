# Validación de Fase 04

Windows Server 2022 y Ubuntu 22.04 aprobaron la suite integral, cobertura y paquetes sobre `a3026d2`. La tabla identifica la evidencia de cada control y la comprobación pendiente de escritorio. [Matriz aprobada](QUALITY_GATE_REPORT.md)

| Control | Evidencia disponible | Estado |
| --- | --- | --- |
| Canales deterministas | Impulso y DFT directas, desplazamientos exactos, tono analítico, proyección de I/Q, Friis y calibración de potencia. [Oráculos](MATHEMATICAL_AUDIT.md) | Matriz aprobada |
| Modelos estocásticos | Marginales Rayleigh/Rice, cuadratura polar de fase, autocorrelación Clarke y masa espectral, ruido Wiener y sombra log-normal. | Suite integral y casos preventivos aprobados |
| Consistencia de interfaces | El experimento del escritorio Windows reprodujo las mismas muestras, relojes, unidades, métricas y huellas desde Python y CLI con Qt bloqueado. [Contraste de interfaces](evidence/candidate-2a0a3fd/windows-interface-parity.json) | Matriz y enlace empaquetado aprobados |
| Compatibilidad y recuperación | Los ensayos abren registros históricos y proyectos compuestos. Comparan reloj, señales y huellas, reanudan barridos y conservan el archivo previo si se cancela la entrega. | Matriz aprobada |
| Cobertura global y crítica | Ambas plataformas alcanzaron los umbrales de líneas y ramas con conteos exactos. [Cobertura](QUALITY_GATE_REPORT.md) | Matriz aprobada |
| Recursos | Los perfiles de seis etapas y 128, 2 048 y 65 536 símbolos se verificaron en ambos runners sobre `a3026d2`. Se comprobaron memoria, archivo previo, cancelación, concurrencia y respuesta offscreen. [Mediciones](PERFORMANCE_REPORT.md#repetición-sobre-a3026d2) | Perfiles medidos aprobados |
| Escritorio y distribución | Windows verificó enlace, exportación, cierre de pestaña y distribuciones. Clarke calculó y abrió ambas figuras al 125 % nativo. El propietario confirmó el funcionamiento en Linux. Ambos sistemas aprobaron instalador y actualización aislada desde 2.0.0. [Distribución](QUALITY_GATE_REPORT.md#paquetes-de-revisión-de-a3026d2) | Pendientes 150 % y 200 % nativos en Windows y el detalle del perfil Linux. Se observó recorte al 200 % con escalado de Qt. |

## Observación de escritorio Windows

Se usó el código de `2a0a3fd` con el complemento `windows` de Qt 6.12.0, en un escritorio a 1366 × 768, escala nativa 100 % y 96 DPI. Workbench mostró el enlace a 1101 × 692 píxeles en tema oscuro. El enlace multitrayecto más fading Rician calculó 4 096 bits y archivó ambas etapas. El proyecto exportado se reabrió con sus huellas y los mismos 20 errores observados. Al cerrar la pestaña, el catálogo conservó el ancho y el botón de cierre se observó con margen respecto del borde.

La figura de distribuciones de la trayectoria Rician seleccionada abrió con ejes y referencias legibles para envolvente y fase. La primera sesión quedó detenida durante Clarke. [Registro de Windows al 100 %](evidence/candidate-2a0a3fd/windows-native-desktop.json)

Se retomó Clarke desde el código candidato `a3026d2` con Qt 6.12.0, dos trayectorias, una entrada reabierta a 96 kHz y Doppler máximo de 64 Hz. El mismo cálculo produjo 16 461 muestras y abrió **Distribuciones de envolvente y fase** y **Autocorrelación y PSD Doppler** en las tres comprobaciones.

| Escala | Configuración | Resultado de geometría |
| --- | --- | --- |
| 125 % | Windows nativo en 1366 × 768. | La ventana y ambas figuras entraron en el escritorio. [Registro](evidence/candidate-a3026d2/windows-clarke-native-125.json) |
| 150 % | Escalado de Qt sobre Windows al 100 %. | La ventana y ambas figuras entraron en el escritorio. [Registro](evidence/candidate-a3026d2/windows-clarke-qt-150.json) |
| 200 % | Escalado de Qt sobre Windows al 100 %. | En 683 × 360 unidades lógicas útiles, la ventana principal excedió el borde inferior en 88 unidades. Las figuras lo excedieron en 81 y 50. [Registro](evidence/candidate-a3026d2/windows-clarke-qt-200.json) |

El panel integrado ofreció 100 % y 125 % en el selector directo de Windows. Se restauró el 100 % al terminar la sesión. Las escalas de Qt se registran como comprobaciones de interfaz y dejan pendiente la observación nativa al 150 % y 200 %.

## Confirmación de Linux

El propietario confirmó el 26 de noviembre de 2026 que el candidato funciona en Linux. La resolución, la escala y los resultados de cada paso del protocolo quedan pendientes de registro.

## Comprobaciones de 2.2.1 Preview

En Windows, la regresión de Clarke se repitió sobre `08cd1bc` a 1366 × 768 con escalado de Qt al 200 %. La ventana principal y ambas figuras quedaron dentro de 683 × 360 unidades lógicas útiles. En Fedora 44, el portable consultó GitHub y verificó los manifiestos firmados de ambos canales. El cierre aprobado conserva como pendientes Windows con escalado nativo al 150 % y 200 % y la prueba interactiva en Fedora Plasma. [Registro Windows](evidence/candidate-08cd1bc/windows-clarke-qt-200.json) · [Registro Fedora](evidence/candidate-08cd1bc/fedora-updates.json) · [Aprobación](DECISION_LOG.md#cierre-e-integración-de-fase-04)

## Protocolo de escritorio real

Usar los portables de 2.2.1 Preview y registrar sistema operativo, SHA o huella del paquete, resolución física, escala del sistema y tema. En Windows verificar las escalas nativas de 150 % y 200 %. En Linux comprobar el flujo en Fedora Plasma con su escala nativa. Usar un usuario o perfil de prueba para validar el actualizador y preservar los datos de trabajo. [Paquetes 2.2.1](../../releases/v2.2.1.md) · [Huellas](evidence/candidate-08cd1bc/SHA256SUMS-2.2.1-CANDIDATE.txt)

1. Abrir **Enlace digital** desde el catálogo de Comunicaciones. Activar **Incluir cadena de canal** y añadir los preajustes **Multitrayecto** y **Fading Rician**, en ese orden. Conservar los valores iniciales e iniciar el enlace. En **Exportar → Experimento completo**, guardar el SLPROJ. Cerrar la pestaña desde la cruz y comprobar que el catálogo conserva su ancho y que los botones tienen margen respecto del borde.
2. Abrir el SLPROJ y usar **I/Q transmitida** como entrada de **Fading Rayleigh y Rician** para conservar sus 96 kHz. Ingresar `0 = 1` y `4 = 0.2, 4, pi/4` en líneas separadas. Elegir la trayectoria de diagnóstico `2`, la variación **Correlacionada · Clarke** y un Doppler máximo de `64` Hz. Aplicar y abrir **Distribuciones de envolvente y fase** y **Autocorrelación y PSD Doppler**. Cambiar de tema y revisar ejes, referencias, navegación y controles de la figura al reducir la ventana.
3. Comprobar que el experimento reabierto conserva ambos registros de etapa, la salida y el reloj de 96 kHz. En **Barrido**, usar una carpeta vacía y dos valores de Eb/N₀, `6` y `10` dB, con dos réplicas. Tras completar las cuatro corridas, reabrir el catálogo y verificar que se pueden reutilizar los resultados.
4. Registrar resultados y capturas de cada sistema, incluidos cortes, avisos, controles inaccesibles y pasos que necesiten ajuste. Identificar por separado las capturas simuladas y la evidencia del escritorio real.

En el registro de cada sesión, indicar el resultado del enlace y regreso al catálogo, de las dos figuras de Clarke y de la reapertura del barrido. Si algún paso queda interrumpido, anotar el último control usado y conservar el SLPROJ exportado o una captura que muestre el problema.
