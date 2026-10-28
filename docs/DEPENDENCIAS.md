# Dependencias y distribución

Evaluación en 21/10/2026 contra documentación oficial. La selección es adecuada para la arquitectura descrita, pero la licencia de cada componente en un instalador final requiere revisar los artefactos efectivamente empaquetados y sus dependencias transitivas.

| Paquete | Uso previsto | Documentación/estado de licencia consultados |
|---|---|---|
| PySide6 | UI nativa Widgets para escritorio | Es el binding oficial de Qt para Python; la edición comunitaria se ofrece bajo LGPLv3/GPLv3 y también existe edición comercial. La distribución final debe escoger y cumplir una vía. [Docs y licencias Qt for Python](https://doc.qt.io/qtforpython-6/) · [Licencia comercial](https://doc.qt.io/qtforpython-6.11/commercial/index.html) |
| NumPy | arreglos complejos, ejes y FFT | La documentación oficial publica términos BSD de tres cláusulas para redistribución. [Licencia NumPy](https://numpy.org/doc/stable/license.html) |
| SciPy | señales, diseño/filtros, convolución, espectro | `scipy.signal` incluye convolución, correlación, periodograma, Welch y diseño FIR/IIR; la guía consultada es SciPy 1.18. SciPy declara BSD modificada de 3 cláusulas; los avisos incluidos en wheels/binarios siguen necesitando inventario para el instalador. [Guía de procesamiento de señales](https://docs.scipy.org/doc/scipy/tutorial/signal.html) · [Referencia](https://docs.scipy.org/doc/scipy/reference/signal.html) · [Licencia](https://docs.scipy.org/doc/scipy-1.16.0/dev/core-dev/index.html#licensing) |
| SymPy | fórmulas exactas/simbólicas, sujeto a validación | El proyecto declara BSD en su documentación. CAS de Python no se asume idéntico al CAS HP. [Política de licencia SymPy](https://docs.sympy.org/dev/citing.html) |
| Matplotlib | trazados con toolbar de pan/zoom independiente | La documentación oficial describe la licencia basada en PSF y compatible con BSD. [Licencia Matplotlib](https://matplotlib.org/stable/project/license.html) |

## Instalación fijada para desarrollo

`requirements.txt` y `pyproject.toml` fijan NumPy 2.5.0, SciPy 1.18.0, SymPy 1.14.0, Matplotlib 3.11.2 y PySide6 6.10.0; se dirigen a Python 3.12 de 64 bits. NumPy 2.5 declara compatibilidad con Python 3.12–3.14; Matplotlib 3.11 requiere Python 3.11 o posterior. El entorno local .venv usa Python 3.12.10 oficial de NuGet y las dependencias instaladas se registran en requirements-lock.txt. La compatibilidad del conjunto fijado en Windows debe verificarse mediante una instalación limpia antes de declarar reproducible la ejecución.

## Distribución

Se genera un EXE de desarrollo mediante PyInstaller 6.22.3. No es todavía la entrega de paridad completa. El empaquetado restringe PATH al entorno local y Windows para evitar incorporar DLL ajenas (se detectó ICU de Poppler incompatible con Qt). Antes de distribuir: auditar avisos/licencias/SBOM y rueda de Qt, resolver si se distribuirá bajo LGPL o licencia comercial, documentar requisitos de relink y componentes Qt incluidos, probar PyInstaller/Nuitka en Windows limpio, verificar inicio, recursos, importación/exportación y desinstalación. No tratar las licencias permisivas del resto como conclusión legal para el conjunto.
