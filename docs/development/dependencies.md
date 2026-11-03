# Dependencias

[← Desarrollo](README.md)

El entorno se dirige a Python 3.12 de 64 bits. `pyproject.toml`, `requirements.txt` y `requirements-lock.txt` registran las dependencias del proyecto y del entorno de distribución.

| Componente | Función |
| --- | --- |
| PySide6 | Interfaz de escritorio, recursos SVG y documentos. |
| NumPy | Muestras complejas, arreglos y operaciones numéricas. |
| SciPy | Procesamiento de señales, diseño de filtros y sistemas. |
| SymPy | Álgebra, cálculo simbólico y expresiones exactas. |
| Matplotlib | Figuras científicas interactivas. |
| h5py | Lectura de datos HDF5 utilizados por formatos MATLAB compatibles. |
| PyInstaller | Empaquetado del portable Windows. |

La aplicación se publica bajo [GPL-3.0-or-later](../../LICENSE). Las dependencias mantienen sus propias licencias; sus avisos están en [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) y `LICENSES/`.

Para conocer las versiones fijadas, consultá [pyproject.toml](../../pyproject.toml) y [requirements-lock.txt](../../requirements-lock.txt). Los cambios de dependencias se documentan junto con sus efectos en cálculo, formatos y distribución.
