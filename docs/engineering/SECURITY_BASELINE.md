# Línea base de seguridad

Revisión del 25 de noviembre de 2026. La distribución pública evaluada es la 2.0.0, producida desde `adfad5c093a236b0565f00f5e97845acf040ec96`. La rama de estabilización tiene un entorno distinto.

## Inventario de la distribución pública

| Portable x86-64 | CPython | QtCore | Qt SVG |
| --- | --- | --- | --- |
| Windows EXE | 3.12.10 · `python312.dll` | 6.10.0 · `Qt6Core.dll` | `Qt6Svg.dll` |
| Linux tar.gz | 3.12.10 · `libpython3.12.so.1.0` | 6.10.0 · `libQt6Core.so.6` | `libQt6Svg.so.6` |

El [inventario por archivo y SHA-256](evidence/portables-v2.0.0.json) sale de los miembros de PyInstaller. Incluye bibliotecas, extensiones y destinos de enlaces registrados por el empaquetador. En ambos se identificaron Qt Quick, Qt Network y Qt SVG. Las versiones de la tabla siguiente se leyeron de las cadenas que contienen los miembros, usando `CArchiveReader.extract` sobre los binarios identificados en el inventario.

El [inventario Python congelado](evidence/packaged-python-v2.0.0.json) cruza el lock de la primera estable con los módulos de `PYZ.pyz`. Ambos binarios incluyen metadatos de distribución de NumPy 2.5.0 y cryptography 50.0.2. Para los demás paquetes muestra el espacio de nombres observado y la versión fijada por el constructor. Un paquete ausente de PYZ puede ser una herramienta de compilación, una extensión que se guarda aparte o una distribución que comparte el espacio de nombres con otras, como PySide6.

| Biblioteca | Windows | Linux |
| --- | --- | --- |
| HDF5 de h5py | 2.0.0 · `hdf5.dll` | 2.0.0 · `libhdf5-9e18f0c6.so.320.0.0` |
| OpenSSL de Python | 3.0.16 · `libcrypto-3.dll` | 3.0.2 · `libcrypto.so.3` |
| Expat | 2.7.1 · `pyexpat.pyd` | 2.4.7 · `libexpat.so.1` |
| OpenBLAS en NumPy y SciPy | DLL presentes. Versión sin confirmar. | 0.3.33 y 0.3.31, respectivamente |
| libpng del sistema de compilación | Sin versión confirmada | 1.6.37 · `libpng16.so.16` |

En Linux una cadena de versión base puede mantenerse después de que el distribuidor aplique parches. Falta recuperar revisión de paquete y procedencia del componente. Los números de OpenSSL tampoco describen necesariamente el runtime incluido por otras bibliotecas, como `cryptography`.

La [consulta OSV](evidence/pypi-osv.json) reportó cero coincidencias para 30 combinaciones de paquetes y versión de los dos archivos de dependencias fijadas. El servicio recibe el ecosistema PyPI, nombre y versión a través de `/v1/querybatch`. El resultado depende de la publicación de avisos en el servicio. Qt enlazado, CPython y librerías compiladas dentro de un wheel se revisan además con los avisos de sus proveedores. [API de OSV](https://google.github.io/osv.dev/post-v1-querybatch/)

## Avisos y exposición

| Hallazgo | Ruta en SignalLab | Estado |
| --- | --- | --- |
| CVE-2026-6210 · Qt SVG | El tema personalizado autodetecta imágenes y sólo decodifica PNG, JPEG, WebP o BMP. La interfaz también renderiza iconos y diagramas SVG propios. | **Mitigado parcialmente en la versión publicada.** Qt 6.10.0 pertenece al rango afectado. El candidato fija 6.12.0, posterior a la corrección. La versión y Qt SVG se verificaron en los portables descartables de Windows y Linux del mismo SHA. [Aviso de Qt](https://www.qt.io/blog/security-advisory-type-confusion-and-heap-buffer-overflow-vulnerability-in-qt-svg-marker-handling) · [Evidencia de empaquetado](evidence/final-matrix-1aac793.json) |
| CVE-2026-79616 · Qt Quick | La biblioteca aparece en los portables 2.0.0. Las pantallas son Qt Widgets y no se encontró un flujo para cargar QML externo. | **Mitigado parcialmente en la versión publicada.** El candidato lleva un Qt posterior a la corrección y usa `PySide6_Essentials`, que contiene los módulos usados por la aplicación sin arrastrar WebEngine y PDF. [Aviso de Qt](https://www.qt.io/blog/security-advisory-cve-2026-79616) |
| CVE-2026-101201 · parseo JSON en Qt | Se encontró QtCore en ambos portables. Las sesiones se leen con `json` de Python, y no se identificó una llamada de aplicación a `QJsonDocument`. | **Ruta directa no observada.** Revisar el alcance transitivo de plugins y eventuales actualizaciones de Qt. [Aviso de Qt](https://www.qt.io/blog/security-advisory-cve-2026-101201) |
| CVE-2026-105924 · conversión CBOR a JSON en Qt | QtCore está presente en ambos entornos. No se identificó una ruta de importación CBOR en los controles de la aplicación. | **Componente afectado también en el candidato.** Qt incluye la corrección desde 6.12.1. Sigue pendiente renovar y verificar la rueda cuando esté disponible. [Aviso de Qt](https://www.qt.io/blog/security-advisory-cve-2026-105924) |
| CVE-2026-115557 · confianza TLS de CPython | El actualizador consulta GitHub mediante `urllib`. Además de HTTPS verifica el manifiesto firmado y la huella del archivo descargado. | **Mitigación parcial.** La firma de datos protege una capa posterior a TLS. El runtime anterior al parche permanece en 2.0.0. [Aviso de CPython](https://www.python.org/downloads/release/python-31216/) |
| CVE-2026-77214 / CVE-2026-102633 · Expat y CVE-2026-114583 · `tarfile` | Se identificaron componentes XML. La herramienta de inventario abre un miembro regular y copia su contenido a un destino fijo. | **Runtime del candidato actualizado.** CPython 3.14.10 y Expat 2.9.0 se verificaron en los dos instaladores. La distribución pública 2.0.0 conserva los runtimes históricos detallados arriba. [Avisos de CPython](https://www.python.org/downloads/release/python-31410/) · [Seguimiento Ubuntu](https://ubuntu.com/security/CVE-2026-77214) |
| CVE-2025-15467 y avisos posteriores · OpenSSL | El actualizador utiliza TLS. CVE-2025-15467 corresponde al procesamiento CMS. La revisión de la aplicación no encontró un flujo de importación CMS. | **Revisión de Ubuntu acreditada en el candidato.** El hash de las dos bibliotecas incluidas se vincula al paquete `3.0.2-0ubuntu1.30`. El runtime TLS de CPython y el OpenSSL de la rueda `cryptography` se verificaron por separado. [Aviso de Ubuntu](https://ubuntu.com/security/notices/USN-8847-1) |
| CVE-2026-17573 · HDF5 | La importación MATLAB 7.3 alcanza h5py y HDF5. El aviso describe una ruta en `h5repack`, herramienta que SignalLab no invoca. La importación lee datos con la API de h5py. | **Pendiente.** Revisar avisos específicos del lector y las referencias externas de HDF5. Las ruedas 3.16.0 incluidas mantienen HDF5 2.0.0. [Aviso de The HDF Group](https://www.hdfgroup.org/2026/07/30/release-of-hdf5-2-2-0-and-two-august-events-newsletter-210/) · [h5py en PyPI](https://pypi.org/project/h5py/) |

El Qt 6.12.1 ya tiene una publicación oficial de Qt. Al hacer la revisión, PyPI aún no ofrecía sus ruedas de Essentials, Addons y shiboken6. Se usó 6.12.0, con ruedas Windows x64 y Linux x86-64 glibc 2.34+, y quedan por revisar avisos posteriores al parche que afectan módulos presentes. [Qt 6.12.1](https://www.qt.io/blog/qt-6.12.1-released) · [Ruedas PySide6 Essentials](https://pypi.org/project/PySide6-Essentials/6.12.0/)

### Actualización del candidato a CPython 3.14.10

La primera línea base de Fase 01 usó 3.12.10. La serie 3.12 publica sus parches como fuentes, y el paquete 3.12.16 del canal NuGet Windows no está disponible. Se eligió 3.14.10 porque GitHub Actions ofrece compilaciones x64 para Windows y Ubuntu 22.04 y existe un paquete oficial para la preparación local de Windows. Se mantiene el lock de dependencias científicas. [Publicación de 3.12.16](https://www.python.org/downloads/release/python-31216/) · [Paquete oficial de Windows](https://www.nuget.org/packages/python/3.14.10) · [Manifiesto de GitHub Actions](https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json)

CPython 3.14.10 incluye las correcciones para CVE-2026-115557 y CVE-2026-114583. La serie actualiza también el Expat incluido a 2.9.0. El diagnóstico del portable registra las versiones cargadas de CPython, OpenSSL y Expat. La auditoría verifica además la biblioteca de CPython contenida en el ejecutable. [Publicación de 3.14.10](https://www.python.org/downloads/release/python-31410/) · [Historial de cambios de CPython](https://docs.python.org/3.14/whatsnew/changelog.html)

Se verificó la firma Authenticode válida de Python Software Foundation para el `python.exe` del paquete NuGet y se fijó el SHA-256 del paquete en `setup_windows.ps1`. La firma pertenece al runtime del proveedor. El trabajo de estabilización usa portables descartables y la publicación 2.0.0 conserva sus runtimes originales. Los avisos posteriores de Qt y los componentes nativos transitivos siguen bajo revisión.

| Portable de prueba en `ccb6a86` | CPython | Expat cargado | OpenSSL de Python cargado |
| --- | --- | --- | --- |
| Windows x64 | 3.14.10 | 2.9.0 | 3.5.9 |
| Linux x86-64 | 3.14.10 | 2.9.0 | 3.0.2 |

Ambos portables pasaron los 13 controles y la inspección del CPython empaquetado. Esa corrida registró la versión base de OpenSSL en Linux. La revisión del paquete Ubuntu se acreditó después con el candidato de cierre. [Evidencia de los ejecutables](evidence/cpython-31410-ccb6a86.json)

### Inventario nativo del cierre

En `853bd67` se registraron la ruta, SHA-256 y origen coincidente de los 219 PE de Windows y los 391 ELF de Linux, junto con los 42 enlaces simbólicos de Linux. La correspondencia de las bibliotecas OpenSSL de Ubuntu se verificó sobre el archivo empaquetado. Se identificó además OpenSSL 4.0.3 mediante el binario de `cryptography` cuyo hash coincide con el de la rueda instalada en cada sistema. [Cierre y alcance](PHASE_01_CLOSEOUT.md) · [Evidencia de la distribución](evidence/phase-01-distribution-853bd67.json)

## Recursos y cancelación

| Flujo | Control existente o agregado | Riesgo residual |
| --- | --- | --- |
| Señales y grillas | `ensure_working_set` rechaza dimensiones fuera del espacio de direcciones y estima matrices vivas contra un 35 % de RAM libre por defecto. | La estimación depende del punto de llamada. No reserva memoria frente a cálculos simultáneos ni garantiza el máximo de un decodificador nativo. |
| JSON, CSV y MATLAB | JSON de sesión y los importadores CSV/JSON estiman antes de decodificar. MAT verifica el tamaño de la variable antes de cargar sus muestras. La rama aplica una comprobación de tamaño antes de leer un script `.m`. | Las estimaciones no acotan de forma uniforme la expansión del parser y los metadatos de archivos comprimidos. La identificación de MAT precede al cálculo del tamaño de la variable. |
| Expresiones y CAS | El intérprete acota determinadas operaciones, y los trabajos cooperativos comprueban cancelación. El controlador consulta el proceso simbólico cada 100 ms y escala de terminación a cierre forzado tras hasta 2 s al cancelarlo. | No hay plazo máximo común ni tope de memoria impuesto por el sistema al worker. Usa los permisos del proceso de escritorio. El subproceso permite cancelar el cálculo y separar fallos. No constituye una sandbox de seguridad. |
| Sesiones | Se valida antes de incorporar y la escritura atómica conserva el último archivo si falla el reemplazo. | La carga de JSON y la validación dependen de la RAM y la complejidad del documento. La medición del cierre cubre escalas de los motores numéricos y la cancelación de DTFT y del subproceso simbólico. |

## Reproducción

```sh
python -B tools/inspect_packaged_runtimes.py SignalLab-PC-2.0.0.exe SignalLab-PC-2.0.0-linux-x86_64.tar.gz --output work/portables.json
python -B tools/check_engineering_package.py --output work/packaged-smoke.json
```

La primera prueba requiere las dos descargas públicas con sus hashes. La segunda construye un portable descartable, comprueba que conserva Qt SVG y ejecuta el diagnóstico interno con Qt offscreen. Su informe no sustituye las pruebas de instaladores, actualizaciones o firma de una entrega.
