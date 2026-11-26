# Trazabilidad de Fase 03

| Requisito | Paquete | Evidencia de implementación | Verificación del candidato |
| --- | --- | --- | --- |
| DC-01 | WP-01 y WP-02 | Contratos de bits, símbolos y reloj implementados y probados en Python. | Comparación de muestras, reloj y procedencia desde Workbench, Python y CLI. |
| DC-02 | WP-02 | Geometrías y energía independientes, etiquetas por reflexión y decisión verificada por búsqueda exhaustiva. | Datos de ida y vuelta y reutilización de etiquetas en Workbench, Python y CLI. |
| DC-03 | WP-03 | Cuadratura RC/RRC, DTFT y convolución independiente. Se verificaron energía, retardo y truncamiento en Python. | Medición FIR y contraste tras el filtro adaptado en Windows y Linux. |
| DC-04 | WP-04 | AWGN por tres referencias. Varianzas contrastadas con χ², retardo y fase con ventanas independientes, recuperación sin ruido y estado ambiguo. | Paridad de interfaces y contraste de la cadena completa con 32 réplicas. |
| DC-05 | WP-05 | Conteo alineado, EVM, referencias exactas y aproximadas verificadas con oráculos. Cinco perfiles Monte Carlo con detención por tamaño y cotas estadísticas. | Informes y figuras desde los resultados. Incertidumbre condicionada al modelo de dependencia. |
| DC-06 y DC-07 | WP-06 | Paridad de muestras y métricas de Workbench, Python y CLI sin Qt. Ocho figuras, informes, ayuda y traspaso de resultados verificados. Curvas BER, SER y EVM para comparaciones. | Arranque empaquetado y exportación de figura, escritorio Windows y comprobaciones automatizadas Linux. |
| DC-08 y DC-09 | WP-07 | Experimento atómico con bits, etiquetas, I/Q e informe en JSON y SLPROJ, con huellas al reabrir e incorporar. Catálogo de barridos, reanudación tras cancelar antes del guardado del índice y exportación CSV. | Banco de 8 corridas reabiertas por sistema, ensayos de cancelación y compatibilidad, intercambio SLBIN. |
| DC-10 | WP-00 y WP-08 | Criterios de cobertura, reglas científicas y matriz de arranque. | Un mismo SHA verificado en Windows y Ubuntu, 1 184 pruebas más 150 casos preventivos por sistema, paquetes y procedencia comprobados. |

[Criterios por requisito](PHASE_03_REQUIREMENTS.md) · [Oráculos](MATHEMATICAL_AUDIT.md) · [Matriz y dictámenes](QUALITY_GATE_REPORT.md)
