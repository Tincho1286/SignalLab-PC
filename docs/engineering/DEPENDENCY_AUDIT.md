# Dependencias, licencias y referencias externas

## Línea base de la entrega 2.3.1

El lock fija NumPy 2.5.5, SciPy 1.18.1, SymPy 1.14.0, Matplotlib 3.11.2 y h5py 3.16.0. CPython empaquetado es 3.14.10. Los inventarios de la Preview confirman Qt Essentials 6.12.1 y Expat 2.9.0 en ambos sistemas. El diagnóstico de Pillow confirma que JPEG 2000 está deshabilitado en ambos empaquetados. [Lock](../../requirements-lock.txt) · [Código y procedencia](phase_05/evidence/candidate-1311df1/verified-build.json)

| Plataforma | Archivos nativos en el inventario | Verificación de OpenSSL |
| --- | ---: | --- |
| Windows x64 | 218 | El runtime CPython informa OpenSSL 3.5.9. El inventario identifica por separado el vínculo de `cryptography`. [Inventario Windows](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.1/windows-native-inventory.json) |
| Linux x86_64 | 385 | `libssl.so.3` y `libcrypto.so.3` se cotejaron con `libssl3:amd64` de Ubuntu `3.0.2-0ubuntu1.30`. El runtime base se informa aparte del vínculo de `cryptography`. [Inventario Linux](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.1/linux-native-inventory.json) |

Los adjuntos incluyen SBOM CycloneDX y comprobantes de las dos construcciones. La evidencia resuelve E-01 en el alcance de los portables indicado en su expediente. El lector MAT conserva E-02 y su política de archivos confiables, con mitigaciones y seguimiento de HDF5. La vigilancia de avisos, componentes del anfitrión y el paso de ruedas Qt fijadas a ruedas de distribución regular se evalúan por candidato y plataforma. [SBOM Windows](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.1/windows-native.cdx.json) · [SBOM Linux](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.1/linux-native.cdx.json) · [Alcance de excepciones](phase_02c/validation/EXCEPTION_APPROVAL_REGISTER.md)

La política para las fases futuras distingue dependencias directas, adaptadores, formatos, procesos y referencias. SciPy se reutiliza dentro del lock. Las referencias de RF se evalúan primero mediante fórmulas, intercambio y programas de contraste. Cualquier adopción exige comprobar licencia, mantenimiento, seguridad, compatibilidad con el CPython fijado y ambos sistemas, precisión, alternativas y coste de distribución y soporte. [Modalidades y fuentes](INTEGRATION_CATALOG.md#referencias-y-modalidades-de-integración)

## Inventario histórico de Fase 00

**Fase 00 · 24 de noviembre de 2026.** Entorno observado: Windows x64, CPython 3.12.10. Las versiones de Linux se declaran en el mismo lock con marcadores de plataforma. Para verificar una publicación hace falta el inventario del artefacto correspondiente.

## Inventario instalado y declarado

| Uso | Dependencias y versiones |
| --- | --- |
| Numérico y simbólico | NumPy 2.5.0, SciPy 1.18.0, SymPy 1.14.0, mpmath 1.3.0. |
| Interfaz y gráficos | PySide6 6.10.0, PySide6_Addons 6.10.0, PySide6_Essentials 6.10.0, shiboken6 6.10.0, Matplotlib 3.11.2. |
| Dependencias de dibujo | contourpy 1.4.0, cycler 0.12.1, fonttools 4.67.0, kiwisolver 1.5.1, Pillow 13.0.0, pyparsing 3.3.3, python-dateutil 2.9.0.post0, six 1.17.0, packaging 26.3. |
| MATLAB 7.3 | h5py 3.16.0. El entorno consultado reportó HDF5 2.0.0. |
| Actualizador y firma | cryptography 50.0.2, cffi 2.1.1, pycparser 3.12. La biblioteca criptográfica reportó OpenSSL 4.0.3 y `ssl` de CPython reportó OpenSSL 3.0.16. Son dos runtimes distintos. |
| Construcción | PyInstaller 6.22.3, pyinstaller-hooks-contrib 2026.9, altgraph 0.17.5, setuptools 84.2.1. Windows añade pefile 2024.8.26 y pywin32-ctypes 0.2.3. |
| Calidad e instalación | pyflakes 3.4.0 para el control estático, pip 25.0.1 en el entorno local. |

`python -m pip check` pasó. El manifiesto `pyproject.toml` fija siete dependencias directas. `requirements.txt` contiene cinco y omite h5py y cryptography. `requirements-lock.txt` contiene h5py pero registra cryptography y sus auxiliares en `requirements-quality.txt`. Ambos flujos de empaquetado instalan los dos archivos fijados. Un usuario que elija el archivo mínimo puede tener disponibles las funciones principales y fallar al usar MATLAB `.mat` o capacidades de actualización. El proyecto fija `>=3.12,<3.13`; evaluar cambios de Python requiere validación en ambos sistemas.

El proyecto declara `GPL-3.0-or-later`. SciPy y SymPy son BSD, NumPy reúne varios avisos permisivos, y Matplotlib incluye licencias diferenciadas para código y fuentes. La distribución abierta de PySide6 permite usar la alternativa GPLv3 que ya documenta SignalLab. PyInstaller tiene condiciones propias y una excepción para distribuir el ejecutable como parte del producto. Conservar el inventario de [avisos de terceros](../../THIRD_PARTY_NOTICES.md) y las licencias de DLL, bibliotecas nativas, fuentes y plugins que realmente se empaqueten. El manifiesto actual de licencias inventaría avisos de la instalación, y queda pendiente contrastarlo con los binarios de Windows y Linux. [Licencias oficiales de Qt](https://doc.qt.io/qt-6/licensing.html) · [Licencia de PyInstaller](https://pyinstaller.org/en/stable/license.html).

## Seguridad y reproducibilidad

| Prioridad | Estado | Hallazgo y criterio de revisión |
| --- | --- | --- |
| Alta | Versión afectada y ruta de entrada identificadas | **CVE-2026-6210.** Qt 6.10.0 está en el rango publicado de Qt SVG. `wallpaper.read_photo` autodetecta el formato con `QImageReader`. El filtro visual de nombre de archivo en el diálogo no valida el códec. Confirmar formato real admitido y módulos presentes en cada artefacto. La corrección debe permitir los formatos de imagen documentados y cubrir formatos no admitidos con archivos benignos. [Aviso oficial de Qt](https://www.qt.io/blog/security-advisory-type-confusion-and-heap-buffer-overflow-vulnerability-in-qt-svg-marker-handling). |
| Alta | Versión afectada, exposición exacta por verificar | CPython 3.12.10 es anterior a correcciones de seguridad de `tarfile` publicadas en 3.12.11. Auditar las rutas de extracción del instalador y del proceso de construcción, que tienen modelos de confianza diferentes. Revisar también `ssl` y módulos compilados al evaluar un runtime con parches. [CPython 3.12.11](https://www.python.org/downloads/release/python-31211/) · [Historial de seguridad de 3.12](https://docs.python.org/3.12/whatsnew/changelog.html). |
| Alta | Cobertura pendiente | La instalación de `pip-audit` en un directorio aislado no pudo resolver el paquete. El acceso HTTP directo del shell también fue rechazado. La revisión manual encontró los avisos anteriores y no cubre todos los paquetes, componentes nativos ni imágenes de CI. |
| Media | Comprobado en configuración | El lock fija versiones y acciones de CI por SHA. No fija hashes de las ruedas ni genera un SBOM completo. Un inventario por plataforma debe incluir Python, Qt, OpenSSL, HDF5, BLAS y componentes del sistema además de los paquetes Python. |
| Media | Hipótesis de exposición | La importación `.mat` abre el formato y enumera datasets antes de cargar los valores. Los avisos de HDF5 necesitan validación por versión y ruta API del binario incluido. Abrir formatos genuinos y corruptos en pruebas acotadas. [Avisos de HDF5](https://github.com/HDFGroup/hdf5/security/advisories). |

Procedimiento externo reproducible. Usar un entorno descartable con acceso a PyPI y generar el JSON por plataforma con los mismos paquetes que el constructor. Para binarios nativos, exportar versiones de bibliotecas durante el empaquetado, cruzarlas con los avisos de cada proveedor y conservar el resultado junto al manifiesto de procedencia.

```console
python -m pip install -r requirements-lock.txt -r requirements-quality.txt
python -m pip check
python -m pip inspect --local
python -m pip install pip-audit
python -m pip_audit --local --format json --output advisory-scan.json
```

Si la herramienta está incluida en el entorno evaluado, su propio árbol aparecerá en el resultado. Para un gate definitivo, separar el escáner y evaluar el inventario fijado del artefacto. [Documentación de pip-audit](https://github.com/pypa/pip-audit).

## Referencias y decisiones preliminares

La madurez se estima por documentación, empaquetado y evidencia de pruebas publicada por cada proyecto. La integración de estas bibliotecas y sus combinaciones con el lock de SignalLab requeriría un ensayo por versión. Ninguna dependencia nueva se aprobó en esta fase. El coste relativo incluye interoperabilidad, CI y distribución, además del código de adaptación.

| Proyecto | Capacidades, licencia y evidencia | Compatibilidad, coste y decisión |
| --- | --- | --- |
| SciPy | DSP, FFT, control numérico, integración y MAT. BSD-3-Clause. Proyecto maduro con pruebas por subpaquete y CI nativo. | Ya integrado en Windows/Linux. Mantener como **dependencia**. Usar expresiones analíticas como referencia independiente cuando el propio algoritmo llama a SciPy. [Repositorio](https://github.com/scipy/scipy). |
| SymPy | Álgebra, integración, transformadas y exactitud racional. BSD-3-Clause. Suite amplia y mpmath. | Ya integrado y multiplataforma. Mantener como **dependencia**. Evitar delegar a sus convenciones implícitas de soporte, Dirac o ROC. [Repositorio](https://github.com/sympy/sympy). |
| pyFDA | Diseño e inspección de filtros. MIT para fuentes, GPLv3 para distribuciones descritas por el proyecto. Qt, SciPy y documentación de uso. | Aplicación de escritorio madura. Integrarla duplicaría interfaz y parte de la cadena. **Referencia** de diseño, formatos Q y UX. Cobertura de pruebas por validar. [Repositorio](https://github.com/chipmuenk/pyfda). |
| python-control | LTI, realimentación, respuestas, conversión y diseño en espacio de estados. BSD-3-Clause. Implementación documentada y suite propia. | NumPy/SciPy/Matplotlib. Slycot opcional para algunas rutas MIMO aumenta coste de binarios. **Referencia** de comparación inicial. Considerar adaptador sólo si aporta una operación ausente. [Guía](https://python-control.readthedocs.io/en/latest/intro.html) · [Repositorio](https://github.com/python-control/python-control). |
| Komm | Modulaciones, canales, secuencias y codificación. GPL-3.0. Documentación, suite pytest y ejemplos comprobables. | Python ≥3.11 según el proyecto. **Adaptador opcional** candidato para comunicaciones. Coste medio por cambios de API, matriz de dependencias y convenciones de normalización. Alternativa: primitivas propias sobre NumPy/SciPy. [Repositorio](https://github.com/rwnobrega/komm). |
| scikit-dsp-comm | DSP y comunicaciones con foco educativo. BSD-2-Clause. Documentación y ejemplos de notebook. | Ecosistema NumPy/SciPy/Matplotlib. **Referencia** de resultados y pedagogía. Validar calidad de pruebas y actividad antes de extender su papel. [Repositorio](https://github.com/mwickert/scikit-dsp-comm). |
| CommPy | Modulaciones, canales y codificación. BSD-3-Clause. Fuentes de prueba y documentación disponibles, con distribución a comprobar para el entorno actual. | Dependencias NumPy/SciPy/Matplotlib. Coste medio por compatibilidad y API. **Referencia** para contraste puntual. Preferir Komm para una prueba de adaptador. [Repositorio](https://github.com/veeresht/CommPy). |
| liquid-dsp | DSP de SDR en C, sincronización, modulación, filtros y resampling. MIT. Pruebas y documentación nativas. | Requiere compilación o binarios. FFTW/libfec opcionales cambian distribución y licencias. **Referencia** de rendimiento y radio. Evaluar proceso externo o binding sólo si hay una necesidad medida. [Repositorio](https://github.com/jgaeddert/liquid-dsp). |
| GNU Radio | Flujogramas, DSP y hardware. GPL-3.0. Proyecto maduro con pruebas C++ y Python, paquetes y documentación. | Boost/C++ y módulos de plataforma. Coste alto de incluirlo. **Proceso externo** opcional con contratos de intercambio y versiones, por ejemplo SigMF. [Repositorio](https://github.com/gnuradio/gnuradio). |
| IQEngine | Visualización y procesamiento web para capturas de RF. MIT. Proyecto con código web, flujos de build y documentación. | Dependencias web/servicios. **Referencia** de interacción y formato. Para interoperar, usar SigMF u outputs verificables. Falta ejecutar su suite. [Repositorio](https://github.com/IQEngine/IQEngine). |
| SigMF | Especificación y esquemas para capturas y anotaciones. CC BY-SA 4.0 para la especificación. | Formato independiente del SO. **Adaptador** de importación/exportación y validación de esquema. Revisar por separado la licencia de la biblioteca de implementación que se elija. Costo bajo o medio según tamaño y metadatos. [Especificación](https://github.com/sigmf/SigMF) · [Licencia](https://github.com/sigmf/SigMF/blob/main/LICENSE.md). |
| SoapySDR | API SDR y descubrimiento de drivers. Boost-1.0 para el núcleo, licencias separadas en drivers. | CMake, C++ y bindings. Linux/Windows requieren drivers específicos. **Adaptador opcional** con prueba de dispositivos emulados y de hardware representativo. Costo alto de verificar combinaciones. [Repositorio](https://github.com/pothosware/SoapySDR). |
| scikit-rf | Touchstone, redes multipuerto, conversiones y calibración. BSD-3-Clause. Proyecto maduro con documentación y pruebas. | Dependencias científicas Python. **Adaptador opcional** en RF. Probar impedancias complejas, parámetros por puerto y versiones Touchstone antes de aprobar el empaquetado. [Repositorio](https://github.com/scikit-rf/scikit-rf). |
| FilterDesk | Filtros RF, componentes, BOM, SPICE, Touchstone y CLI. Apache-2.0. Publica Windows/Linux y casos dorados. | Python ≥3.12 según el proyecto y una aplicación completa. **Referencia** de validación y experiencia. Exportaciones comparables sin integrar su GUI. [Repositorio](https://github.com/fsclavo/filter-desk). |
| CMSIS-DSP | Primitivas ARM Cortex-M/A, incluidos formatos Q y filtros. Apache-2.0. Pruebas de referencia y código optimizado. | Compilación C y arquitecturas ARM. **Referencia** para vectores exportados. Confirmar compilador, saturación y orden de coeficientes. El desktop usa su propio motor de simulación. [Repositorio](https://github.com/ARM-software/CMSIS-DSP). |
| ZipCPU dspfilters | Ejemplos HDL de filtros y técnicas de hardware. LGPLv3 declarada. Señala implementaciones demostrativas. | Coste alto para adoptar RTL, herramientas FPGA y prueba de temporización. **Referencia** de arquitectura y casos. Cobertura funcional y regeneración por verificar antes de usar módulos. [Repositorio](https://github.com/ZipCPU/dspfilters). |
| Analog Devices HDL | Bloques y proyectos vinculados a convertidores y placas. Licencias por archivo y compilación bajo términos propios. | Dependencias de FPGA/licencias de herramientas y hardware. **Referencia**. La validación de un bloque concreto exige revisar la licencia elegida y el banco de simulación del proyecto correspondiente. [Repositorio](https://github.com/analogdevicesinc/hdl) · [Licencia](https://raw.githubusercontent.com/analogdevicesinc/hdl/main/LICENSE). |
| Sionna | Simulación de comunicaciones y canal, con componentes que dependen de la versión. Apache-2.0. Suites pytest y documentación científica. | La rama revisada indica PyTorch ≥2.9 para PHY/SYS y recomienda Ubuntu. Coste alto para el desktop. **Descartar como dependencia del producto** y mantener como posible comparación en un entorno de investigación separado. [Repositorio](https://github.com/NVlabs/sionna). |

Comparaciones adicionales solicitadas para etapas futuras: [Qucs-S](https://github.com/ra3xdh/qucs_s) para netlists, [PyVISA](https://github.com/pyvisa/pyvisa) para SCPI/VISA. Sus requisitos de motores o drivers merecen evaluación específica al abrir cada fase.
