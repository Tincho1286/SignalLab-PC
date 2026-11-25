# Línea base de estabilización

La Fase 01 se apoya en revisiones identificables y pruebas con el perfil Qt offscreen. Los resultados siguientes corresponden a estados diferentes del repositorio.

| Estado | Identidad | Evidencia |
| --- | --- | --- |
| Referencia inicial | `16ffcbaee8356e41de6ed1e5e3410b607afe480f` | 367 archivos Python en la guarda estática. Cobertura de líneas 77,95 % en un archivo de fuentes. 785 pruebas pasaron. La prueba de procedencia que llama a Git no tuvo acceso a `.git`. [Auditoría inicial](AUDIT_REPORT.md) |
| Rediseño local de la auditoría | Árbol de trabajo medido el 24 de noviembre, con cambios locales sobre la referencia inicial | 791 pruebas de la suite, 293 casos del control matemático y 150 casos del barrido. La guardia detectó la importación que faltaba en el manejo de errores de filtros. [Auditoría inicial](AUDIT_REPORT.md) |
| Primera estable 2.0.0 | `adfad5c093a236b0565f00f5e97845acf040ec96` | Jobs nativos de distribución e instaladores en ambos sistemas y manifiesto firmado. Versiones reales CPython 3.12.10 y Qt 6.10.0. [Ejecución de la estable](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45534937561) |
| Candidato de estabilización | `1aac7930c503fee33acf6ac65a611ab7822fd2ff` | Referencia limpia de código, pruebas y herramientas. Qt Essentials 6.12.0 y CPython 3.12.10. [Matriz Windows/Linux](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45544630297) |

## Reproducción de la referencia inicial

Usar un checkout limpio del SHA del candidato. Los jobs de referencia usan Windows Server 2022 y Ubuntu 22.04 x86-64. Instalar GL y el runtime gráfico offscreen en Linux como declara el workflow. Python 3.12.10 en ambos sistemas.

```sh
python -m pip install -r requirements-lock.txt -r requirements-quality.txt -r requirements-engineering.txt
python -B -X utf8 tools/check_engineering_baseline.py --output work/engineering-baseline
python -B -X utf8 tools/check_engineering_package.py --output work/engineering-baseline/packaged-smoke.json
python -B tools/audit_dependencies.py --report work/import-graph.json --dot work/import-graph.dot
```

El directorio de salida de la primera comprobación tiene que ser nuevo. Guarda el SHA antes y después, perfil, versiones instaladas, códigos de salida y resultados de línea y rama. La suite integral descubre todos los tests, exige cobertura por familia y repite el barrido matemático preventivo. Las semillas se conservan con el reporte integral. La construcción descartable ejecuta el diagnóstico del ejecutable y registra su SHA-256, CPython y Qt. Se guardan únicamente informes y logs.

El diagnóstico offscreen comprueba cálculo y controles reales sin interacción manual con el escritorio. Instalación, escalado de pantalla y experiencia de usuario en la edición candidata se registran aparte.

## Estado de los controles

La corrección DFT/DTFT, las regresiones de sesiones históricas y el control de lectura MATLAB pasaron comprobaciones dirigidas locales. Sobre `e6d0ebc`, Windows pasó 297 pruebas del gate de matemática, 150 casos preventivos y la guarda estática de 375 archivos. Sobre el mismo árbol de aplicación con el ajuste de empaquetado en `7e18467`, el portable descartable Windows pasó 13 comprobaciones. La inspección del archivo confirmó que contiene Qt 6.12.0 y Qt SVG. [Evidencia local](evidence/windows-local-checks.json)

La primera corrida integral, sobre `327a62c`, encontró que una prueba del menú de figuras comprobaba el resultado antes del evento de selección. Qt 6.12 abre el menú sin bloquear la llamada de prueba que simula el clic. La corrección sincroniza la prueba con la señal de la acción y comprueba que se abra la figura elegida. La misma corrida terminó con una excepción nativa en Windows bajo cobertura. El caso de DTFT cercano al cierre pasó aislado. El diagnóstico de la matriz siguiente registra el test activo y habilita `faulthandler`. [Corrida inicial](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45542153305)

Una corrida posterior sobre `e6d0ebc` completó 797 pruebas y 150 casos preventivos en cada plataforma. El único fallo de la suite en ambos casos fue la comprobación temprana del menú de figuras. No reapareció la excepción nativa de Windows. El empaquetado de esa corrida usaba una ruta de recursos relativa al archivo de configuración temporal. Se corrigió y se verificó con el smoke local Windows. [Resumen de la matriz intermedia](evidence/intermediate-matrix-e6d0ebc.json)

| Control en `1aac793` | Windows Server 2022 x64 | Ubuntu 22.04 x86-64 |
| --- | ---: | ---: |
| Guarda estática | 375 archivos aprobados | 375 archivos aprobados |
| Suite integral | 797/797 | 797/797 |
| Casos preventivos con dos semillas | 150/150 | 150/150 |
| Diagnóstico del portable descartable | 13/13 | 13/13 |
| Cobertura global de líneas | 77,27 % | 77,25 % |
| Cobertura global de ramas | 63,90 % | 63,87 % |
| Trazas con ejecución del worker simbólico | 122 | 122 |
| Runtime del portable descartable | CPython 3.12.10 y Qt 6.12.0 | CPython 3.12.10 y Qt 6.12.0 |

Los dos jobs verificaron el SHA antes y después de ejecutar la suite. Las huellas de código, pruebas y herramientas coincidieron. Una ejecución local de Windows sobre el mismo código pasó 797 pruebas y 150 casos preventivos sin instrumentación. La excepción nativa inicial no reapareció en la matriz final. [Evidencias de la referencia](evidence/final-matrix-1aac793.json) · [Matriz de validación](VALIDATION_MATRIX.md)

## Dictamen de la primera referencia

**NO-GO para iniciar Engineering Core.** La referencia matemática, de sesiones y de portables de prueba está verificada en ambos sistemas. Sigue abierto el mantenimiento de seguridad del runtime, la cobertura está por debajo de los objetivos globales y por motor, y falta ampliar las pruebas de compatibilidad y de recursos. El piloto DFT queda documentado para revisión y la Fase 02 requiere autorización específica. [Estado del proyecto](PROJECT_STATE.md) · [Seguridad](SECURITY_BASELINE.md) · [ADR 001](ADR-001-DFT-PILOT.md)

## Segunda referencia de la Fase 01

La referencia de `develop` es `ccb6a861aa836c5ddd455306a9e6ec7177881a82`. Fija CPython 3.14.10 para el desarrollo, la matriz y la construcción. Para repetir los comandos de la referencia inicial se usa la versión de `.python-version` del SHA que se está midiendo. Las dependencias del lock se instalan por wheel, con validación de `pip check`. El diagnóstico comprueba el CPython real del portable y registra los runtimes de TLS y XML. [Matriz de GitHub Actions](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45613503980)

Se agregaron 17 pruebas matemáticas independientes a la suite integral y al gate de matemática. Cubren alias firmado y borde de Nyquist, fase inicial, reloj y reconstrucción, conversión racional, cuantización y punto fijo, series continuas, impulsos, CTFT inversa, PSD por Welch y energía en frecuencia. Detectaron dos defectos reproducibles. El cuantizador podía elegir el nivel superior para una muestra inmediatamente inferior al punto medio, incluida la pérdida de precisión con extremos muy dispares. La integración de energía podía desbordar en el cuadrado o en la suma antes de aplicar su factor de escala. Ambas correcciones conservan los oráculos en `tests/test_math_sampling_fourier.py`. El gate local Windows de la primera actualización a 3.14 pasó 314 pruebas y el barrido de 150 casos. La matriz de `develop` cubre también la comparación compensada de puntos medios.

| Control en `ccb6a86` | Windows Server 2022 x64 | Ubuntu 22.04 x86-64 |
| --- | ---: | ---: |
| Guarda estática | 375 archivos aprobados | 375 archivos aprobados |
| Suite integral | 814/814 | 814/814 |
| Casos preventivos con dos semillas | 150/150 | 150/150 |
| Diagnóstico del portable descartable | 13/13 | 13/13 |
| CPython del ejecutable | 3.14.10 | 3.14.10 |
| Cobertura de líneas de Muestreo | 92,11 % | 92,11 % |
| Cobertura de líneas de Fourier | 91,44 % | 91,44 % |

Las huellas de fuente, pruebas y herramientas coincidieron entre los dos sistemas. En Windows también se verificó que el script de desarrollo migre un entorno 3.12 a 3.14, conserve un respaldo utilizable y deje las dependencias instaladas sin conflictos. `main` contiene la versión estable 2.0.0. El candidato y sus verificaciones quedan en `develop`. [Evidencia del candidato](evidence/cpython-31410-ccb6a86.json) · [Cobertura](COVERAGE_REPORT.md)

## Referencia de cierre de Fase 01

El candidato `853bd67f7005e893ea6ddaeb37122a764e10b2ea` amplía la compatibilidad de proyectos y pruebas científicas y registra los controles de distribución sobre Windows Server 2022 y Ubuntu 22.04. El informe de cierre conserva las mediciones, el SBOM y las excepciones que afectan a una futura entrega. [Informe de cierre](PHASE_01_CLOSEOUT.md)
