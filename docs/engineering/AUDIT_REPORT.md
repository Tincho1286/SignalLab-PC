# SignalLab Engineering · Informe de auditoría

**Fase 00 · 24 de noviembre de 2026.** Repositorio `Tincho1286/SignalLab-PC`. Esta revisión documenta la base del proyecto existente y las condiciones para estabilizarlo. Los cambios del rediseño y la preparación de SignalLab PC 2.0 tienen su propia entrega.

## Diagnóstico

SignalLab PC ya dispone de motores numéricos y simbólicos, modelos reutilizables, una biblioteca de resultados con procedencia, importación y sesiones versionadas. La auditoría inventarió **30 herramientas y 84 rutas** en el rediseño local. Estas capacidades permiten construir un laboratorio extensible sobre el mismo proyecto. La cobertura numérica está distribuida de manera desigual y las rutas de interfaz, transporte y empaquetado son parte del contrato científico.

| Referencia | Evidencia |
| --- | --- |
| Commit original auditado | `16ffcbaee8356e41de6ed1e5e3410b607afe480f`, rama `codex/frontend-redesign`. Coincidía con `origin/main` al empezar la auditoría. |
| Árbol local de auditoría | 68 archivos modificados y 8 Python sin seguimiento antes de añadir documentos. Se utilizó para controles de rediseño. Su composición queda separada del commit original. |
| Canal publicado al iniciar | Consultado mediante la API de GitHub con acceso confirmado. `v1.9.6` era la estable principal y `v1.9.9` existía como preliminar. La vista web recuperada sin sesión mostraba una foto anterior, por lo que se descartó como evidencia del canal vigente. La primera consulta desde el shell restringido no tuvo acceso HTTP. |
| Discrepancia de canal | `signallab_pc.__init__` en la línea base dice `1.9.9` y `stable`, mientras la publicación es preliminar. `update_ui` usa esa variable para indicar preliminar en la app. El estado de la release y el manifiesto firmado son superficies separadas. |
| Entorno local | Windows x64, CPython 3.12.10, PySide6 6.10.0 y Matplotlib 3.11.2, con Qt en modo offscreen para la suite. |
| Rama de auditoría | `codex/engineering-audit`, separada después de la 2.0.0. Las mediciones iniciales conservan las referencias al commit y al árbol local que se inspeccionaron. |

Los historiales y la configuración de los flujos son fuentes primarias. [Publicaciones](https://github.com/Tincho1286/SignalLab-PC/releases) · [GitHub Actions](https://github.com/Tincho1286/SignalLab-PC/actions).

## Métodos de verificación y resultados

| Control | Referencia y resultado | Interpretación |
| --- | --- | --- |
| `unittest discover` completo | Árbol local de auditoría. **791 pruebas aprobadas**, sin fallos, errores ni omisiones, en 584,1 s. | Confirma los casos ejecutados en Windows offscreen. El error de importación estática quedó fuera de las rutas de error que recorrió esta suite. |
| Gate matemático | Árbol local de auditoría. **293 pruebas y 150/150 barridos** aprobados, con dos semillas. | Evidencia por familia, complementada con oráculos directos y el hallazgo de fase DFT. [Auditoría matemática](MATHEMATICAL_AUDIT.md). |
| Guardia estática | **367 archivos aprobados** en el commit original. En el árbol local, un nombre indefinido en `course_tools_panel.py:calculate`, dentro de `except`, falló en un análisis de 375 archivos. | Un dato inválido podía ocultar el error original de un diseño FIR/IIR. Durante la preparación separada de 2.0.0 se corrigió la importación y la guardia de 375 archivos pasó. Se verificó el aviso en un formulario FIR real. |
| Cobertura de líneas | **77,95 %** en la copia exacta del commit original, 32.112 líneas ejecutadas de 41.198 consideradas ejecutables en 366 módulos Python. | CPython 3.12 `sys.monitoring`, sólo proceso principal. Incluye línea de ejecución, no decisión o ramas. No instrumentó procesos simbólicos independientes ni DLL. |
| Suite bajo cobertura | 786 casos ejecutados. 785 aprobados y un error de entorno. | `test_offline_signer_binds_both_native_installer_proofs` ejecuta `git rev-parse HEAD`. Una copia hecha con `git archive` no conserva `.git`. En el árbol local con Git esa prueba pasó. Repetir en un checkout del mismo commit para una medición limpia. |
| Dependencias | `pip check` aprobado. Inventario por `pip inspect --local`. | La solución de dependencias Python es consistente en el entorno observado. El inventario nativo y el escaneo completo tienen tareas separadas. [Dependencias](DEPENDENCY_AUDIT.md). |
| CI y empaquetado | Actions usa `windows-2022` y `ubuntu-22.04`. En el historial público la ejecución matemática #120 y la construcción #132 finalizaron correctamente. Ejecuciones previas #118, #119, #130 y #131 mostraban fallos. | Éxito de una construcción y publicación son evidencias diferentes. Fijar el SHA de cada job y recopilar comprobantes de cada artefacto. [Historial de Actions](https://github.com/Tincho1286/SignalLab-PC/actions). |

La cobertura observada en algunos módulos fue `model` 78/86, `fourier` 218/288, `laplace_algebra` 281/325, `z_inverse` 182/193, `filters` 312/352, `sampling` 206/328, `state_space` 109/112, `cas_engine` 483/517 y `session` 23/27. Conviene medir ramas y procesos hijos para saber qué condiciones quedaron sin ejercicio. Se conservaron logs, el grafo DOT, la métrica por módulo y los scripts de medición en el directorio de trabajo `signallab-engineering-audit`, fuera del producto.

## Entradas y límites de confianza

`engine.evaluate_expression`, `symbolic.parse` y `cas_engine.Calculator.parse` interpretan el AST de una expresión con evaluadores específicos. El CAS construye números racionales a partir del texto y estima costos para el árbol y los exponentes. La complejidad de una integral, expansión o matriz puede superar la sugerida por el tamaño de su entrada. `symbolic_process` ejecuta el cálculo por JSON en un proceso separado y lo termina al cancelar. El proceso separado controla la vida del cálculo, pero comparte los privilegios del usuario.

Los proyectos JSON validan versión y registros y permiten recuperar el trabajo previo si la carga falla. El lector de `.m` implementa un subconjunto de asignaciones y expresiones sin ejecutar MATLAB. CSV, JSON, MATLAB y fotos de fondo requieren presupuestos y pruebas de error propios. Los aspectos de firma, archivos y versiones se registran en [DEPENDENCY_AUDIT](DEPENDENCY_AUDIT.md).

## Verificación de la entrega 2.0.0

La primera estable 2.0.0 se construyó desde `adfad5c093a236b0565f00f5e97845acf040ec96`. Los jobs nativos de Windows y Linux pasaron los controles de la construcción y del instalador. Se contrastaron los artefactos descargados y los hashes remotos y se comprobó el manifiesto firmado que sirve el canal estable. [Ejecución de distribución](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45534937561) · [Release 2.0.0](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.0.0).

## Estado de los bloqueantes

- **Alto, comprobado.** La convención de origen en la fase DFT cambia entre su herramienta independiente y la superposición con DTFT. Ambas siguen una convención válida. El flujo debe mostrar cuál usa para prevenir errores de interpretación.
- **Alto, comprobado y corregido en la preparación de 2.0.0.** El manejador de errores del rediseño podía fallar al validar un filtro. Corregirlo confirma el valor de ejecutar la guardia estática y una prueba sobre el formulario.
- **Alto, componente afectado.** Qt SVG 6.10.0 está dentro del rango de un aviso del proveedor. La preparación de 2.0.0 restringe el códec de fotos de fondo a los formatos documentados y se comprobó con imágenes benignas. Queda revisar los binarios nativos y actualizar la dependencia en condiciones verificadas. [Aviso de Qt](https://www.qt.io/blog/security-advisory-type-confusion-and-heap-buffer-overflow-vulnerability-in-qt-svg-marker-handling).
- **Alto, alcance por cerrar.** CPython 3.12.10 precede correcciones de seguridad. El análisis manual no cubre todos los componentes empaquetados. Preparar una línea base Windows/Linux con inventario nativo y referencias de cada versión. [Cambios de seguridad de CPython](https://www.python.org/downloads/release/python-31211/).
- **Alto, medido.** La concentración de dependencias diferidas hace riesgosa una reorganización global. Mantener compatibilidad de sesiones y extraer contratos un flujo a la vez.

## Reproducción

Ejecutar desde un checkout real en Windows o Linux y guardar el SHA, los indicadores de cambios locales y las versiones de dependencias. En el entorno de prueba Qt necesita las bibliotecas de sistema correspondientes. La CI enumera las instaladas en Linux.

```console
git rev-parse HEAD
git status --short
python -m pip install -r requirements-lock.txt -r requirements-quality.txt
python -B -X utf8 tools/check_static.py
python -B -X utf8 tools/check_math.py
python -B -X utf8 tools/check_workflows.py
python -B -X utf8 -m unittest discover -s tests -v
```

Configurar `QT_QPA_PLATFORM=offscreen` y `OPENBLAS_NUM_THREADS=1` para CI y aislar las preferencias y datos de la aplicación. Para medir cobertura completa en un entorno con acceso al índice, instalar `coverage` en el entorno descartable, ejecutar `python -m coverage run --branch --source=signallab_pc -m unittest discover -s tests` y exportar `python -m coverage json`. Añadir configuración para subprocesos si se necesita cubrir el proceso simbólico en esa misma medición. Para ejecutar la misma comprobación de empaquetado, despachar `.github/workflows/portable.yml` sobre una revisión aprobada y verificar hashes de los resultados y manifiestos. El escaneo de dependencias y la comprobación de binarios nativos se reproducen siguiendo [DEPENDENCY_AUDIT](DEPENDENCY_AUDIT.md).

## Recomendación

**El proyecto está preparado para iniciar Fase 01 cuando se autorice.** Esa fase debe cerrar las diferencias de fase y procedencia, completar el inventario de seguridad, fijar una línea base multiplataforma y asegurar que las sesiones antiguas se puedan abrir. La evidencia observada justifica estabilizar la base. La ampliación de capacidades queda condicionada a los criterios de salida de estabilización.

- [Arquitectura real e inventario funcional](ARCHITECTURE_AS_IS.md)
- [Auditoría matemática](MATHEMATICAL_AUDIT.md)
- [Dependencias y referencias externas](DEPENDENCY_AUDIT.md)
- [Registro de riesgos](RISK_REGISTER.md)
- [Deuda técnica](TECHNICAL_DEBT.md)
- [Arquitectura objetivo y hoja de ruta](ROADMAP.md)
- [Backlog y criterios de aceptación](BACKLOG.md)
