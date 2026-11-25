# Matriz visual

| Pantalla | Configuración | Alcance |
| --- | --- | --- |
| Windows real, ventana 640 × 420 lógica | Escala del anfitrión | Inicio, búsqueda, DFT, resultado y gráfico inspeccionados |
| Windows Qt offscreen | 640 × 420, 1366 × 768 y 1920 × 1080 lógicos, factores 1 a 2 | Diez vistas generadas en la prueba local para seis combinaciones |
| Windows del candidato | Perfil CI y 960 × 540 a factor 2 adicional | Capturas del candidato |
| Linux del candidato | Xvfb con Qt xcb, mismas combinaciones | Capturas virtuales del candidato |
| Windows y Linux reales | Ajustes reales de 125 %, 150 % y 200 % | Actas pendientes |

Las vistas incluyen Inicio, DFT, IDFT, FIR, IIR, muestreo con resultado, cambio de tasa, PSD, Proyecto y CAS. Los casos de sesiones, tablas, diálogos, cancelación e I/O se ejercitan en las pruebas funcionales. Generar una captura no acredita por sí solo todos los controles de esa vista.
