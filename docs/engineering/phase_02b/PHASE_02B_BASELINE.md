# Línea base de Fase 02B

**25 de noviembre de 2026.** Árbol limpio en `ff3e762611f356bdea4f48c582ae3bea6b9a6557`. La diferencia respecto del candidato `ce6846bc3e6bc3d56e80bda06eda6edd1e4e2557` contiene ocho archivos de documentación y evidencia. Los dos SHA comparten código, pruebas y configuración. En GitHub sólo figuran `main` en `acb9e38` y `develop` en `ff3e762`. Las referencias históricas que sólo existen en el equipo se preservaron.

| Control | Resultado |
| --- | --- |
| Matriz del candidato DFT | Se confirmó su conclusión exitosa en GitHub. Registró 829 pruebas integrales y 150 casos preventivos por plataforma. Los portables descartables e instaladores pasaron sus diagnósticos. |
| Reproducción local Windows | `pip check` aprobado y seis pruebas del piloto DFT aprobadas mediante `python -B -X utf8 -m unittest discover -s tests -p test_math_dft_pilot.py`. |
| Runtime local | CPython 3.14.10, Qt Essentials y shiboken6 6.12.0, OpenSSL 3.5.9, NumPy 2.5.0, SciPy 1.18.0 y h5py 3.16.0. Los índices de PyPI de ambas ruedas 6.12.1 devolvieron 404 al consultar. |
| Frontera headless | Importar `dft_application`, `jobs`, `session`, `filters` y `state_space` dejó el proceso sin módulos de PySide ni shiboken cargados. |
| Reloj y persistencia | `Signal` conserva coordenadas y reloj. `Transfer` contiene coeficientes, período y ROC. `StateModel` contiene matrices y período. `Project` guarda instantáneas con padres y `session` usa reemplazo atómico. `jobs` usa un contexto local al hilo. |

Qt entra desde `ui`, `toolbox` y los paneles. Las operaciones científicas se pueden consumir por separado. La DFT ya lleva plazo y presupuesto cooperativos. El formato JSON y su costo observado, los DPI reales, el actualizador por canal público, Qt y las cuotas simbólicas conservan el seguimiento anterior. [Corrida del piloto](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45628542049) · [Evidencia del piloto](../evidence/dft-pilot-ci-ce6846b.json) · [Registro de riesgos](../RISK_REGISTER.md)
