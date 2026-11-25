# Validación integral de Fase 02B

## Criterio previo de WP-02B.07

El candidato debe estar limpio, coincidir antes y después de la ejecución, declarar la misma huella de código y pasar suite, barrido preventivo, recursos, persistencia, casos históricos, headless, GUI, CLI, guarda estática y distribución descartable en Windows y Ubuntu. Los datos del benchmark anterior indican su SHA separado. Los objetivos de cobertura son 85 % global, 90 % en Muestreo y 90 % en Fourier.

La matriz final arrancó sobre `8ad3066a2f91f8758c32ab422cd63d6868dec5df`. [Corrida final](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45638606172)

La prueba local de dependencias inspeccionó imports directos de diez módulos de núcleo y CLI. El subgrafo resultante es acíclico. Se cargó el ejemplo y el proceso quedó sin PySide, PyQt, shiboken ni qtpy. Las pruebas de consola bloquean activamente esos imports. La comprobación local adicional confirmó el retardo de grupo de 15 muestras para un FIR simétrico de longitud 31 en su banda de paso.

## Resultados del candidato

| Control | Windows Server 2022 x64 | Ubuntu 22.04 x86-64 |
| --- | ---: | ---: |
| Suite integral | 850/850 | 850/850 |
| Barrido preventivo | 150/150 | 150/150 |
| Casos nuevos de Fase 02B | 21/21 | 21/21 |
| Reutilización entre herramientas y GUI | 318/318 | 318/318 |
| Diagnóstico del portable | 13/13 | 13/13 |
| Instalación y entrega descartable | Aprobado | Aprobado |
| Guarda estática | 385 archivos | 385 archivos |

Las comprobaciones integrales registraron el mismo SHA al comienzo y al final, y las huellas de fuente, pruebas y herramientas coincidieron. No se registraron errores, casos omitidos ni fallos. Los portables cargaron CPython 3.14.10. El inventario registró 219 binarios de Windows y 391 de Linux. La revisión de OpenSSL de Ubuntu se comprobó por SHA-256 para `libssl.so.3` y `libcrypto.so.3`. La entrega de prueba usó instaladores reales y manifiesto descartable. Se preservan las limitaciones de la validación de entrega pública y DPI real. [Evidencia consolidada](phase02b-ci-8ad3066.json)
