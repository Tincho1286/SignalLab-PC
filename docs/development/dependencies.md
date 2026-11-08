# Dependencias

[← Desarrollo](README.md)

El entorno de desarrollo y construcción utiliza Python 3.12 de 64 bits. Las versiones directas se declaran en `pyproject.toml`; `requirements-lock.txt` fija las dependencias del entorno de distribución y `requirements-quality.txt` las herramientas de comprobación. Los instaladores y portables incluyen su propio entorno de ejecución.

| Componente | Función en el proyecto |
| --- | --- |
| PySide6 | Interfaz de escritorio, documentos y recursos SVG. |
| NumPy | Muestras complejas, arreglos y operaciones numéricas. |
| SciPy | Procesamiento de señales, diseño de filtros y análisis de sistemas. |
| SymPy | Álgebra, cálculo simbólico y expresiones exactas. |
| Matplotlib | Figuras científicas interactivas. |
| h5py | Lectura de datos HDF5 utilizados por formatos MATLAB compatibles. |
| cryptography | Verificación y creación de firmas Ed25519 del manifiesto de actualización. |
| PyInstaller | Empaquetado nativo de la aplicación en Windows y Linux. |
| Inno Setup | Construcción del instalador Windows por usuario. |

La aplicación se publica bajo [GPL-3.0-or-later](../../LICENSE). Cada dependencia conserva su licencia y sus avisos: se registran en [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) y `LICENSES/`, y el paquete Linux incluye además los avisos recogidos de su entorno de construcción.

Los archivos de procedencia identifican el código y el entorno utilizados para generar cada distribución. Al cambiar una dependencia, deben revisarse sus efectos sobre cálculo, formatos, compatibilidad y licencias, además de actualizar los archivos de versiones fijadas. [Compilar y publicar](releases.md).
