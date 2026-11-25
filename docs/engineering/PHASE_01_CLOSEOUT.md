# Cierre de Fase 01 de SignalLab Engineering

**Fecha de revisión** 25 de noviembre de 2026.

La referencia recibida es el informe de `84e6339`, con las evidencias de `ccb6a86`. Para el cierre se ampliaron las pruebas científicas y de compatibilidad, se construyeron instaladores descartables y se añadieron comprobaciones de recursos y de procedencia de bibliotecas nativas. Los controles se ejecutan en `develop`, mientras que `main` contiene la versión pública 2.0.0. El trabajo se limita a Fase 01.

**Candidato de cierre** `853bd67f7005e893ea6ddaeb37122a764e10b2ea` en Windows Server 2022 x64 y Ubuntu 22.04 x86-64. La ejecución de GitHub conserva únicamente evidencia de auditoría. [Matriz del candidato](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45622588882)

**Dictamen** cierre de la línea base de Fase 01 con excepciones documentadas. El candidato constituye una referencia reproducible de estabilización. La evaluación de Qt 6.12.1, la validación de DPI del sistema y la actualización por el canal público quedan pendientes para una futura entrega. La autorización de Engineering Core se evalúa por separado.

## Dependencias nativas

El inventario cubre 219 archivos PE en Windows y 391 archivos ELF en Linux. Registra además 42 enlaces simbólicos de Linux con sus destinos. Cada archivo tiene una huella SHA-256 del miembro extraído del portable. La atribución compara esa huella con archivos de ruedas, del runtime de CPython o de paquetes Ubuntu. El inventario alcanza los componentes distribuidos como archivos. El código compilado dentro de cada archivo y las bibliotecas que aporta el anfitrión pueden requerir información adicional del proveedor.

Se acreditó el origen de los 610 archivos nativos. En la primera salida faltaba encontrar 55 extensiones Linux de CPython porque `platstdlib` apuntaba al entorno virtual. Sus 55 huellas coincidieron con el archivo oficial de CPython 3.14.10 para Ubuntu 22.04 x64, cuya huella de publicación también se verificó. Se incorporó `DESTSHARED` a la búsqueda para usar el directorio del intérprete en futuras corridas. El complemento de procedencia analiza el inventario del mismo portable, con el mismo hash del artefacto. [SBOM Windows](evidence/native-windows-853bd67.cdx.json) · [SBOM Linux](evidence/native-linux-853bd67.cdx.json) · [Correspondencias con el archivo de CPython](evidence/native-linux-cpython-853bd67.json)

| Runtime comprobado | Windows x64 | Ubuntu x86-64 |
| --- | --- | --- |
| CPython en el binario instalado | 3.14.10 | 3.14.10 |
| Expat cargado por CPython | 2.9.0 | 2.9.0 |
| QtCore empaquetado | 6.12.0 | 6.12.0 |
| OpenSSL de Python | 3.5.9 | `libssl3:amd64 3.0.2-0ubuntu1.30` |
| OpenSSL del módulo nativo de `cryptography 50.0.2` | 4.0.3 | 4.0.3 |

En Linux, `ssl.OPENSSL_VERSION` comunica 3.0.2. Las huellas de `libssl.so.3` y `libcrypto.so.3` coinciden byte por byte con las de la revisión corregida por Ubuntu. Para OpenSSL de `cryptography` se midió la versión con el módulo nativo de la rueda cuyo SHA-256 coincide con el del miembro distribuido. [Aviso USN-8847-1](https://ubuntu.com/security/notices/USN-8847-1)

Al 25 de noviembre, Qt 6.12.1 estaba publicado como Qt. Los índices de PyPI de `PySide6-Essentials` y `shiboken6` para esa versión respondían 404. El candidato conserva 6.12.0. La actualización queda pendiente de que estén disponibles ambas ruedas compatibles por plataforma. Qt 6.12.1 corrige CVE-2026-105924. La revisión de SignalLab no encontró uso directo de la conversión de CBOR a JSON que describe el aviso. [Publicación de Qt 6.12.1](https://www.qt.io/blog/qt-6.12.1-released) · [Historial de Essentials](https://pypi.org/project/PySide6-Essentials/#history) · [Historial de shiboken6](https://pypi.org/project/shiboken6/#history) · [Aviso de Qt](https://www.qt.io/blog/security-advisory-cve-2026-105924)

## Compatibilidad y exactitud

La ampliación contiene siete pruebas con comprobaciones independientes. Incluye proyectos de los esquemas 1 y 2, los tres formatos de diagramas, una hoja CAS con reutilización de un resultado publicado, estabilidad según la ROC y la respuesta en frecuencia de sistemas con avance. Comprueba además la diferencia entre un hueco aislado integrable y un intervalo incompleto para la transformada inversa, incluido el caso en el que una delta concentra masa en el punto omitido.

El proyecto v2 y los tres diagramas se generaron con los escritores de 2.0.0. El proyecto v1 se reconstruyó a partir del formato admitido y sirve para comprobar reloj heredado y procedencia. La fusión inválida se rechaza de forma transaccional y la fusión válida reasigna identificadores conservando relaciones. El CAS conserva el resultado publicado en la biblioteca y permite operarlo en otra hoja. La hoja activa, los borradores y el estado de las variables locales del CAS quedan fuera de la persistencia de sesión. [Contratos y archivos de prueba](SESSION_COMPATIBILITY.md)

La suite integral pasó **821 de 821 pruebas** y **150 de 150 casos preventivos** en cada sistema. La guarda estática pasó en 375 archivos. La cobertura de líneas fue de **77,56 % en Windows** y **77,53 % en Ubuntu**, con 63,39 % y 63,36 % de ramas. Las siete pruebas ampliaron el alcance con oráculos y contratos de reutilización. Sobre el mismo denominador de 40.980 líneas se ejecutaron 11 líneas adicionales en Windows y 9 en Ubuntu respecto de `ccb6a86`.

Muestreo alcanzó 92,11 % de líneas y Fourier 91,44 %, por encima del 90 % orientativo. La excepción global frente al objetivo de 85 % se justifica para la línea base por el alcance de los controles científicos, de compatibilidad y de distribución. Quedan unas 3.050 líneas para alcanzar ese objetivo. Entre las brechas mayores están `toolbox.py`, los paneles docentes, `ui.py`, el escritorio y el editor de polos y ceros. Conservarlas en el denominador hace visibles los casos pendientes. La excepción conserva el 85 % como objetivo orientativo y el seguimiento de rutas reales de interacción. [Medición y brechas](COVERAGE_REPORT.md) · [Evidencia de cobertura](evidence/phase-01-coverage-853bd67.json)

## Revisión visual y de interacción

Se usó un perfil descartable en Windows. A 640 × 480 lógicos y 100 % se comprobó la navegación desde Inicio hasta Muestreo, el acceso a los campos mediante desplazamiento y la ejecución de un cálculo de 101 muestras. La acción «Abrir gráfico» abrió la figura con dos ejes y marcas discretas visibles. En una ventana de 800 × 450 lógicos y escala Qt de 150 %, el CAS permitió escribir y evaluar `diff((x+1)^3,x)`. El resultado `3(x+1)²` se pudo leer en la hoja con la potencia visible y las acciones de resultado accesibles.

La matriz de capturas usa cuatro perfiles lógicos, 640 × 480 al 100 %, 800 × 600 al 125 %, 960 × 640 al 150 % y 1280 × 800 al 100 %. Cada perfil registra el backend de Qt, las dimensiones efectivas y el factor de escala. La escala se aplica al proceso Qt y aproxima el efecto del DPI. Cambiar la escala del monitor y mover ventanas entre pantallas con DPI distintos requieren una prueba de escritorio adicional. La revisión se limita a Inicio, Muestreo y CAS. Se mantiene abierto el control visual de los editores especiales y de ventanas de figuras en escritorios de menor tamaño.

La primera corrida agotó el plazo del control de reutilización en los dos sistemas antes de construir los portables. Los tiempos aumentaban a lo largo de las pruebas de sesiones. Se hizo explícita en su limpieza la entrega de los eventos `DeferredDelete` que `processEvents()` deja en cola al ejecutar sin un bucle de aplicación. El plazo se mantuvo en 420 s. También se corrigió el cierre de las capturas para que el diálogo de guardado de una sesión descartable no detuviera la matriz visual. [Primera corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45620549961) · [Documentación de Qt sobre eventos diferidos](https://doc.qt.io/qt-6/qcoreapplication.html#processEvents)

Se revisaron las 12 capturas de cada sistema. Los cuatro perfiles de Linux usaron el backend `xcb` en Xvfb. En las vistas compactas se conservaron los botones principales y la zona de desplazamiento. En las vistas de 1280 × 800 se dispusieron los datos y los resultados en dos columnas. Las capturas de Linux se inspeccionaron visualmente. La interacción manual se hizo en Windows y el DPI real del monitor se mantuvo fijo.

## Recursos y cancelación

Cada caso se ejecutó una vez en un proceso nuevo con un hilo para BLAS y OpenMP. El tiempo mide el cálculo después de importar módulos y preparar la señal. El pico residente incluye el entorno Python y la entrada. La memoria libre antes de los casos fue de 13,2–13,3 GiB en Windows y de 10,9 GiB en Ubuntu.

| Cálculo | Muestras | Windows · ms / MiB pico | Ubuntu · ms / MiB pico |
| --- | ---: | ---: | ---: |
| DFT | 16.384 | 2,44 / 97,6 | 3,10 / 107,2 |
| DFT | 262.144 | 10,36 / 113,3 | 13,55 / 121,8 |
| DTFT en 1.025 frecuencias | 1.024 | 52,77 / 101,9 | 46,46 / 111,9 |
| DTFT en 1.025 frecuencias | 8.192 | 383,48 / 107,0 | 269,06 / 118,1 |
| Cambio de tasa 2/3 | 16.384 | 3,62 / 97,2 | 5,11 / 106,5 |
| Cambio de tasa 2/3 | 262.144 | 11,30 / 107,1 | 24,43 / 116,2 |

Con una memoria libre simulada de 102.400 bytes, el 35 % admite 560 muestras complejas en cuatro arreglos vivos y rechaza 561. La cancelación de DTFT se solicitó al informar el primer avance y se observó en 0,021 ms en Windows y 0,025 ms en Ubuntu. La del proceso simbólico se solicitó 150 ms después del lanzamiento y concluyó 63,93 ms y 53,53 ms más tarde, respectivamente. En ambos casos simbólicos se verificó el cierre del proceso y la eliminación de su directorio temporal.

Las mediciones caracterizan tres operaciones con dos tamaños de entrada por operación y dos rutas de cancelación. El 35 % es una estimación previa donde se aplica la guarda. Los cálculos nativos pueden ocupar memoria adicional y atender la cancelación al alcanzar el próximo punto de control. Sigue pendiente un plazo común y una cota de memoria impuesta por el sistema para trabajos simbólicos o concurrentes. [Resultados de medición](evidence/phase-01-distribution-853bd67.json) · [Línea base de seguridad](SECURITY_BASELINE.md)

## Alcance del actualizador

La verificación del candidato construye el portable y el instalador con los scripts de distribución. La prueba usa un manifiesto firmado con una clave Ed25519 descartable y confirma que la clave pública de producción rechaza esa firma. El actualizador valida versión, origen permitido, longitud y SHA-256 antes de entregar los bytes del instalador real a la prueba nativa. La respuesta del transporte proviene de un archivo local. La firma de datos de la prueba, la confianza HTTPS de producción, Authenticode y la publicación son controles distintos.

Windows aprobó el registro por usuario, la actualización de prueba sobre la instalación, el rechazo de una versión anterior, la desinstalación y el diagnóstico de la aplicación instalada. Ubuntu aprobó la instalación con el `.run` real, la reparación en sitio, la desinstalación y la preservación de los archivos del usuario. Pasaron los 13 controles del ejecutable instalado y las 316 pruebas de reutilización entre herramientas en cada sistema. Las migraciones entre versiones se comprobaron con paquetes de prueba. Una actualización remota desde la edición pública anterior hacia este candidato requeriría un manifiesto de distribución auténtico y una entrega autorizada. [Evidencia de los instaladores y sus hashes](evidence/phase-01-distribution-853bd67.json)

## Seguimiento de riesgos

| Riesgo residual | Prioridad | Criterio de seguimiento |
| --- | --- | --- |
| Qt 6.12.0 frente a avisos posteriores | Alta | Repetir inventario y pruebas en las ruedas Windows/Linux de Essentials y shiboken6 de 6.12.1 cuando estén disponibles. El código de la aplicación no mostró una ruta directa para convertir CBOR a JSON. |
| Bibliotecas incorporadas estáticamente dentro de ruedas y bibliotecas provistas por el sistema anfitrión | Media | Identificar esas capas mediante inventarios del proveedor y revisión por plataforma. El hash identifica el archivo distribuido y ayuda a revisar avisos contra su origen. |
| Memoria, plazos y cancelación bajo cargas de trabajo distintas | Alta | Ampliar la caracterización a cargas simultáneas, análisis simbólico de larga duración y lotes de importación. Documentar un criterio de plazo y memoria para cálculos nativos y sus puntos de cancelación. |
| Persistencia completa de las hojas CAS | Media | Tratar la recuperación de variables locales, historial y borradores como un contrato distinto de la reutilización de resultados. |
| DPI del sistema y escritorios Linux | Media | Probar con una sesión de escritorio en X11 o Wayland y monitores con DPI distintos. Incluir el editor de diagramas, figuras independientes y cambio de monitor. |
| Actualización de extremo a extremo y confianza de Windows | Alta antes de publicar | Probar la migración desde un instalador anterior con una entrega autorizada, y revisar origen, confianza del sistema y arranque de la aplicación bajo esa política. |

Engineering Core, incluido el piloto de extracción de DFT, queda sujeto a autorización específica. [ADR 001](ADR-001-DFT-PILOT.md)

## Reproducción

Ejecutar desde una copia limpia del SHA validado. La matriz instala los archivos de requisitos fijados con el CPython de `.python-version`. En el control de Linux se usa Ubuntu 22.04 x86-64 con el paquete `libssl3` actualizado y un servidor Xvfb para las capturas.

```sh
python -B tools/check_engineering_baseline.py --output work/engineering-baseline
python -B tools/check_resource_limits.py --output work/distribution-audit/resources.json
python -B tools/native_sbom.py outputs/SignalLab-PC-2.0.0-linux-x86_64.tar.gz --output work/distribution-audit
python -B tools/capture_candidate_ui.py --output work/distribution-audit/ui
```

En Windows, el inventario recibe `outputs/SignalLab-PC-2.0.0.exe`. La comprobación de actualización se ejecuta con el instalador recién construido y, en Windows, con la ruta a Inno Setup. En Linux la captura necesita un servidor X11. La revisión documentada usó `xvfb-run -a -s '-screen 0 1920x1080x24'`. [Definición de la matriz](../../.github/workflows/mathematics.yml)
