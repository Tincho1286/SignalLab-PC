# Matriz de validación de Fase 03

## Consolidación de 02C

Un único despacho de Mathematical reliability, sobre `a5eafa9a1e98116e84b57d3bb0e8881ea02b2931`. La suite completa, los portables descartables, la auditoría de instaladores y la consolidación de CI aprobaron. Los recibos conservan las huellas SHA-256 de los informes, incluidos los inventarios y las pruebas de actualización. El informe de CI coincide con la verificación local. [Corrida e informes](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45812233593) · [Recibos](evidence/baseline-a5eafa9-receipt.json) · [Resultados](PHASE_03_BASELINE.md)

## Verificación inicial de comunicaciones

| Evidencia | Entorno y resultado |
| --- | --- |
| Referencias de pulsos | SciPy, 79 valores mediante cuadratura del espectro de RC o RRC. Incluye el límite exacto y puntos vecinos. |
| Etiquetas y energía | Reflexión Gray de 3 y 2 bits y suma de energía de 4, 16, 64 y 256-QAM. |
| BER coherente | Cinco valores de la integral de probabilidad antipodal. |
| Errores en QAM | Veinte combinaciones de orden y Eb/N0 mediante integrales gaussianas sobre regiones de decisión y distancia de Hamming para Gray. |
| Comparador externo | Komm 0.37.0, ejecutado aparte. Detecta discrepancias en puntos vecinos de polos de RRC. |

[Métodos y reproducción](MATHEMATICAL_AUDIT.md) · [Reglas para completar la validación](QUALITY_GATE_CRITERIA.md)

## Comprobación del escritorio Windows

Sobre `441f1c2`, se abrió Workbench en el escritorio Windows local de 1366 × 768, con 96 DPI informados por el sistema y Qt 6.12.0 del entorno de desarrollo. El procedimiento abrió el enlace, calculó y mostró el informe, abrió constelación y ojo como figuras separadas y navegó al barrido. Las escalas 1,5 y 2 se aplicaron en Qt sobre ese mismo escritorio. La matriz de empaquetado verifica aparte Qt 6.12.1.

| Escala de Qt | Área útil lógica | Vista observada |
| ---: | ---: | --- |
| 1 | 1 366 × 720 | Datos e informe en paralelo. Las figuras separadas abren con sus controles. |
| 1,5 | 911 × 480 | Vista compacta. El resultado se selecciona al calcular y conserva los ocho accesos a las figuras. |
| 2 | 683 × 360 | Altura inferior al mínimo lógico de 420 de Workbench. El ojo queda comprimido con los controles visibles. «Solo figura» recupera altura para las trazas y sus ejes. |

Las cinco pruebas de Workbench para comunicaciones también pasaron con el backend nativo de Windows. El acta distingue DPI nativo de escalas simuladas. La validación automatizada de comunicaciones en Linux se ejecuta offscreen. La matriz también captura herramientas históricas de Workbench sobre Xvfb. La prueba funcional del nuevo laboratorio en un escritorio Linux queda para la validación del propietario. [Acta con huellas de capturas](evidence/workbench-windows-441f1c2.json)

Para revisar ese recorrido en un escritorio, abrí **Comunicaciones digitales → Enlace digital**, ejecutá el perfil inicial, alterná constelación y ojo desde resultados y guardá una figura. Después abrí un barrido, variá Eb/N₀ y cancelá entre corridas. Al retomarlo, confirmá que reaparecen las corridas ya verificadas. Registrá resolución física, escala del sistema y versión del candidato.

## Matriz final del candidato

Los cinco trabajos de `45834151197` aprobaron en el primer intento para `441f1c2`. Windows y Ubuntu usaron CPython 3.14.10 y las dependencias fijadas. Ambas suites aprobaron 1 184 pruebas y 150 casos preventivos. Los equipos de distribución verificaron el runtime, los límites, la firma de ensayo, la actualización nativa e identificaron el conjunto exacto de archivos de distribución. Se comprobaron por separado los hashes de los ZIP y de sus miembros. [Ejecución](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45834151197) · [Quality Gate final](QUALITY_GATE_REPORT.md) · [Recibo de los cinco trabajos](evidence/candidate-441f1c2/matrix-receipt.json)
