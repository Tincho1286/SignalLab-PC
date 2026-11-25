# Línea base de seguridad

Revisión del 25 de noviembre de 2026. La distribución pública evaluada es la 2.0.0, producida desde `adfad5c093a236b0565f00f5e97845acf040ec96`. La rama de estabilización tiene un entorno distinto.

## Inventario de la distribución pública

| Portable x86-64 | CPython | QtCore | Qt SVG |
| --- | --- | --- | --- |
| Windows EXE | 3.12.10 · `python312.dll` | 6.10.0 · `Qt6Core.dll` | `Qt6Svg.dll` |
| Linux tar.gz | 3.12.10 · `libpython3.12.so.1.0` | 6.10.0 · `libQt6Core.so.6` | `libQt6Svg.so.6` |

El [inventario por archivo y SHA-256](evidence/portables-v2.0.0.json) sale de los miembros de PyInstaller. Incluye bibliotecas, extensiones y destinos de enlaces registrados por el empaquetador. En ambos se identificaron HDF5, OpenBLAS, OpenSSL, Qt Quick, Qt Network y Qt SVG. En Linux también se identificó `libexpat.so.1`. Windows incorpora `pyexpat.pyd`. Los nombres de miembros identifican presencia. El inventario asigna versiones sólo a CPython y QtCore mediante cadenas encontradas dentro de sus binarios. Queda pendiente asociar las demás bibliotecas con sus versiones, dependencias del sistema y avisos específicos.

La [consulta OSV](evidence/pypi-osv.json) reportó cero coincidencias para 30 combinaciones de paquetes y versión de los dos archivos de dependencias fijadas. El servicio recibe el ecosistema PyPI, nombre y versión a través de `/v1/querybatch`. El resultado depende de la publicación de avisos en el servicio. Qt enlazado, CPython y librerías compiladas dentro de un wheel se revisan además con los avisos de sus proveedores. [API de OSV](https://google.github.io/osv.dev/post-v1-querybatch/)

## Avisos y exposición

| Hallazgo | Ruta en SignalLab | Estado |
| --- | --- | --- |
| CVE-2026-6210 · Qt SVG | El tema personalizado autodetecta imágenes y sólo decodifica PNG, JPEG, WebP o BMP. La interfaz también renderiza iconos y diagramas SVG propios. | **Mitigado parcialmente en la versión publicada.** Qt 6.10.0 pertenece al rango afectado. El candidato fija 6.12.0, posterior a la corrección. Su empaquetado debe comprobarse por plataforma. [Aviso de Qt](https://www.qt.io/blog/security-advisory-type-confusion-and-heap-buffer-overflow-vulnerability-in-qt-svg-marker-handling) |
| CVE-2026-79616 · Qt Quick | La biblioteca aparece en los portables 2.0.0. Las pantallas son Qt Widgets y no se encontró un flujo para cargar QML externo. | **Mitigado parcialmente en la versión publicada.** El candidato lleva un Qt posterior a la corrección y usa `PySide6_Essentials`, que contiene los módulos usados por la aplicación sin arrastrar WebEngine y PDF. [Aviso de Qt](https://www.qt.io/blog/security-advisory-cve-2026-79616) |
| CVE-2026-101201 · parseo JSON en Qt | Se encontró QtCore en ambos portables. Las sesiones se leen con `json` de Python, y no se identificó una llamada de aplicación a `QJsonDocument`. | **Ruta directa no observada.** Revisar el alcance transitivo de plugins y eventuales actualizaciones de Qt. [Aviso de Qt](https://www.qt.io/blog/security-advisory-cve-2026-101201) |
| CVE-2026-115557 · confianza TLS de CPython | El actualizador consulta GitHub mediante `urllib`. Además de HTTPS verifica el manifiesto firmado y la huella del archivo descargado. | **Mitigación parcial.** La firma de datos protege una capa posterior a TLS. El runtime anterior al parche permanece en 2.0.0. [Aviso de CPython](https://www.python.org/downloads/release/python-31216/) |
| CVE-2026-77214 / CVE-2026-102633 · Expat y CVE-2026-114583 · `tarfile` | Se identificaron componentes XML. No se encontró una importación general de XML o tar como entrada de cálculo. La herramienta de inventario abre sólo un miembro regular y copia su contenido a un destino fijo. | **Pendiente.** Identificar la versión exacta de Expat en cada binario y probar el runtime parcheado. [Avisos de CPython](https://www.python.org/downloads/release/python-31216/) |

El Qt 6.12.1 ya tiene una publicación oficial de Qt. Al hacer la revisión, PyPI aún no ofrecía sus ruedas de Essentials, Addons y shiboken6. Se usó 6.12.0, con ruedas Windows x64 y Linux x86-64 glibc 2.34+, y quedan por revisar avisos posteriores al parche que afectan módulos presentes. [Qt 6.12.1](https://www.qt.io/blog/qt-6.12.1-released) · [Ruedas PySide6 Essentials](https://pypi.org/project/PySide6-Essentials/6.12.0/)

**CPython pendiente.** `setup-python` lista 3.12.16 para Ubuntu 22.04 x64. La edición 3.12.16 de CPython sólo publica fuentes y no estuvo disponible en el canal NuGet Windows que usa SignalLab. La línea base comparativa fija 3.12.10 para ambos sistemas. Antes de una entrega nueva hay que validar Linux 3.12.16 y elegir para Windows entre construir y verificar CPython desde fuentes o migrar a una serie compatible con binarios corregidos. [Manifiesto de GitHub Actions](https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json) · [Publicación de CPython](https://www.python.org/downloads/release/python-31216/)

## Recursos y cancelación

| Flujo | Control existente o agregado | Riesgo residual |
| --- | --- | --- |
| Señales y grillas | `ensure_working_set` rechaza dimensiones fuera del espacio de direcciones y estima matrices vivas contra un 35 % de RAM libre por defecto. | La estimación depende del punto de llamada. No reserva memoria frente a cálculos simultáneos ni garantiza el máximo de un decodificador nativo. |
| JSON, CSV y MATLAB | JSON de sesión y los importadores CSV/JSON estiman antes de decodificar. MAT verifica el tamaño de la variable antes de cargar sus muestras. La rama aplica una comprobación de tamaño antes de leer un script `.m`. | Las estimaciones no acotan de forma uniforme la expansión del parser y los metadatos de archivos comprimidos. La identificación de MAT precede al cálculo del tamaño de la variable. |
| Expresiones y CAS | El intérprete acota determinadas operaciones, y los trabajos cooperativos comprueban cancelación. El controlador consulta el proceso simbólico cada 100 ms y escala de terminación a cierre forzado tras hasta 2 s al cancelarlo. | No hay plazo máximo común ni tope de memoria impuesto por el sistema al worker. Usa los permisos del proceso de escritorio. El subproceso permite cancelar el cálculo y separar fallos. No constituye una sandbox de seguridad. |
| Sesiones | Se valida antes de incorporar y la escritura atómica conserva el último archivo si falla el reemplazo. | La carga de JSON y la validación dependen de la RAM y la complejidad del documento. Falta medir límites con casos benignos escalables. |

## Reproducción

```sh
python -B tools/inspect_packaged_runtimes.py SignalLab-PC-2.0.0.exe SignalLab-PC-2.0.0-linux-x86_64.tar.gz --output work/portables.json
python -B tools/check_engineering_package.py --output work/packaged-smoke.json
```

La primera prueba requiere las dos descargas públicas con sus hashes. La segunda construye un portable descartable, comprueba que conserva Qt SVG y ejecuta el diagnóstico interno con Qt offscreen. Su informe no sustituye las pruebas de instaladores, actualizaciones o firma de una entrega.
