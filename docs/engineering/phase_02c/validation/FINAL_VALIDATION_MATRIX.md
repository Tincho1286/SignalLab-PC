# Matriz final del candidato 459b9fc

La matriz vigente está en [Resultado de a80508c](#resultado-de-a80508c).

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
| `99f7ce2` | Publicación LTI sólo tras cálculo aceptado. 922 pruebas integrales y 150 casos preventivos por sistema. Ambos trabajos de distribución agotaron el límite de 420 s. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45686815857) · [Evaluación](evidence/quality-gate-99f7ce2.json) |
| `4f0f32d7e4d64e97b734fd5d30680efd3b4f553a` | Las dos suites y la distribución Linux terminaron. Windows alcanzó el límite de 540 s en la última prueba del verificador UI. El perfil Windows local también seguía avanzando cuando llegó al límite. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45687451296) |
| `7f1babd` | Importación transaccional con referencias preservadas y admisión compartida de lectura. Windows volvió a agotar el plazo fijo de interfaz. Se canceló el resto de la auditoría al quedar superada por el candidato posterior. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45689038376) |
| `eb50895250b124ec0554a4c52d894d5ac790e7a5` | Candidato vigente. El supervisor completó localmente 345 pruebas de escritorio en 583,8 s, con cero fallos, errores u omisiones. Los 150 casos preventivos pasaron en el mismo árbol funcional. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45689459348) · [Verificación local](evidence/windows-local-workflows-eb50895.json) |

La evidencia de cada corrida corresponde a su SHA. El portátil descartable del trabajo de línea base y el binario inventariado para distribución se construyen independientemente desde el mismo candidato. Las actas de Windows 96 DPI proceden de un escritorio real. Los perfiles Linux corresponden a Xvfb con escalas simuladas.

Cada evento de corrección generó su propia corrida porque cambió el SHA. «Re-run failed jobs» reutiliza el commit de origen y se reserva para un fallo transitorio. El flujo de portables ya permite elegir una sola plataforma en un despacho manual sin firma. El Quality Gate final conserva la matriz de ambos sistemas y coteja un único SHA. Los commits documentales posteriores se comparan contra el candidato por ruta y conservan sus resultados si el diff es exclusivamente documental. [Mecanismo de GitHub](https://docs.github.com/es/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)

El flujo matemático mantiene los controles de catálogo y análisis estático en cada push a `develop`. Los pushes nuevos cancelan comprobaciones automáticas sustituidas y las ejecuciones manuales usan un grupo de concurrencia propio. La matriz integral, el SBOM, los instaladores y el Quality Gate se ejecutan una sola vez por candidato mediante el parámetro manual `engineering_baseline=true` del mismo workflow. La primera corrida con el supervisor, 45689459348, se conserva para validar su candidato. Este ajuste sólo afecta el disparo de ejecuciones posteriores. [Reglas de concurrencia](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency)

## Resultado de eb50895

| Control | Windows x64 | Linux x86-64 |
| --- | --- | --- |
| Suite integral y preventiva, mismo SHA limpio | 925 + 150 aprobadas | 925 + 150 aprobadas |
| Supervisión del verificador gráfico | 345 aprobadas en 555,8 s | 345 aprobadas en 506,9 s |
| Diagnóstico congelado del portable | Aprobado, incluye CAS y SLPROJ | Aprobado, incluye CAS y SLPROJ |
| Instalador y actualización 2.0.0 → 2.0.1 | Aprobados con destino aislado y clave temporal | Aprobados con destino aislado y clave temporal |
| Inventario de binarios y SBOM | 219 archivos nativos | 389 archivos nativos y OpenSSL Ubuntu verificado |
| Banco y cancelación | 71 perfiles, 22 cancelaciones sin pérdida | 71 perfiles, 22 cancelaciones sin pérdida |
| Campaña científica | 48 proyectos, 170 MiB RSS, 10,64 s | 48 proyectos, 177 MiB RSS, 9,58 s |
| Mayor pausa del heartbeat con autoguardado | 13,08 ms | 10,86 ms |
| Quality Gate automático | 35 de 37 controles | 35 de 37 controles |

Los cuatro trabajos de plataforma y el informe automatizado aprobaron la ejecución. El resultado de cierre conserva las brechas globales aunque los trabajos hayan terminado bien. Se verificaron ambos instaladores con manifiesto de ensayo, rechazo de firma temporal desde el verificador de producción y descarga corrupta rechazada. La matriz se reprodujo con el mismo SHA y produjo el mismo JSON de evaluación. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45689459348) · [Índice](evidence/ci-eb50895.json)

El cambio de disparo en `d996f87` fue comprobado por la corrida automática de sólo tres trabajos. Aprobaron matemática Windows, matemática Linux y controles estáticos. Los motores, la suite, el entorno fijado y los scripts de construcción mantienen el árbol probado en la auditoría. [Corrida rápida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45691896234)

## Resultado de 623c9dd

La única matriz de continuación se despachó después de comprobar ambos objetivos de cobertura en Windows local. Cada etapa de las plataformas registra `623c9ddcc2460485b549e864fa86ddc6b7cba407`. Los informes de cobertura y compilación corresponden a ese candidato de auditoría 2.0.1. [Corrida 45739704501](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45739704501)

| Control | Windows 2022 | Ubuntu 22.04 |
| --- | --- | --- |
| Árbol y cobertura | SHA limpio, 88,38 % de líneas y 75,15 % de ramas | SHA limpio, 88,33 % de líneas y 75,18 % de ramas |
| Integral, preventivo | 1 108/1 109 y 150/150 | 1 109/1 109 y 150/150 |
| Portable y actualización 2.0.0 → 2.0.1 aislada | Aprobados | Aprobados |
| Inventario y SBOM | 219 archivos cotejados | 389 archivos cotejados. OpenSSL de Ubuntu 3.0.2-0ubuntu1.30 |
| Recursos y persistencia | 71 mediciones, 22 perfiles de cancelación, 48 corridas y 6 ensayos de recuperación | 71 mediciones, 22 perfiles de cancelación, 48 corridas y 6 ensayos de recuperación |
| Controles de Quality Gate | 36/37 | 37/37 |

El verificador ejecutó `tools/check_quality_gate_02c.py --require-automated` contra los artefactos de la corrida. Produjo el mismo JSON que GitHub y devolvió código 1 por el control integral de Windows. El caso de fondos falló al comparar el alias 8.3 con la ruta larga. `b6bcb85` corrige esa aserción y la regresión pasó en Windows local. `87b74ed` corrige el hallazgo posterior de figuras al maximizar y tiene evidencia local independiente. [Recibos de los cinco artefactos](evidence/ci-623c9dd.json) · [Quality Gate](QUALITY_GATE_REPORT.md#evaluación-del-candidato-623c9dd)

## Regresiones focalizadas en Windows sobre 8e274e7

El trabajo `desktop-regressions` aprobó 3/3 pruebas en Windows 2022 con CPython 3.14.10 y Qt offscreen. Incluye identidad de la carpeta gestionada, rechazo de contenido no raster y reapertura de una figura tras cambiar entre disposición compacta y amplia. El checkout registró `8e274e72bc0d5bbec1ca3766e2522def3214f3ce`, que contiene `b6bcb85` y `87b74ed`. El despacho omitió matemáticas, cobertura integral y distribución. La matriz integral sigue referida a `623c9dd`. [Log del trabajo](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45744295852/job/139656507132)

El push del mismo SHA también aprobó el flujo habitual de `develop`, con matemática en Windows y Ubuntu y el análisis estático. [Corrida rápida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45744279375)

## Distribución, recursos y almacenamiento de a80508c

Los trabajos de distribución de la corrida 45745729541 terminaron correctamente en Windows 2022 y Ubuntu 22.04. Los recibos se descargaron con verificación del digest publicado por GitHub. El salto aislado de 2.0.0 a 2.0.1 conservó la sesión y el destino, rechazó una descarga corrupta y ejecutó el diagnóstico del programa instalado. El verificador con la clave pública de producción rechazó el manifiesto firmado con la clave temporal del ensayo. [Recibo Windows](evidence/windows-installer-a80508c.json) · [Recibo Linux](evidence/linux-installer-a80508c.json) · [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45745729541)

| Control | Windows x64 | Linux x86-64 |
| --- | --- | --- |
| Verificador de interfaz del empaquetado | 347 pruebas en 321,18 s | 347 pruebas en 339,09 s |
| Diagnósticos del portable instalado | 15 aprobados | 15 aprobados |
| Archivos nativos cotejados con el SBOM | 219 | 389 |
| Perfiles de rendimiento y cancelaciones solicitadas | 71 y 22 | 71 y 22 |
| Mayor latencia observada de cancelación en esos perfiles | 47,98 ms | 55,72 ms |
| DFT con 1 048 576 muestras, mediana y pico de RSS | 59,62 ms y 178,49 MiB | 55,45 ms y 186,34 MiB |
| Guardar SLPROJ con 1 048 576 muestras por registro, mediana y tamaño | 192,62 ms y 33 555 971 bytes | 140,75 ms y 33 555 971 bytes |
| Campaña de 48 proyectos, duración y pico de RSS | 11,99 s y 169,52 MiB | 10,44 s y 177,23 MiB |
| Mayor pausa de interfaz durante la escritura SLPROJ en segundo plano | 10,69 ms | 10,63 ms |

La referencia `faef335` tenía 67 perfiles y 17 intentos de cancelación por plataforma. El mismo perfil DFT de 1 048 576 muestras medía 62,13 ms y 178,23 MiB de RSS en Windows y 77,17 ms y 187,43 MiB en Linux. Los tiempos corresponden a runners compartidos. Las 22 cancelaciones del candidato preservaron los destinos y la campaña verificó 288 registros, 75 497 472 muestras y 1 208 085 276 bytes. Se comprobó la reanudación desde el catálogo al cancelar la octava corrida. [Banco y alcance](../resources/OPERATIONAL_ENVELOPE.md) · [Dimensionamiento](../persistence/COMMUNICATIONS_STORAGE_SIZING.md)

## Resultado de a80508c

La corrida 45745729541 se despachó una vez en `develop` con `engineering_baseline=true` el 25/11/2026 a las 23:56, hora argentina. Terminó 25 min 34 s después. Los cuatro trabajos de plataforma y el verificador de CI aprobaron el mismo SHA `a80508c224d902ce225c6b6cc66fd090210c52b2`. Los dos informes de línea base lo registraron antes y después de la suite con las fuentes intactas. [Corrida y logs](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45745729541) · [Recibos](evidence/ci-a80508c.json)

| Control | Windows x64 | Linux x86-64 |
| --- | ---: | ---: |
| Pruebas integrales aprobadas, cero omisiones | 1 110 | 1 110 |
| Casos preventivos aprobados | 150 | 150 |
| Líneas globales | 37 993/42 982 (88,39 %) | 37 968/42 982 (88,33 %) |
| Ramas globales | 12 437/16 538 (75,20 %) | 12 434/16 538 (75,18 %) |
| Controles de umbral en componentes | 23/23 | 23/23 |
| Quality Gate automático | 37/37 | 37/37 |

En las dos suites pasaron `test_managed_copies_keep_source_and_clean_only_matching_old_files`, el rechazo de imágenes fuera de los formatos admitidos y `test_figure_launcher_keeps_calculated_views_after_switching_workspace_layout`. La auditoría integral verificó las familias de proyectos históricos, diagramas, Fourier, muestreo, archivo científico y CAS. Las actas Windows a 100 % y 125 % complementan los perfiles automatizados. [Windows](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45745729541/job/139661196421) · [Linux](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45745729541/job/139661196526) · [Acta](../gui/DESKTOP_CONTINUATION.md#acta-windows-del-candidato-a80508c)

Con los artefactos de plataforma descomprimidos en `work/phase02c-ci-a80508c`, la comprobación `python -B -X utf8 tools/check_quality_gate_02c.py --input work/phase02c-ci-a80508c --output work/phase02c-ci-a80508c/verified --candidate a80508c224d902ce225c6b6cc66fd090210c52b2 --require-automated` devolvió código 0. El contenido JSON coincidió con el informe de GitHub. El índice distingue las huellas de los artefactos y reportes originales de las copias versionadas con fin de línea normalizado. [Resultado automático](evidence/quality-gate-a80508c.json) · [Dictámenes](QUALITY_GATE_REPORT.md#evaluación-del-candidato-a80508c)

## Verificación de empaquetado E-01

En la única matriz integral de `2f1410c` con Qt 6.12.1 pasaron 1 110 pruebas y 150 casos preventivos por plataforma. Windows obtuvo 88,36 % de líneas y 75,18 % de ramas. Linux obtuvo 88,31 % y 75,16 %. El trabajo de empaquetado de Windows falló durante la compilación de AVIF. Linux completó la matriz de plataforma. [Matriz inicial](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45751459528)

La primera corrida focalizada compiló las bibliotecas de Pillow en Windows y detectó una ruta que pip interpretó como requisito remoto. Se canceló el resto de esa corrida cuando el commit con la corrección estuvo disponible. El despacho focalizado final utilizó la opción `native_packaging=true` y aprobó los portables e instaladores Windows y Linux del mismo `64dc3c4`. En ambos instaladores se verificaron la transición aislada desde 2.0.0, el destino, la preservación de la sesión y el rechazo de una descarga corrupta. [Caso de ruta Windows](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45752832083/job/139684425485) · [Auditoría final](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45753691354) · [Índice de evidencia](evidence/ci-e01-64dc3c4.json)
