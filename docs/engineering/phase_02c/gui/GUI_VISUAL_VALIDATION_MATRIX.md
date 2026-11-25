# Matriz visual

| Pantalla | Configuración | Alcance |
| --- | --- | --- |
| Windows real, pantalla física 1366 × 768 a 100 % y ventana compacta | 96 DPI, backend windows | Inicio, búsqueda, DFT, resultado, gráfico, Proyecto y cuadro de guardado inspeccionados |
| Windows con backend nativo y escalas Qt simuladas | Siete perfiles, factores 1 a 2 | 70 capturas. Se inspeccionaron FIR a tamaño de escritorio, PSD compacto y conversión de tasa con factor 2 |
| Windows Qt offscreen | Geometría de widget y tamaños | Se observaron glifos sustitutos. La legibilidad se evaluó con el backend nativo |
| Windows del candidato | Perfil CI y 960 × 540 a factor 2 adicional | Capturas del candidato |
| Linux del candidato | Xvfb con Qt xcb, mismas combinaciones | Capturas virtuales del candidato |
| Windows y Linux reales | Ajustes reales de 125 %, 150 % y 200 % | Actas pendientes |

Las vistas incluyen Inicio, DFT, IDFT, FIR, IIR, muestreo con resultado, cambio de tasa, PSD, Proyecto y CAS. Se generaron 70 capturas Windows CI y 70 capturas Linux Xvfb para el candidato. En el perfil Linux de 640 × 420 el botón de PSD queda accesible y su etiqueta larga se corta al final. La observación queda registrada para la prueba de escritorio real. Los casos de sesiones, tablas, diálogos, cancelación e I/O se ejercitan en las pruebas funcionales. Generar una captura no acredita por sí solo todos los controles de esa vista. [FIR Windows](../validation/evidence/windows-fir-1366.png) · [PSD Windows](../validation/evidence/windows-psd-compact.png) · [FIR Linux](../validation/evidence/linux-xvfb-fir-1366.png) · [PSD Linux](../validation/evidence/linux-xvfb-psd-compact.png)
