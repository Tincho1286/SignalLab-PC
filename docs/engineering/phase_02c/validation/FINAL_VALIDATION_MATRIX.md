# Matriz final del candidato 459b9fc

La corrida 45650373957 terminó correctamente en 18 min 28 s. Los artefactos de líneas base, instaladores, inventarios y rendimiento corresponden a `459b9fc505c0a6a4d20bb6c5e898a5ae3f3cb281`. Se comprobó el SHA antes y después de la suite. [Corrida y artefactos](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45650373957) · [Evidencia estructurada](evidence/ci-459b9fc.json)

| Control | Windows x64 | Ubuntu x86-64 |
| --- | --- | --- |
| Suite integral y análisis estático | 870 pruebas, cero fallos, análisis aprobado | 870 pruebas, cero fallos, análisis aprobado |
| Oráculos preventivos | 150/150, dos semillas | 150/150, dos semillas |
| Procedencia, integración y compatibilidad histórica | Siete regresiones dedicadas y casos de proyecto, sesiones y CLI aprobados | Mismos contratos aprobados |
| Líneas y ramas globales | 78,09 % y 63,84 % | 78,06 % y 63,82 % |
| API y CLI sin Qt | Paridad DFT y flujo DSP aprobados | Paridad DFT y flujo DSP aprobados |
| Recursos | 57 perfiles y ocho cancelaciones de carga o escritura, además de DTFT y simbólico | Mismos perfiles y comprobaciones |
| Portables | Diagnóstico del ejecutable congelado aprobado | Diagnóstico del ejecutable congelado aprobado |
| Instalación y entrega descartable | Upgrade con fixtures, desinstalación, rechazo de downgrade y comprobación del candidato real | Instalación del candidato real, reparación, desinstalación, conservación de datos |
| SBOM y runtime | 219 archivos nativos, CPython 3.14.10 | 391 archivos y 42 enlaces, CPython 3.14.10, OpenSSL de Ubuntu verificado |
| Interfaz y DPI | Suite, capturas de siete perfiles y sesión interactiva Windows a 96 DPI | Suite y capturas de siete perfiles Xvfb inspeccionadas según alcance |
| Validación fuera del runner | DPI real adicional pendiente | Escritorio real y DPI del sistema pendientes |
| Entrega pública | Firma de producción y salto desde 2.0.0 pendientes | Salto desde 2.0.0 y canal real pendientes |

[Análisis de cobertura](../testing/FINAL_COVERAGE_REPORT.md) · [Escritorio y DPI](../gui/GUI_VISUAL_VALIDATION_MATRIX.md) · [Instalación Windows](evidence/windows-installer-459b9fc.json) · [Instalación Linux](evidence/linux-installer-459b9fc.json)

## Matriz de la continuidad

| Control en `faef335bb7892cda92edc50a7c4f417a89b0415c` | Windows x64 | Ubuntu x86-64 |
| --- | --- | --- |
| SHA limpio y suite | Mismo SHA antes/después, 890 pruebas | Mismo SHA antes/después, 890 pruebas |
| Preventivo | 150 casos, 2 semillas | 150 casos, 2 semillas |
| Portables | 14 diagnósticos aprobados | 14 diagnósticos aprobados |
| Distribución aislada | 2.0.0 → 2.0.1, preservación de sesión, descarga corrupta rechazada | Mismos controles, reparación y desinstalación Linux |
| SBOM | 219 archivos nativos con origen registrado | 391 archivos nativos y 42 enlaces |
| Runtime | CPython 3.14.10, OpenSSL 3.5.9 en el runtime de Python | CPython 3.14.10, libssl3 `3.0.2-0ubuntu1.30` del runner |
| Recursos | 67 perfiles y 17 intentos temporizados | 67 perfiles y 17 intentos temporizados |
| Interfaz | Siete perfiles automatizados y acta Windows 100 % en dos tamaños | Siete perfiles Xvfb. Escritorio real pendiente |

La clave usada para el ensayo fue efímera. El verificador de producción rechazó su firma y el manifiesto estable se comprobó con su clave pública. El salto usa los instaladores reales, sin cambiar el canal público. El adaptador de auditoría hace instalación silenciosa y evita esperar al propio proceso que ejecuta la prueba. El recibo acredita la transferencia, la sustitución en el mismo destino y la ejecución del binario instalado. En ambos builds el binding de cryptography declara OpenSSL 4.0.3 además del OpenSSL que carga Python.

El resumen conserva por separado los SHA-256 de los JSON originales de CI y los de los archivos versionados. Git normaliza los finales de línea en los JSON Windows.

[Corrida 45673548563](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45673548563) · [Datos y SHA de archivos](evidence/ci-faef335.json) · [Recibo Windows](evidence/windows-installer-faef335.json) · [Recibo Linux](evidence/linux-installer-faef335.json)

## Continuación autónoma

La corrida 45683218209 completó las dos suites y las dos auditorías de distribución sobre `54adaa088ee03430ba53f1068da8086756d3bc25`. Conserva 907 pruebas integrales, 150 preventivas, 71 perfiles de rendimiento y 8 perfiles de interfaz por plataforma. Pasaron la verificación congelada y la actualización aislada 2.0.0 → 2.0.1. La cobertura global siguió bajo el objetivo. En `0fc6d5a` ambas suites integrales se completaron, pero la distribución Linux agotó el plazo del verificador UI antes de construir y auditar su instalador.

| SHA | Corrida y objeto de validación |
| --- | --- |
| `faef335` | Referencia de la instrucción. 890 pruebas y 150 casos preventivos por plataforma. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45673548563) |
| `54adaa0` | Coinciden SHA, cobertura y artefactos por sistema. El informe identifica 32/36 controles automáticos aprobados y detalla cuatro brechas. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45683218209) · [Índice](evidence/ci-54adaa0.json) |
| `0fc6d5a` | Regresión de foco CAS y diagnóstico congelado. Linux interrumpió el verificador UI a 420,115 s. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45684469040) |
| `3a68618` | Cancelación de JSON y aislamiento entre generaciones de recuperación. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45685956523) |
| `99f7ce2` | Publicación LTI sólo después de cálculo aceptado. Perfiles adicionales de cancelación de lectura. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45686815857) |
| `4f0f32d7e4d64e97b734fd5d30680efd3b4f553a` | Renueva el presupuesto CI de interfaz a 540 s. En el perfil Windows local se agotó mientras la suite seguía avanzando. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45687451296) |
| `7f1babd` | Importación transaccional con referencias preservadas y admisión compartida de lectura. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45689038376) |
| `eb50895250b124ec0554a4c52d894d5ac790e7a5` | Candidato vigente. Supervisor de CI con progreso por prueba y plazo máximo de 960 s. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45689459348) |

La evidencia de cada corrida corresponde a su SHA. El portátil descartable del trabajo de línea base y el binario inventariado para distribución se construyen independientemente desde el mismo candidato. Las actas de Windows 96 DPI proceden de un escritorio real. Los perfiles Linux corresponden a Xvfb con escalas simuladas.

Cada evento de corrección generó su propia corrida porque cambió el SHA. «Re-run failed jobs» reutiliza el commit de origen y se reserva para un fallo transitorio. Durante el desarrollo de la corrección se deben ejecutar primero los casos afectados. Para entregar el Quality Gate final se ejecuta la matriz existente una vez por candidato estable de auditoría y se coteja un único SHA en los dos sistemas. [Mecanismo de GitHub](https://docs.github.com/es/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)
